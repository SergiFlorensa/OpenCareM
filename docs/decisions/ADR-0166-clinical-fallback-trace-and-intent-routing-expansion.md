# ADR-0166: Clinical Fallback Trace + Intent Routing Expansion

## Status

Accepted (2026-03-05)

## Context

In TM-211, clinical chat showed inconsistent interpretability traces in some fallback paths:

- Responses were downgraded to structured clinical output, but no explicit quality-gate trace was emitted.
- This broke automated QA expectations and reduced observability for root-cause analysis.

Also, intent routing needed broader lexical coverage for common clinician asks (drugs, steps, referrals, follow-up, similar cases).

## Decision

1. Add explicit trace emission in structured clinical fallback branch:

- `clinical_answer_quality_gate=final_structured_fallback`

This trace is emitted in strict pipeline mode when the final answer is rendered by the structured clinical fallback path and the trace is not already present.

2. Expand RAG query intent markers in `RAGOrchestrator`:

- Pharmacology: add `farmacologia`, `tratamiento(s)`, `interacciones`, `contraindicaciones`.
- Steps/actions: add `recomendacion`, `recomendar`, `proponer`.
- Referral: add `remitir`.
- Follow-up: add `plan de control`.
- Similar cases: add `valorar otros casos`, `casos de referencia`.

## Consequences

### Positive

- QA and observability now see consistent fallback trace in strict clinical flows.
- Better routing hints for operational medical queries without changing public API contract.

### Trade-offs / Risks

- More fallback traces may appear in analytics; dashboards should account for this.
- Broader lexical intent matching can increase false positives in ambiguous prompts.

## Validation

- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -o addopts=""`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py -o addopts=""`
- `.\venv\Scripts\python.exe -m ruff check app/services/clinical_chat_service.py app/services/rag_orchestrator.py app/tests/test_clinical_chat_operational.py app/tests/test_rag_orchestrator_optimizations.py`
