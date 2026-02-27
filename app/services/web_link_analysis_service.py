"""
Link analysis utilities for web source authority scoring.

Includes:
- Anchor text aggregation.
- Global PageRank.
- Topic-specific PageRank.
- HITS (hub/authority), including a query-focused base-set variant.
"""
from __future__ import annotations

import json
import math
import re
import threading
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from app.services.web_crawler_service import canonicalize_url


@dataclass(slots=True)
class WebLinkAnalysisBuildSummary:
    nodes: int
    edges: int
    topic_seed_nodes: int
    manifest_path: str
    output_path: str


class WebLinkAnalysisService:
    """Builds and consumes link-analysis snapshots for runtime ranking."""

    _TOKEN_PATTERN = re.compile(r"[a-z0-9]{3,}")
    _MAX_ANCHOR_TERMS_PER_URL = 64

    _CACHE_LOCK = threading.Lock()
    _SNAPSHOT_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}

    @classmethod
    def _normalize_text(cls, text: str) -> str:
        return re.sub(r"\s+", " ", str(text or "")).strip().lower()

    @classmethod
    def _tokenize(cls, text: str) -> list[str]:
        return cls._TOKEN_PATTERN.findall(cls._normalize_text(text))

    @staticmethod
    def _domain_matches(host: str, allowed_domains: set[str]) -> bool:
        if not allowed_domains:
            return True
        for domain in allowed_domains:
            if host == domain or host.endswith(f".{domain}"):
                return True
        return False

    @staticmethod
    def _build_incoming(adjacency: dict[str, list[str]]) -> dict[str, list[str]]:
        incoming: dict[str, list[str]] = defaultdict(list)
        for source, targets in adjacency.items():
            for target in targets:
                incoming[target].append(source)
        return dict(incoming)

    @classmethod
    def _extract_outgoing_edges(cls, record: dict[str, Any]) -> list[tuple[str, str]]:
        edges: list[tuple[str, str]] = []
        outgoing_edges = record.get("outgoing_edges")
        if isinstance(outgoing_edges, list):
            for row in outgoing_edges:
                if not isinstance(row, dict):
                    continue
                target = canonicalize_url(str(row.get("url") or ""))
                if not target:
                    continue
                anchor = str(row.get("anchor") or "")
                edges.append((target, anchor))
            if edges:
                return edges

        outgoing_anchor_texts = record.get("outgoing_anchor_texts") or {}
        if isinstance(outgoing_anchor_texts, dict):
            for raw_target, raw_anchor in outgoing_anchor_texts.items():
                target = canonicalize_url(str(raw_target or ""))
                if not target:
                    continue
                edges.append((target, str(raw_anchor or "")))

        outgoing_links = record.get("outgoing_links")
        if isinstance(outgoing_links, list):
            for raw_target in outgoing_links:
                target = canonicalize_url(str(raw_target or ""))
                if not target:
                    continue
                if not any(existing_target == target for existing_target, _ in edges):
                    edges.append((target, ""))
            return edges

        legacy_links = record.get("links")
        if isinstance(legacy_links, list):
            for raw_target in legacy_links:
                target = canonicalize_url(str(raw_target or ""))
                if not target:
                    continue
                if not any(existing_target == target for existing_target, _ in edges):
                    edges.append((target, ""))
        return edges

    @classmethod
    def _compute_pagerank(
        cls,
        adjacency: dict[str, list[str]],
        *,
        alpha: float,
        iterations: int,
        personalization: dict[str, float] | None = None,
    ) -> dict[str, float]:
        nodes = sorted(adjacency.keys())
        if not nodes:
            return {}
        node_count = len(nodes)
        if personalization:
            personal = {node: max(float(personalization.get(node, 0.0)), 0.0) for node in nodes}
            personal_total = sum(personal.values())
            if personal_total <= 0:
                personal = {node: 1.0 / node_count for node in nodes}
            else:
                personal = {node: value / personal_total for node, value in personal.items()}
        else:
            personal = {node: 1.0 / node_count for node in nodes}

        scores = {node: 1.0 / node_count for node in nodes}
        damping = max(0.0, min(1.0, 1.0 - alpha))
        teleport = max(0.0, min(1.0, alpha))
        for _ in range(max(1, iterations)):
            updated = {node: teleport * personal[node] for node in nodes}
            dangling_mass = sum(scores[node] for node in nodes if not adjacency.get(node))
            if dangling_mass > 0:
                for node in nodes:
                    updated[node] += damping * dangling_mass * personal[node]
            for source in nodes:
                targets = adjacency.get(source) or []
                if not targets:
                    continue
                share = damping * scores[source] / len(targets)
                for target in targets:
                    updated[target] = updated.get(target, 0.0) + share
            total = sum(updated.values())
            if total > 0:
                scores = {node: updated.get(node, 0.0) / total for node in nodes}
            else:
                scores = dict(updated)
        return scores

    @classmethod
    def _compute_hits(
        cls,
        adjacency: dict[str, list[str]],
        *,
        iterations: int,
        base_nodes: set[str] | None = None,
    ) -> tuple[dict[str, float], dict[str, float]]:
        all_nodes = set(adjacency.keys())
        if base_nodes:
            nodes = sorted(node for node in all_nodes if node in base_nodes)
        else:
            nodes = sorted(all_nodes)
        if not nodes:
            return {}, {}
        node_set = set(nodes)
        outgoing = {
            node: [target for target in adjacency.get(node, []) if target in node_set]
            for node in nodes
        }
        incoming: dict[str, list[str]] = {node: [] for node in nodes}
        for source, targets in outgoing.items():
            for target in targets:
                incoming[target].append(source)

        authorities = {node: 1.0 for node in nodes}
        hubs = {node: 1.0 for node in nodes}
        for _ in range(max(1, iterations)):
            next_authorities = {
                node: sum(hubs[source] for source in incoming[node]) for node in nodes
            }
            authority_norm = (
                math.sqrt(sum(value * value for value in next_authorities.values())) or 1.0
            )
            authorities = {
                node: next_authorities[node] / authority_norm for node in nodes
            }

            next_hubs = {
                node: sum(authorities[target] for target in outgoing[node]) for node in nodes
            }
            hub_norm = math.sqrt(sum(value * value for value in next_hubs.values())) or 1.0
            hubs = {node: next_hubs[node] / hub_norm for node in nodes}

        max_authority = max(authorities.values()) or 1.0
        max_hub = max(hubs.values()) or 1.0
        normalized_authorities = {node: authorities[node] / max_authority for node in nodes}
        normalized_hubs = {node: hubs[node] / max_hub for node in nodes}
        return normalized_authorities, normalized_hubs

    @classmethod
    def build_snapshot(
        cls,
        *,
        manifest_path: str,
        output_path: str,
        trusted_domains: list[str],
        pagerank_alpha: float = 0.15,
        pagerank_iterations: int = 50,
        hits_iterations: int = 20,
    ) -> WebLinkAnalysisBuildSummary:
        manifest = Path(manifest_path)
        if not manifest.exists():
            raise FileNotFoundError(f"Manifest no encontrado: {manifest}")

        trusted = {
            str(item or "").strip().lower()
            for item in trusted_domains
            if str(item or "").strip()
        }
        adjacency_sets: dict[str, set[str]] = defaultdict(set)
        incoming_anchor_terms: dict[str, Counter[str]] = defaultdict(Counter)
        nodes: set[str] = set()

        with manifest.open("r", encoding="utf-8") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except ValueError:
                    continue
                source = canonicalize_url(str(record.get("url") or ""))
                if not source:
                    continue
                nodes.add(source)
                outgoing_edges = cls._extract_outgoing_edges(record)
                for target, anchor_text in outgoing_edges:
                    adjacency_sets[source].add(target)
                    nodes.add(target)
                    for token in cls._tokenize(anchor_text):
                        incoming_anchor_terms[target][token] += 1

        adjacency = {node: sorted(adjacency_sets.get(node, set())) for node in sorted(nodes)}
        topic_personalization = {
            node: 1.0
            for node in adjacency
            if cls._domain_matches((urlparse(node).hostname or "").lower(), trusted)
        }

        global_pagerank = cls._compute_pagerank(
            adjacency,
            alpha=pagerank_alpha,
            iterations=pagerank_iterations,
            personalization=None,
        )
        topic_pagerank = cls._compute_pagerank(
            adjacency,
            alpha=pagerank_alpha,
            iterations=pagerank_iterations,
            personalization=topic_personalization if topic_personalization else None,
        )
        hits_authority, hits_hub = cls._compute_hits(
            adjacency,
            iterations=hits_iterations,
            base_nodes=None,
        )

        global_max = max(global_pagerank.values()) if global_pagerank else 0.0
        topic_max = max(topic_pagerank.values()) if topic_pagerank else 0.0
        authority_max = max(hits_authority.values()) if hits_authority else 0.0
        hub_max = max(hits_hub.values()) if hits_hub else 0.0

        compact_anchor_terms: dict[str, dict[str, int]] = {}
        for node, counts in incoming_anchor_terms.items():
            top_terms = counts.most_common(cls._MAX_ANCHOR_TERMS_PER_URL)
            if top_terms:
                compact_anchor_terms[node] = {term: int(freq) for term, freq in top_terms}

        snapshot = {
            "version": 1,
            "generated_at_epoch": round(time.time(), 3),
            "manifest_path": str(manifest.resolve()),
            "stats": {
                "nodes": len(adjacency),
                "edges": sum(len(targets) for targets in adjacency.values()),
                "topic_seed_nodes": len(topic_personalization),
                "global_pagerank_max": float(global_max),
                "topic_pagerank_max": float(topic_max),
                "hits_authority_max": float(authority_max),
                "hits_hub_max": float(hub_max),
                "pagerank_alpha": float(pagerank_alpha),
                "pagerank_iterations": int(pagerank_iterations),
                "hits_iterations": int(hits_iterations),
            },
            "adjacency": adjacency,
            "global_pagerank": global_pagerank,
            "topic_pagerank": topic_pagerank,
            "hits_authority": hits_authority,
            "hits_hub": hits_hub,
            "incoming_anchor_terms": compact_anchor_terms,
        }

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")

        # Invalidate cache for this snapshot path.
        with cls._CACHE_LOCK:
            cls._SNAPSHOT_CACHE.pop(str(output.resolve()), None)
            cls._SNAPSHOT_CACHE.pop(str(output), None)

        return WebLinkAnalysisBuildSummary(
            nodes=len(adjacency),
            edges=sum(len(targets) for targets in adjacency.values()),
            topic_seed_nodes=len(topic_personalization),
            manifest_path=str(manifest),
            output_path=str(output),
        )

    @classmethod
    def _load_snapshot(cls, path: str) -> tuple[dict[str, Any] | None, str | None]:
        snapshot_path = Path(path)
        if not snapshot_path.exists():
            return None, "snapshot_missing"
        try:
            stat = snapshot_path.stat()
        except OSError:
            return None, "snapshot_stat_error"
        cache_key = str(snapshot_path.resolve())
        with cls._CACHE_LOCK:
            cached = cls._SNAPSHOT_CACHE.get(cache_key)
            if cached and abs(cached[0] - stat.st_mtime) < 1e-6:
                return cached[1], None
        try:
            raw_payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None, "snapshot_parse_error"

        adjacency_raw = raw_payload.get("adjacency") or {}
        adjacency: dict[str, list[str]] = {}
        for raw_source, raw_targets in adjacency_raw.items():
            source = canonicalize_url(str(raw_source or ""))
            if not source:
                continue
            targets: list[str] = []
            if isinstance(raw_targets, list):
                for raw_target in raw_targets:
                    target = canonicalize_url(str(raw_target or ""))
                    if target:
                        targets.append(target)
            adjacency[source] = list(dict.fromkeys(targets))

        incoming_anchor_raw = raw_payload.get("incoming_anchor_terms") or {}
        incoming_anchor_terms: dict[str, dict[str, int]] = {}
        if isinstance(incoming_anchor_raw, dict):
            for raw_url, raw_terms in incoming_anchor_raw.items():
                url = canonicalize_url(str(raw_url or ""))
                if not url or not isinstance(raw_terms, dict):
                    continue
                parsed_terms: dict[str, int] = {}
                for term, count in raw_terms.items():
                    token = cls._normalize_text(str(term))
                    if not token:
                        continue
                    try:
                        parsed_terms[token] = max(0, int(count))
                    except (TypeError, ValueError):
                        continue
                if parsed_terms:
                    incoming_anchor_terms[url] = parsed_terms

        def _normalized_scores(
            raw_scores: dict[str, Any] | None,
            *,
            fallback_max: float,
        ) -> dict[str, float]:
            parsed: dict[str, float] = {}
            if isinstance(raw_scores, dict):
                for raw_url, value in raw_scores.items():
                    url = canonicalize_url(str(raw_url or ""))
                    if not url:
                        continue
                    try:
                        parsed[url] = max(float(value), 0.0)
                    except (TypeError, ValueError):
                        continue
            max_score = max(parsed.values()) if parsed else 0.0
            denominator = max(max_score, fallback_max, 1e-9)
            return {url: min(value / denominator, 1.0) for url, value in parsed.items()}

        stats = raw_payload.get("stats") or {}
        try:
            global_max = float(stats.get("global_pagerank_max") or 0.0)
        except (TypeError, ValueError):
            global_max = 0.0
        try:
            topic_max = float(stats.get("topic_pagerank_max") or 0.0)
        except (TypeError, ValueError):
            topic_max = 0.0
        try:
            authority_max = float(stats.get("hits_authority_max") or 0.0)
        except (TypeError, ValueError):
            authority_max = 0.0
        try:
            hub_max = float(stats.get("hits_hub_max") or 0.0)
        except (TypeError, ValueError):
            hub_max = 0.0

        snapshot = {
            "adjacency": adjacency,
            "incoming": cls._build_incoming(adjacency),
            "incoming_anchor_terms": incoming_anchor_terms,
            "global_pagerank_norm": _normalized_scores(
                raw_payload.get("global_pagerank"), fallback_max=global_max
            ),
            "topic_pagerank_norm": _normalized_scores(
                raw_payload.get("topic_pagerank"), fallback_max=topic_max
            ),
            "hits_authority_norm": _normalized_scores(
                raw_payload.get("hits_authority"), fallback_max=authority_max
            ),
            "hits_hub_norm": _normalized_scores(
                raw_payload.get("hits_hub"), fallback_max=hub_max
            ),
            "stats": {
                "nodes": int(stats.get("nodes") or len(adjacency)),
                "edges": int(stats.get("edges") or 0),
                "topic_seed_nodes": int(stats.get("topic_seed_nodes") or 0),
            },
        }
        with cls._CACHE_LOCK:
            cls._SNAPSHOT_CACHE[cache_key] = (stat.st_mtime, snapshot)
        return snapshot, None

    @classmethod
    def _anchor_relevance(cls, query_tokens: set[str], anchor_terms: dict[str, int]) -> float:
        if not query_tokens or not anchor_terms:
            return 0.0
        shared = sum(freq for token, freq in anchor_terms.items() if token in query_tokens)
        total = sum(anchor_terms.values())
        if total <= 0:
            return 0.0
        coverage = shared / total
        return min(max(coverage * 1.5, 0.0), 1.0)

    @classmethod
    def _compute_query_hits(
        cls,
        *,
        snapshot: dict[str, Any],
        query_tokens: set[str],
        candidate_urls: set[str],
        max_hits_base: int,
    ) -> tuple[dict[str, float], dict[str, float], int]:
        adjacency = snapshot.get("adjacency") or {}
        incoming = snapshot.get("incoming") or {}
        if not adjacency:
            return {}, {}, 0

        roots = set(candidate_urls)
        incoming_anchor_terms = snapshot.get("incoming_anchor_terms") or {}
        topic_scores = snapshot.get("topic_pagerank_norm") or {}
        if query_tokens:
            ranked_roots: list[tuple[float, float, str]] = []
            for url, terms in incoming_anchor_terms.items():
                overlap = sum(freq for token, freq in terms.items() if token in query_tokens)
                if overlap <= 0:
                    continue
                ranked_roots.append((float(overlap), float(topic_scores.get(url, 0.0)), url))
            ranked_roots.sort(key=lambda row: (row[0], row[1], row[2]), reverse=True)
            for _, _, url in ranked_roots[: max(1, max_hits_base // 2)]:
                roots.add(url)
                if len(roots) >= max_hits_base:
                    break

        base_set = set(roots)
        for url in list(roots):
            for target in adjacency.get(url, []):
                base_set.add(target)
                if len(base_set) >= max_hits_base:
                    break
            if len(base_set) >= max_hits_base:
                break
            for source in incoming.get(url, []):
                base_set.add(source)
                if len(base_set) >= max_hits_base:
                    break
            if len(base_set) >= max_hits_base:
                break

        if len(base_set) > max_hits_base:
            global_scores = snapshot.get("global_pagerank_norm") or {}
            ranked = sorted(
                base_set,
                key=lambda url: (
                    float(topic_scores.get(url, 0.0)),
                    float(global_scores.get(url, 0.0)),
                    url,
                ),
                reverse=True,
            )
            base_set = set(ranked[:max_hits_base])

        if not base_set:
            return {}, {}, 0
        authorities, hubs = cls._compute_hits(
            adjacency,
            iterations=12,
            base_nodes=base_set,
        )
        return authorities, hubs, len(base_set)

    @classmethod
    def score_candidates(
        cls,
        *,
        query: str,
        candidate_urls: list[str],
        snapshot_path: str,
        max_hits_base: int = 120,
    ) -> tuple[dict[str, dict[str, float]], dict[str, str]]:
        snapshot, error = cls._load_snapshot(snapshot_path)
        trace: dict[str, str] = {}
        if snapshot is None:
            trace["web_search_link_analysis_loaded"] = "0"
            if error:
                trace["web_search_link_analysis_error"] = error
            return {}, trace

        canonical_candidates = [
            canonicalize_url(url) for url in candidate_urls if canonicalize_url(url)
        ]
        if not canonical_candidates:
            trace["web_search_link_analysis_loaded"] = "1"
            trace["web_search_link_analysis_candidates"] = "0"
            return {}, trace

        query_tokens = set(cls._tokenize(query))
        candidate_set = set(canonical_candidates)
        authorities, hubs, hits_base_size = cls._compute_query_hits(
            snapshot=snapshot,
            query_tokens=query_tokens,
            candidate_urls=candidate_set,
            max_hits_base=max(20, int(max_hits_base)),
        )

        global_scores = snapshot.get("global_pagerank_norm") or {}
        topic_scores = snapshot.get("topic_pagerank_norm") or {}
        default_authorities = snapshot.get("hits_authority_norm") or {}
        default_hubs = snapshot.get("hits_hub_norm") or {}
        incoming_anchor_terms = snapshot.get("incoming_anchor_terms") or {}

        scored: dict[str, dict[str, float]] = {}
        for url in canonical_candidates:
            global_pr = float(global_scores.get(url, 0.0))
            topic_pr = float(topic_scores.get(url, 0.0))
            hits_authority = float(authorities.get(url, default_authorities.get(url, 0.0)))
            hits_hub = float(hubs.get(url, default_hubs.get(url, 0.0)))
            anchor_relevance = cls._anchor_relevance(
                query_tokens,
                incoming_anchor_terms.get(url, {}),
            )
            link_score = min(
                max(
                    (0.30 * global_pr)
                    + (0.35 * topic_pr)
                    + (0.20 * hits_authority)
                    + (0.10 * hits_hub)
                    + (0.05 * anchor_relevance),
                    0.0,
                ),
                1.0,
            )
            scored[url] = {
                "global_pagerank": global_pr,
                "topic_pagerank": topic_pr,
                "hits_authority": hits_authority,
                "hits_hub": hits_hub,
                "anchor_relevance": anchor_relevance,
                "link_score": link_score,
            }

        avg_link_score = (
            sum(item["link_score"] for item in scored.values()) / len(scored)
            if scored
            else 0.0
        )
        stats = snapshot.get("stats") or {}
        trace.update(
            {
                "web_search_link_analysis_loaded": "1",
                "web_search_link_analysis_candidates": str(len(canonical_candidates)),
                "web_search_link_analysis_nodes": str(int(stats.get("nodes") or 0)),
                "web_search_link_analysis_edges": str(int(stats.get("edges") or 0)),
                "web_search_link_analysis_topic_seed_nodes": str(
                    int(stats.get("topic_seed_nodes") or 0)
                ),
                "web_search_link_analysis_hits_base": str(int(hits_base_size)),
                "web_search_link_analysis_avg_score": f"{avg_link_score:.3f}",
            }
        )
        return scored, trace
