"""
Crawler web clinico local (polite) para alimentar corpus RAG.

Uso rapido:
    python -m app.scripts.crawl_clinical_web --max-pages 80
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.services.knowledge_source_service import KnowledgeSourceService
from app.services.web_crawler_service import WebCrawlerConfig, WebCrawlerService

DEFAULT_SEEDS = [
    "https://www.who.int/health-topics/sepsis",
    "https://www.cdc.gov/sepsis/",
    "https://pubmed.ncbi.nlm.nih.gov/?term=sepsis+guideline",
]


def _parse_csv_domains(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [item.strip().lower() for item in raw.split(",") if item.strip()]


def _parse_seeds(values: list[str] | None) -> list[str]:
    if not values:
        return list(DEFAULT_SEEDS)
    seeds: list[str] = []
    for value in values:
        if value.startswith("http://") or value.startswith("https://"):
            seeds.append(value.strip())
            continue
        candidate = Path(value)
        if candidate.exists():
            for line in candidate.read_text(encoding="utf-8").splitlines():
                row = line.strip()
                if row and not row.startswith("#"):
                    seeds.append(row)
    return seeds or list(DEFAULT_SEEDS)


def main() -> None:
    parser = argparse.ArgumentParser(description="Crawler clinico polite con checkpoint local")
    parser.add_argument(
        "--seed",
        action="append",
        default=[],
        help=(
            "URL semilla (se puede repetir). Si el valor es ruta a archivo, "
            "se leen URLs por linea."
        ),
    )
    parser.add_argument(
        "--allowed-domains",
        default="",
        help=(
            "CSV de dominios permitidos. Si se omite, usa whitelist clinica del sistema "
            "(CLINICAL_CHAT_WEB_ALLOWED_DOMAINS)."
        ),
    )
    parser.add_argument("--output-dir", default="docs/web_raw", help="Directorio de salida")
    parser.add_argument(
        "--checkpoint-path",
        default="tmp/web_crawl_checkpoint.json",
        help="Ruta de checkpoint para reanudar",
    )
    parser.add_argument("--resume", action="store_true", help="Reanuda desde checkpoint si existe")
    parser.add_argument("--max-pages", type=int, default=120, help="Maximo de paginas a guardar")
    parser.add_argument("--max-depth", type=int, default=2, help="Profundidad maxima")
    parser.add_argument("--workers", type=int, default=6, help="Numero de workers")
    parser.add_argument("--front-queues", type=int, default=4, help="Numero de front queues")
    parser.add_argument(
        "--request-timeout-seconds",
        type=int,
        default=8,
        help="Timeout HTTP por request en segundos",
    )
    parser.add_argument(
        "--politeness-multiplier",
        type=float,
        default=10.0,
        help="Multiplicador de espera por host (recomendado >= 10)",
    )
    parser.add_argument(
        "--min-host-delay-seconds",
        type=float,
        default=0.5,
        help="Delay minimo entre requests al mismo host",
    )
    parser.add_argument(
        "--max-urls-per-host",
        type=int,
        default=80,
        help="Limite de URLs en frontier por host",
    )
    parser.add_argument(
        "--max-pages-per-host",
        type=int,
        default=40,
        help="Limite de paginas guardadas por host",
    )
    parser.add_argument(
        "--near-duplicate-threshold",
        type=float,
        default=0.90,
        help="Umbral de near-duplicate por MinHash [0..1]",
    )
    parser.add_argument(
        "--checkpoint-every-pages",
        type=int,
        default=10,
        help="Frecuencia de checkpoint en paginas guardadas",
    )
    parser.add_argument(
        "--disable-robots",
        action="store_true",
        help="Desactiva robots.txt (no recomendado)",
    )

    args = parser.parse_args()
    seeds = _parse_seeds(args.seed)
    cli_domains = _parse_csv_domains(args.allowed_domains)
    allowed_domains = cli_domains or KnowledgeSourceService.get_allowed_domains()

    config = WebCrawlerConfig(
        seeds=seeds,
        output_dir=args.output_dir,
        checkpoint_path=args.checkpoint_path,
        resume_from_checkpoint=args.resume,
        allowed_domains=allowed_domains,
        max_pages=max(1, args.max_pages),
        max_depth=max(0, args.max_depth),
        workers=max(1, args.workers),
        front_queues=max(1, args.front_queues),
        request_timeout_seconds=max(2, args.request_timeout_seconds),
        politeness_multiplier=max(1.0, args.politeness_multiplier),
        min_host_delay_seconds=max(0.0, args.min_host_delay_seconds),
        max_urls_per_host=max(1, args.max_urls_per_host),
        max_pages_per_host=max(1, args.max_pages_per_host),
        near_duplicate_threshold=min(max(args.near_duplicate_threshold, 0.5), 0.99),
        checkpoint_every_pages=max(1, args.checkpoint_every_pages),
        enable_robots=not args.disable_robots,
    )
    crawler = WebCrawlerService(config=config)
    summary = crawler.run()
    print(json.dumps(summary.__dict__, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

