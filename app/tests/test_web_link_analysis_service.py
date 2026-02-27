import json

from app.services.web_link_analysis_service import WebLinkAnalysisService


def _write_manifest(path, records):
    lines = [json.dumps(record, ensure_ascii=False) for record in records]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_build_snapshot_computes_topic_pagerank_bias(tmp_path):
    manifest_path = tmp_path / "crawl_manifest.jsonl"
    snapshot_path = tmp_path / "snapshot.json"
    _write_manifest(
        manifest_path,
        [
            {
                "url": "https://trusted.org/a",
                "outgoing_edges": [
                    {"url": "https://untrusted.net/x", "anchor": "clinical resource"},
                ],
            },
            {
                "url": "https://untrusted.net/x",
                "outgoing_edges": [
                    {"url": "https://untrusted.net/y", "anchor": "sepsis management"},
                ],
            },
            {
                "url": "https://untrusted.net/y",
                "outgoing_edges": [
                    {"url": "https://untrusted.net/x", "anchor": "sepsis protocol"},
                ],
            },
        ],
    )

    summary = WebLinkAnalysisService.build_snapshot(
        manifest_path=str(manifest_path),
        output_path=str(snapshot_path),
        trusted_domains=["trusted.org"],
    )
    assert summary.nodes == 3
    payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    trusted_url = "https://trusted.org/a"
    assert payload["topic_pagerank"][trusted_url] > payload["global_pagerank"][trusted_url]


def test_score_candidates_uses_anchor_relevance_and_hits(tmp_path):
    manifest_path = tmp_path / "crawl_manifest.jsonl"
    snapshot_path = tmp_path / "snapshot.json"
    _write_manifest(
        manifest_path,
        [
            {
                "url": "https://trusted.org/root",
                "outgoing_edges": [
                    {"url": "https://trusted.org/sepsis", "anchor": "sepsis guideline"},
                    {"url": "https://trusted.org/other", "anchor": "respiratory care"},
                ],
            },
            {
                "url": "https://trusted.org/index",
                "outgoing_edges": [
                    {"url": "https://trusted.org/sepsis", "anchor": "sepsis protocol"},
                ],
            },
            {
                "url": "https://trusted.org/sepsis",
                "outgoing_edges": [
                    {"url": "https://trusted.org/root", "anchor": "critical care"},
                ],
            },
        ],
    )
    WebLinkAnalysisService.build_snapshot(
        manifest_path=str(manifest_path),
        output_path=str(snapshot_path),
        trusted_domains=["trusted.org"],
    )

    scores, trace = WebLinkAnalysisService.score_candidates(
        query="sepsis manejo urgencias",
        candidate_urls=[
            "https://trusted.org/sepsis",
            "https://trusted.org/other",
        ],
        snapshot_path=str(snapshot_path),
        max_hits_base=80,
    )

    assert trace["web_search_link_analysis_loaded"] == "1"
    assert int(trace["web_search_link_analysis_hits_base"]) >= 2
    assert scores["https://trusted.org/sepsis"]["anchor_relevance"] > 0
    assert (
        scores["https://trusted.org/sepsis"]["link_score"]
        > scores["https://trusted.org/other"]["link_score"]
    )
