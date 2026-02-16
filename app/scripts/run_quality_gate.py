"""Ejecuta el gate de evaluacion continua de calidad IA clinica."""

from __future__ import annotations

import pytest


def main() -> int:
    return pytest.main(
        [
            "-q",
            "app/tests/test_quality_regression_gate.py",
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
