"""
Crawler web local con politeness por host, robots.txt y checkpoint.

Disenado para alimentar corpus clinico sin servicios de pago y con
trazabilidad operacional.
"""
from __future__ import annotations

import hashlib
import json
import re
import socket
import threading
import time
from collections import deque
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from dataclasses import asdict, dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser


def canonicalize_url(raw_url: str) -> str:
    """Normaliza URL para deduplicacion."""
    text = str(raw_url or "").strip()
    if not text:
        return ""
    parsed = urlparse(text)
    scheme = (parsed.scheme or "https").lower()
    if scheme not in {"http", "https"}:
        return ""
    host = parsed.netloc.lower()
    if not host:
        return ""
    path = parsed.path or "/"
    if path != "/":
        path = path.rstrip("/")
    filtered_params = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if not key.lower().startswith("utm_")
        and key.lower() not in {"gclid", "fbclid", "mc_cid", "mc_eid"}
    ]
    query = urlencode(filtered_params, doseq=True)
    return urlunparse((scheme, host, path, "", query, ""))


def _url_host(url: str) -> str:
    return (urlparse(url).hostname or "").strip().lower()


def _normalize_text(text: str) -> str:
    normalized = re.sub(r"\s+", " ", str(text or "")).strip().lower()
    return normalized


def _build_word_shingles(text: str, *, size: int) -> set[str]:
    tokens = re.findall(r"[a-z0-9]{3,}", _normalize_text(text))
    if not tokens:
        return set()
    if len(tokens) < size:
        return {" ".join(tokens)}
    return {" ".join(tokens[idx : idx + size]) for idx in range(0, len(tokens) - size + 1)}


def _minhash_signature(shingles: set[str], seeds: tuple[int, ...]) -> tuple[int, ...]:
    if not shingles:
        return ()
    signature: list[int] = []
    for seed in seeds:
        min_hash = min(
            int.from_bytes(
                hashlib.sha1(f"{seed}:{shingle}".encode("utf-8", errors="ignore")).digest()[:8],
                byteorder="big",
                signed=False,
            )
            for shingle in shingles
        )
        signature.append(min_hash)
    return tuple(signature)


