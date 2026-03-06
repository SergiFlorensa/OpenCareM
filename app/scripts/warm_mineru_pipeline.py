"""
Warm-up y smoke test local de MinerU para parsing PDF.

Ejecuta el parser configurado sobre un PDF real para:
- descargar modelos en frio si faltan;
- validar que `mineru` CLI es invocable desde el backend;
- imprimir la traza efectiva de parseo.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from app.services.pdf_parser_service import PDFParserService


def main() -> int:
    parser = argparse.ArgumentParser(description="Warm-up local de MinerU")
    parser.add_argument("--pdf", required=True, help="Ruta absoluta o relativa al PDF a probar")
    parser.add_argument(
        "--preview-chars",
        type=int,
        default=400,
        help="Numero de caracteres a mostrar de vista previa",
    )
    args = parser.parse_args()

    pdf_path = Path(args.pdf).expanduser().resolve()
    if not pdf_path.exists():
        print(f"RESULT=FAIL reason=pdf_not_found path={pdf_path}")
        return 1

    result = PDFParserService.parse(pdf_path)
    preview = result.text.replace("\n", " ")[: max(80, int(args.preview_chars))]

    print(f"PDF={pdf_path}")
    for key in sorted(result.trace):
        print(f"{key}={result.trace[key]}")
    print(f"preview={preview}")
    print("RESULT=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
