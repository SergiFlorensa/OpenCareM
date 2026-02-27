import json
from types import SimpleNamespace

from app.scripts.sync_chunks_to_elastic import _build_bulk_payload


def test_build_bulk_payload_contains_expected_fields():
    chunk = SimpleNamespace(
        id=10,
        document_id=5,
        chunk_index=0,
        chunk_text="Texto clinico de prueba.",
        section_path="Seccion > Prueba",
        specialty="critical_ops",
        tokens_count=4,
        keywords=["sepsis", "shock"],
        custom_questions=["Que hacer en shock septico?"],
        document=SimpleNamespace(source_file="docs/47_motor_sepsis_urgencias.md"),
    )

    payload = _build_bulk_payload([chunk], index_name="clinical_chunks")
    lines = [line for line in payload.strip().splitlines() if line.strip()]
    assert len(lines) == 2

    action = json.loads(lines[0])
    doc = json.loads(lines[1])

    assert action["index"]["_index"] == "clinical_chunks"
    assert action["index"]["_id"] == "10"
    assert doc["chunk_id"] == 10
    assert doc["source_file"] == "docs/47_motor_sepsis_urgencias.md"
    assert doc["keywords_text"] == "sepsis shock"
    assert "shock septico" in doc["custom_questions_text"].lower()