def _signature_similarity(left: tuple[int, ...], right: tuple[int, ...]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    matches = sum(1 for l_value, r_value in zip(left, right) if l_value == r_value)
    return matches / len(left)


class _HTMLContentParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self._title_open = False
        self._title_parts: list[str] = []
        self._text_parts: list[str] = []
        self._links: list[tuple[str, str]] = []
        self._current_link: str | None = None
        self._current_link_text_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lowered = tag.lower()
        if lowered in {"script", "style", "noscript"}:
            self._skip_depth += 1
        if lowered == "title":
            self._title_open = True
        if lowered == "a":
            for key, value in attrs:
                if key.lower() == "href" and value:
                    self._current_link = value.strip()
                    self._current_link_text_parts = []
                    break

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        if lowered in {"script", "style", "noscript"} and self._skip_depth > 0:
            self._skip_depth -= 1
        if lowered == "title":
            self._title_open = False
        if lowered == "a":
            if self._current_link:
                anchor_text = " ".join(self._current_link_text_parts).strip()
                self._links.append((self._current_link, anchor_text))
            self._current_link = None
            self._current_link_text_parts = []

    def handle_data(self, data: str) -> None:
        if self._skip_depth > 0:
            return
        cleaned = re.sub(r"\s+", " ", data or "").strip()
        if not cleaned:
            return
        if self._title_open:
            self._title_parts.append(cleaned)
        else:
            self._text_parts.append(cleaned)
        if self._current_link:
            self._current_link_text_parts.append(cleaned)

    @property
    def title(self) -> str:
        text = " ".join(self._title_parts).strip()
        return text[:180]

    @property
    def text(self) -> str:
        return " ".join(self._text_parts).strip()

    @property
    def links(self) -> list[str]:
        return list(dict.fromkeys(href for href, _ in self._links))

    @property
    def linked_anchors(self) -> list[tuple[str, str]]:
        return list(self._links)


@dataclass(slots=True)
class CrawlRequest:
    url: str
    depth: int
    priority: int
    discovered_from: str | None = None


@dataclass(slots=True)
class CrawlPage:
    url: str
    host: str
    depth: int
    title: str
    text: str
    status_code: int
    content_type: str
    fetched_at: float
    fetch_latency_ms: float
    dns_ip: str | None
    links: list[str] = field(default_factory=list)
    link_anchors: dict[str, str] = field(default_factory=dict)
    discovered_from: str | None = None
    source_file: str | None = None


@dataclass(slots=True)
class CrawlRunSummary:
    pages_fetched: int
    pages_saved: int
    pages_skipped_robots: int
    pages_skipped_non_html: int
    pages_skipped_near_duplicate: int
    urls_discovered: int
    frontier_pending: int
    errors: int
    checkpoint_path: str
    output_dir: str
    elapsed_seconds: float


@dataclass(slots=True)
class WebCrawlerConfig:
    seeds: list[str]
    output_dir: str = "docs/web_raw"
    checkpoint_path: str = "tmp/web_crawl_checkpoint.json"
    resume_from_checkpoint: bool = True
    allowed_domains: list[str] = field(default_factory=list)
    max_pages: int = 120
    max_depth: int = 2
    workers: int = 6
    front_queues: int = 4
    request_timeout_seconds: int = 8
    user_agent: str = "clinical-crawler/1.0 (+internal)"
    politeness_multiplier: float = 10.0
    min_host_delay_seconds: float = 0.5
    robots_cache_ttl_seconds: int = 3600
    checkpoint_every_pages: int = 10
    max_content_bytes: int = 1_500_000
    min_text_chars: int = 240
    near_duplicate_threshold: float = 0.90
    shingle_size: int = 3
    max_urls_per_host: int = 80
    max_pages_per_host: int = 40
    enable_robots: bool = True
    minhash_seeds: tuple[int, ...] = tuple(range(24))


@dataclass(slots=True)
class _FetchResult:
    request: CrawlRequest
    page: CrawlPage | None = None
    skip_reason: str | None = None
    error: str | None = None


@dataclass(slots=True)
class _RobotsCacheItem:
    parser: RobotFileParser
    fetched_at: float


class WebCrawlerService:
    """Crawler web con frontier priorizada y cortesia por host."""

    _DOMAIN_AUTHORITY_HINTS = {
        "who.int": 1.00,
        "cdc.gov": 0.98,
        "nih.gov": 0.98,
        "pubmed.ncbi.nlm.nih.gov": 0.99,
        "nejm.org": 0.95,
        "thelancet.com": 0.94,
        "bmj.com": 0.93,
        "jamanetwork.com": 0.93,
        "scielo.org": 0.90,
    }

    def __init__(self, config: WebCrawlerConfig) -> None:
        if config.max_pages <= 0:
            raise ValueError("max_pages debe ser > 0.")
        if config.workers <= 0:
            raise ValueError("workers debe ser > 0.")
        self.config = config
        self.output_dir = Path(config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_path = Path(config.checkpoint_path)
        self.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.output_dir / "crawl_manifest.jsonl"

        self._allowed_domains = [
            domain.strip().lower() for domain in config.allowed_domains if domain
        ]
        self._front_queues: list[deque[CrawlRequest]] = [
            deque() for _ in range(max(1, config.front_queues))
        ]
        self._pending_by_host: dict[str, deque[CrawlRequest]] = {}
        self._active_hosts: set[str] = set()
        self._host_next_allowed_at: dict[str, float] = {}
        self._host_enqueued_count: dict[str, int] = {}
        self._host_saved_count: dict[str, int] = {}
        self._queued_or_seen_urls: set[str] = set()
        self._content_signatures: list[tuple[int, ...]] = []
        self._dns_cache: dict[str, str] = {}
        self._dns_failures: set[str] = set()
        self._robots_cache: dict[str, _RobotsCacheItem] = {}
        self._network_lock = threading.Lock()
        self._manifest_lock = threading.Lock()
        self._stats = {
            "pages_fetched": 0,
            "pages_saved": 0,
            "pages_skipped_robots": 0,
            "pages_skipped_non_html": 0,
            "pages_skipped_near_duplicate": 0,
            "urls_discovered": 0,
            "errors": 0,
        }

    @staticmethod
    def _request_to_json(item: CrawlRequest) -> dict[str, Any]:
        return asdict(item)

    @staticmethod
    def _request_from_json(payload: dict[str, Any]) -> CrawlRequest:
        return CrawlRequest(
            url=str(payload.get("url") or ""),
            depth=int(payload.get("depth") or 0),
            priority=int(payload.get("priority") or 0),
            discovered_from=str(payload.get("discovered_from") or "") or None,
        )

    def _domain_allowed(self, host: str) -> bool:
        if not host:
            return False
        if not self._allowed_domains:
            return True
        for allowed in self._allowed_domains:
            if host == allowed or host.endswith(f".{allowed}"):
                return True
        return False

    def _domain_authority_score(self, host: str) -> float:
        normalized = host.lower()
        score = 0.55
        for domain, value in self._DOMAIN_AUTHORITY_HINTS.items():
            if normalized == domain or normalized.endswith(f".{domain}"):
                score = max(score, value)
        if normalized.endswith(".gov"):
            score = max(score, 0.92)
        elif normalized.endswith(".edu"):
            score = max(score, 0.88)
        return min(max(score, 0.0), 1.0)

    def _compute_priority(self, *, url: str, depth: int) -> int:
        host = _url_host(url)
        authority = self._domain_authority_score(host)
        depth_penalty = min(max(depth, 0), 10) * 8
        score = int((authority * 100) - depth_penalty)
        return max(1, min(score, 100))

    def _front_index_for_priority(self, priority: int) -> int:
        count = len(self._front_queues)
        scaled = int((100 - max(1, min(priority, 100))) * count / 101)
        return max(0, min(scaled, count - 1))

    def _enqueue(self, request: CrawlRequest) -> bool:
        url = canonicalize_url(request.url)
        if not url:
            return False
        request.url = url
        if request.depth > self.config.max_depth:
            return False
        host = _url_host(url)
        if not self._domain_allowed(host):
            return False
        if host and self._host_enqueued_count.get(host, 0) >= self.config.max_urls_per_host:
            return False
        if url in self._queued_or_seen_urls:
            return False
        self._queued_or_seen_urls.add(url)
        if host:
            self._host_enqueued_count[host] = self._host_enqueued_count.get(host, 0) + 1
        request.priority = request.priority or self._compute_priority(url=url, depth=request.depth)
        index = self._front_index_for_priority(request.priority)
        self._front_queues[index].append(request)
        self._stats["urls_discovered"] += 1
        return True

    def _promote_front_to_back(self) -> None:
        for queue in self._front_queues:
            if not queue:
                continue
            request = queue.popleft()
            host = _url_host(request.url)
            if not host:
                continue
            if host not in self._pending_by_host:
                self._pending_by_host[host] = deque()
            self._pending_by_host[host].append(request)
            break

    def _frontier_pending_count(self) -> int:
        return sum(len(queue) for queue in self._front_queues) + sum(
            len(queue) for queue in self._pending_by_host.values()
        )

    def _has_frontier_work(self) -> bool:
        if any(queue for queue in self._front_queues):
            return True
        return any(queue for queue in self._pending_by_host.values())

    def _next_schedulable_request(self) -> tuple[str | None, CrawlRequest | None, float]:
        if self._has_frontier_work():
            self._promote_front_to_back()
        now = time.monotonic()
        chosen_host: str | None = None
        chosen_request: CrawlRequest | None = None
        chosen_priority = -1
        min_wait = 0.2
        for host, queue in list(self._pending_by_host.items()):
            if not queue:
                continue
            if host in self._active_hosts:
                continue
            ready_at = self._host_next_allowed_at.get(host, 0.0)
            if ready_at > now:
                min_wait = min(min_wait, max(0.01, ready_at - now))
                continue
            candidate = queue[0]
            if candidate.priority > chosen_priority:
                chosen_priority = candidate.priority
                chosen_host = host
                chosen_request = candidate
        if chosen_host and chosen_request:
            self._pending_by_host[chosen_host].popleft()
            if not self._pending_by_host[chosen_host]:
                self._pending_by_host.pop(chosen_host, None)
            return chosen_host, chosen_request, 0.0
        return None, None, min_wait

    def _resolve_dns_ip(self, host: str) -> str | None:
        if not host:
            return None
        with self._network_lock:
            if host in self._dns_cache:
                return self._dns_cache[host]
            if host in self._dns_failures:
                return None
        try:
            ip_address = socket.gethostbyname(host)
        except OSError:
            with self._network_lock:
                self._dns_failures.add(host)
            return None
        with self._network_lock:
            self._dns_cache[host] = ip_address
        return ip_address

    def _load_robots_parser(self, host: str) -> RobotFileParser | None:
        if not host:
            return None
        now = time.time()
        with self._network_lock:
            cached = self._robots_cache.get(host)
            if cached and (now - cached.fetched_at) < self.config.robots_cache_ttl_seconds:
                return cached.parser
        raw_text = ""
        for scheme in ("https", "http"):
            robots_url = f"{scheme}://{host}/robots.txt"
            request = Request(robots_url, headers={"User-Agent": self.config.user_agent})
            try:
                with urlopen(request, timeout=self.config.request_timeout_seconds) as response:
                    raw_text = response.read().decode("utf-8", errors="ignore")
                break
            except (HTTPError, URLError, TimeoutError):
                continue
        parser = RobotFileParser()
        parser.parse(raw_text.splitlines())
        with self._network_lock:
            self._robots_cache[host] = _RobotsCacheItem(parser=parser, fetched_at=now)
        return parser

    def _is_url_allowed_by_robots(self, url: str) -> bool:
        if not self.config.enable_robots:
            return True
        host = _url_host(url)
        if not host:
            return False
        parser = self._load_robots_parser(host)
        if parser is None:
            return True
        try:
            return parser.can_fetch(self.config.user_agent, url)
        except Exception:
            return True

    def _extract_html_payload(
        self,
        *,
        base_url: str,
        html: str,
    ) -> tuple[str, str, list[str], dict[str, str]]:
        parser = _HTMLContentParser()
        parser.feed(html)
        title = parser.title
        text = parser.text
        links: list[str] = []
        link_anchors: dict[str, str] = {}
        for href, anchor_text in parser.linked_anchors:
            absolute = canonicalize_url(urljoin(base_url, href))
            if not absolute:
                continue
            host = _url_host(absolute)
            if not self._domain_allowed(host):
                continue
            links.append(absolute)
            existing_anchor = link_anchors.get(absolute, "")
            current_anchor = re.sub(r"\s+", " ", anchor_text or "").strip()
            if current_anchor and len(current_anchor) >= len(existing_anchor):
                link_anchors[absolute] = current_anchor
        unique_links = list(dict.fromkeys(links))
        normalized_anchor_map = {url: link_anchors.get(url, "") for url in unique_links}
        return title, text, unique_links, normalized_anchor_map

    def _is_near_duplicate_content(self, text: str) -> bool:
        shingles = _build_word_shingles(text, size=max(2, self.config.shingle_size))
        if not shingles:
            return False
        signature = _minhash_signature(shingles, self.config.minhash_seeds)
        for previous_signature in self._content_signatures:
            similarity = _signature_similarity(signature, previous_signature)
            if similarity >= self.config.near_duplicate_threshold:
                return True
        self._content_signatures.append(signature)
        return False

    def _persist_page(self, page: CrawlPage) -> CrawlPage:
        host_safe = re.sub(r"[^a-z0-9.-]", "_", page.host.lower())
        digest = hashlib.sha1(page.url.encode("utf-8", errors="ignore")).hexdigest()[:14]
        host_dir = self.output_dir / host_safe
        host_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{digest}.md"
        destination = host_dir / filename
        body = (
            f"# {page.title or 'Web source'}\n\n"
            f"- source_url: {page.url}\n"
            f"- host: {page.host}\n"
            f"- fetched_at_epoch: {page.fetched_at:.3f}\n"
            f"- depth: {page.depth}\n\n"
            f"{page.text}\n"
        )
        destination.write_text(body, encoding="utf-8")
        page.source_file = str(destination)
        record = {
            "url": page.url,
            "source_file": page.source_file,
            "host": page.host,
            "depth": page.depth,
            "discovered_from": page.discovered_from,
            "title": page.title,
            "status_code": page.status_code,
            "fetch_latency_ms": round(page.fetch_latency_ms, 2),
            "links_discovered": len(page.links),
            "outgoing_links": list(page.links),
            "outgoing_anchor_texts": dict(page.link_anchors),
            "outgoing_edges": [
                {
                    "url": target,
                    "anchor": str(page.link_anchors.get(target) or ""),
                }
                for target in page.links
            ],
        }
        with self._manifest_lock:
            with self.manifest_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        return page

    def _to_checkpoint_payload(self) -> dict[str, Any]:
        return {
            "front_queues": [
                [self._request_to_json(item) for item in queue] for queue in self._front_queues
            ],
            "pending_by_host": {
                host: [self._request_to_json(item) for item in queue]
                for host, queue in self._pending_by_host.items()
            },
            "host_next_allowed_at": self._host_next_allowed_at,
            "host_enqueued_count": self._host_enqueued_count,
            "host_saved_count": self._host_saved_count,
            "queued_or_seen_urls": sorted(self._queued_or_seen_urls),
            "content_signatures": [list(item) for item in self._content_signatures],
            "stats": self._stats,
            "timestamp": time.time(),
        }

    def _save_checkpoint(self) -> None:
        payload = self._to_checkpoint_payload()
        temp_path = self.checkpoint_path.with_suffix(".tmp")
        temp_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        temp_path.replace(self.checkpoint_path)

    def _load_checkpoint(self) -> bool:
        if not self.checkpoint_path.exists():
            return False
        try:
            payload = json.loads(self.checkpoint_path.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            return False
        front_payload = payload.get("front_queues") or []
        for idx, entries in enumerate(front_payload):
            if idx >= len(self._front_queues):
                break
            queue = self._front_queues[idx]
            queue.clear()
            for raw_item in entries:
                queue.append(self._request_from_json(raw_item))
        self._pending_by_host.clear()
        for host, entries in (payload.get("pending_by_host") or {}).items():
            parsed_entries = deque(self._request_from_json(raw_item) for raw_item in entries)
            if parsed_entries:
                self._pending_by_host[str(host)] = parsed_entries
        self._host_next_allowed_at = {
            str(key): float(value)
            for key, value in (payload.get("host_next_allowed_at") or {}).items()
        }
        self._host_enqueued_count = {
            str(key): int(value)
            for key, value in (payload.get("host_enqueued_count") or {}).items()
        }
        self._host_saved_count = {
            str(key): int(value) for key, value in (payload.get("host_saved_count") or {}).items()
        }
        self._queued_or_seen_urls = set(payload.get("queued_or_seen_urls") or [])
        self._content_signatures = [
            tuple(int(value) for value in row) for row in (payload.get("content_signatures") or [])
        ]
        stats_payload = payload.get("stats") or {}
        for key in self._stats:
            self._stats[key] = int(stats_payload.get(key, self._stats[key]))
        return True

    def _fetch_request(self, request: CrawlRequest) -> _FetchResult:
        started_at = time.monotonic()
        if not self._is_url_allowed_by_robots(request.url):
            return _FetchResult(request=request, skip_reason="robots")
        host = _url_host(request.url)
        dns_ip = self._resolve_dns_ip(host)
        url_request = Request(
            request.url,
            headers={"User-Agent": self.config.user_agent, "Accept": "text/html, text/plain"},
        )
        try:
            with urlopen(url_request, timeout=self.config.request_timeout_seconds) as response:
                status_code = int(getattr(response, "status", 200) or 200)
                content_type = str(response.headers.get("Content-Type") or "").lower()
                raw_bytes = response.read(self.config.max_content_bytes)
        except (HTTPError, URLError, TimeoutError) as exc:
            return _FetchResult(request=request, error=exc.__class__.__name__)
        if "text/html" not in content_type and "text/plain" not in content_type:
            return _FetchResult(request=request, skip_reason="non_html")
        text = raw_bytes.decode("utf-8", errors="ignore")
        title, body_text, links, link_anchors = self._extract_html_payload(
            base_url=request.url,
            html=text,
        )
        cleaned_body = re.sub(r"\s+", " ", body_text).strip()
        if len(cleaned_body) < self.config.min_text_chars:
            return _FetchResult(request=request, skip_reason="thin_content")
        latency_ms = (time.monotonic() - started_at) * 1000.0
        page = CrawlPage(
            url=request.url,
            host=host,
            depth=request.depth,
            title=title or host,
            text=cleaned_body,
            status_code=status_code,
            content_type=content_type[:120],
            fetched_at=time.time(),
            fetch_latency_ms=latency_ms,
            dns_ip=dns_ip,
            links=links,
            link_anchors=link_anchors,
            discovered_from=request.discovered_from,
        )
        return _FetchResult(request=request, page=page)

    def run(self) -> CrawlRunSummary:
        started_at = time.monotonic()
        resumed = False
        if self.config.resume_from_checkpoint:
            resumed = self._load_checkpoint()
        if not resumed:
            for seed in self.config.seeds:
                canonical = canonicalize_url(seed)
                if not canonical:
                    continue
                self._enqueue(
                    CrawlRequest(
                        url=canonical,
                        depth=0,
                        priority=self._compute_priority(url=canonical, depth=0),
                    )
                )

        futures: dict[Future[_FetchResult], tuple[str, float]] = {}
        with ThreadPoolExecutor(max_workers=self.config.workers) as executor:
            while True:
                if self._stats["pages_saved"] >= self.config.max_pages:
                    break
                while len(futures) < self.config.workers:
                    host, request, wait_seconds = self._next_schedulable_request()
                    if request is None or host is None:
                        if not futures and self._has_frontier_work():
                            time.sleep(wait_seconds)
                        break
                    self._active_hosts.add(host)
                    futures[executor.submit(self._fetch_request, request)] = (
                        host,
                        time.monotonic(),
                    )
                if not futures:
                    if not self._has_frontier_work():
                        break
                    continue

                done, _ = wait(list(futures.keys()), timeout=0.3, return_when=FIRST_COMPLETED)
                for future in done:
                    host, host_started_at = futures.pop(future)
                    self._active_hosts.discard(host)
                    elapsed = max(time.monotonic() - host_started_at, 0.001)
                    self._host_next_allowed_at[host] = time.monotonic() + max(
                        self.config.min_host_delay_seconds,
                        elapsed * self.config.politeness_multiplier,
                    )
                    try:
                        result = future.result()
                    except Exception:
                        self._stats["errors"] += 1
                        continue

                    if result.error:
                        self._stats["errors"] += 1
                        continue
                    if result.skip_reason == "robots":
                        self._stats["pages_skipped_robots"] += 1
                        continue
                    if result.skip_reason in {"non_html", "thin_content"}:
                        self._stats["pages_skipped_non_html"] += 1
                        continue
                    page = result.page
                    if page is None:
                        self._stats["errors"] += 1
                        continue

                    self._stats["pages_fetched"] += 1
                    if self._is_near_duplicate_content(page.text):
                        self._stats["pages_skipped_near_duplicate"] += 1
                        continue
                    if self._host_saved_count.get(host, 0) >= self.config.max_pages_per_host:
                        continue

                    persisted = self._persist_page(page)
                    self._stats["pages_saved"] += 1
                    self._host_saved_count[host] = self._host_saved_count.get(host, 0) + 1
                    if self._stats["pages_saved"] % self.config.checkpoint_every_pages == 0:
                        self._save_checkpoint()

                    if persisted.depth >= self.config.max_depth:
                        continue
                    for link in persisted.links:
                        link_host = _url_host(link)
                        if not self._domain_allowed(link_host):
                            continue
                        self._enqueue(
                            CrawlRequest(
                                url=link,
                                depth=persisted.depth + 1,
                                priority=self._compute_priority(
                                    url=link,
                                    depth=persisted.depth + 1,
                                ),
                                discovered_from=persisted.url,
                            )
                        )

        self._save_checkpoint()
        elapsed_seconds = time.monotonic() - started_at
        return CrawlRunSummary(
            pages_fetched=int(self._stats["pages_fetched"]),
            pages_saved=int(self._stats["pages_saved"]),
            pages_skipped_robots=int(self._stats["pages_skipped_robots"]),
            pages_skipped_non_html=int(self._stats["pages_skipped_non_html"]),
            pages_skipped_near_duplicate=int(self._stats["pages_skipped_near_duplicate"]),
            urls_discovered=int(self._stats["urls_discovered"]),
            frontier_pending=int(self._frontier_pending_count()),
            errors=int(self._stats["errors"]),
            checkpoint_path=str(self.checkpoint_path),
            output_dir=str(self.output_dir),
            elapsed_seconds=round(elapsed_seconds, 3),
        )
