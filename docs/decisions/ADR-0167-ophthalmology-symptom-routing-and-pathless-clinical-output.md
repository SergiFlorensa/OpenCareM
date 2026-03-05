# ADR-0167: Ophthalmology Symptom Routing + Pathless Clinical Output

## Status

Accepted (2026-03-05)

## Context

Clinical queries with ocular symptoms (for example, "dolor en ojo derecho") were drifting to generic domains (`critical_ops`) instead of `ophthalmology`.

Additionally, some responses exposed internal repository/endpoint locators in user-facing text (`docs/...`, `/api/v1/...`, file leaf names), which degrades UX and perceived grounding quality.

## Decision

1. Extend ophthalmology routing signals in `ClinicalChatService`:

- Domain keywords and specialty hints now include ocular symptom patterns such as:
  - `dolor ocular`,
  - `dolor de ojo`,
  - `dolor en el ojo`,
  - `ojo derecho`,
  - `ojo izquierdo`,
  - `vision borrosa`,
  - `disminucion visual`,
  - `cuerpo extrano ocular`.

2. Remove internal path exposure from rendered answers:

- In clinical/general renderers, show human-readable source labels only.
- Hide endpoint locators from response text.
- Sanitize snippets to remove path-like artifacts.
- In extractive RAG source anchors, keep section/title references without filename leaf suffixes.

3. Exclude `docs/decisions/` as clinical source locator in chat response assembly.

## Consequences

### Positive

- Better specialty routing for ophthalmology in natural language symptom queries.
- Cleaner, clinician-facing responses with grounded references but without technical repository noise.

### Trade-offs / Risks

- Ocular lexical expansion may introduce occasional false positives in non-clinical uses of "ojo"; requires regression monitoring.

## Validation

- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -o addopts=""`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py -o addopts=""`
- `.\venv\Scripts\python.exe -m ruff check app/services/clinical_chat_service.py app/services/rag_orchestrator.py app/tests/test_clinical_chat_operational.py app/tests/test_rag_orchestrator_optimizations.py`
