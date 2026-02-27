"""
Builds link-analysis snapshot from crawler manifest.

Usage:
    python -m app.scripts.build_web_link_analysis
"""
from __future__ import annotations

import argparse
import json

from app.services.knowledge_source_service import KnowledgeSourceService
from app.services.web_link_analysis_service import WebLinkAnalysisService


def _parse_csv_domains(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [item.strip().lower() for item in raw.split(",") if item.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Build web link-analysis snapshot")
    parser.add_argument(
        "--manifest-path",
        default="docs/web_raw/crawl_manifest.jsonl",
        help="Crawler manifest path (JSONL)",
    )
    parser.add_argument(
        "--output-path",
        default="docs/web_raw/link_analysis_snapshot.json",
        help="Output snapshot path (JSON)",
    )
    parser.add_argument(
        "--trusted-domains",
        default="",
        help=(
            "CSV of trusted domains. If omitted, uses the platform web whitelist "
            "(KnowledgeSourceService)."
        ),
    )
    parser.add_argument(
        "--pagerank-alpha",
        type=float,
        default=0.15,
        help="Teleport probability for PageRank [0..1], default 0.15",
    )
    parser.add_argument(
        "--pagerank-iterations",
        type=int,
        default=50,
        help="Power iterations for PageRank",
    )
    parser.add_argument(
        "--hits-iterations",
        type=int,
        default=20,
        help="Power iterations for HITS",
    )
    args = parser.parse_args()

    trusted_domains = _parse_csv_domains(args.trusted_domains)
    if not trusted_domains:
        trusted_domains = KnowledgeSourceService.get_allowed_domains()
    summary = WebLinkAnalysisService.build_snapshot(
        manifest_path=args.manifest_path,
        output_path=args.output_path,
        trusted_domains=trusted_domains,
        pagerank_alpha=min(max(float(args.pagerank_alpha), 0.0), 1.0),
        pagerank_iterations=max(5, int(args.pagerank_iterations)),
        hits_iterations=max(5, int(args.hits_iterations)),
    )
    print(json.dumps(summary.__dict__, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
