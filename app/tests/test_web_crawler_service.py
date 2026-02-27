import json
import time

from app.services.web_crawler_service import (
    CrawlPage,
    CrawlRequest,
    WebCrawlerConfig,
    WebCrawlerService,
    canonicalize_url,
)


def test_canonicalize_url_strips_tracking_and_fragment():
    value = "HTTPS://Who.Int/path/?utm_source=x&a=1&fbclid=zz#top"
    assert canonicalize_url(value) == "https://who.int/path?a=1"


def test_extract_html_payload_keeps_allowed_domain_links(tmp_path):
    config = WebCrawlerConfig(
        seeds=["https://www.who.int/health-topics/sepsis"],
        output_dir=str(tmp_path / "out"),
        checkpoint_path=str(tmp_path / "ckpt.json"),
        allowed_domains=["who.int"],
    )
    service = WebCrawlerService(config=config)
    html = """
    <html>
      <head><title>Sepsis overview</title></head>
      <body>
        <p>Clinical sepsis management and initial approach.</p>
        <a href="/guidelines">Guidelines</a>
        <a href="https://example.com/x">Other</a>
      </body>
    </html>
    """
    title, text, links, anchors = service._extract_html_payload(
        base_url="https://www.who.int/health-topics/sepsis",
        html=html,
    )
    assert title == "Sepsis overview"
    assert "Clinical sepsis management" in text
    assert links == ["https://www.who.int/guidelines"]
    assert anchors == {"https://www.who.int/guidelines": "Guidelines"}


def test_near_duplicate_detection_uses_signature_threshold(tmp_path):
    config = WebCrawlerConfig(
        seeds=["https://www.who.int/health-topics/sepsis"],
        output_dir=str(tmp_path / "out"),
        checkpoint_path=str(tmp_path / "ckpt.json"),
        allowed_domains=["who.int"],
        near_duplicate_threshold=0.75,
    )
    service = WebCrawlerService(config=config)
    first_text = (
        "Clinical management of sepsis in emergency settings includes fluids, "
        "blood cultures, lactate monitoring and early antibiotics."
    )
    second_text = (
        "Clinical management of sepsis in emergency settings includes fluids, "
        "blood cultures, lactate monitoring and early antibiotics in first hour."
    )
    assert service._is_near_duplicate_content(first_text) is False
    assert service._is_near_duplicate_content(second_text) is True


def test_checkpoint_roundtrip_restores_frontier_and_stats(tmp_path):
    output_dir = tmp_path / "out"
    checkpoint_path = tmp_path / "ckpt.json"
    config = WebCrawlerConfig(
        seeds=["https://www.who.int/health-topics/sepsis"],
        output_dir=str(output_dir),
        checkpoint_path=str(checkpoint_path),
        allowed_domains=["who.int"],
    )
    service = WebCrawlerService(config=config)
    service._enqueue(
        CrawlRequest(
            url="https://www.who.int/health-topics/sepsis",
            depth=0,
            priority=90,
        )
    )
    service._stats["pages_saved"] = 3
    service._save_checkpoint()

    restored = WebCrawlerService(config=config)
    loaded = restored._load_checkpoint()
    assert loaded is True
    assert restored._frontier_pending_count() >= 1
    assert restored._stats["pages_saved"] == 3


def test_priority_prefers_authoritative_domains(tmp_path):
    config = WebCrawlerConfig(
        seeds=["https://www.who.int/health-topics/sepsis"],
        output_dir=str(tmp_path / "out"),
        checkpoint_path=str(tmp_path / "ckpt.json"),
        allowed_domains=["who.int", "example.com"],
    )
    service = WebCrawlerService(config=config)
    who_priority = service._compute_priority(url="https://www.who.int/x", depth=0)
    generic_priority = service._compute_priority(url="https://www.example.com/x", depth=0)
    assert who_priority > generic_priority


def test_persist_page_writes_outgoing_edges_and_anchor_text(tmp_path):
    config = WebCrawlerConfig(
        seeds=["https://www.who.int/health-topics/sepsis"],
        output_dir=str(tmp_path / "out"),
        checkpoint_path=str(tmp_path / "ckpt.json"),
        allowed_domains=["who.int"],
    )
    service = WebCrawlerService(config=config)
    page = CrawlPage(
        url="https://www.who.int/health-topics/sepsis",
        host="www.who.int",
        depth=1,
        title="Sepsis",
        text="Clinical overview of sepsis response in emergency settings.",
        status_code=200,
        content_type="text/html",
        fetched_at=time.time(),
        fetch_latency_ms=120.0,
        dns_ip="127.0.0.1",
        links=["https://www.who.int/guidelines"],
        link_anchors={"https://www.who.int/guidelines": "Sepsis guidelines"},
        discovered_from="https://www.who.int/health-topics",
    )
    service._persist_page(page)
    lines = service.manifest_path.read_text(encoding="utf-8").strip().splitlines()
    assert lines
    payload = json.loads(lines[-1])
    assert payload["outgoing_links"] == ["https://www.who.int/guidelines"]
    assert payload["outgoing_anchor_texts"] == {
        "https://www.who.int/guidelines": "Sepsis guidelines"
    }
    assert payload["outgoing_edges"] == [
        {
            "url": "https://www.who.int/guidelines",
            "anchor": "Sepsis guidelines",
        }
    ]
