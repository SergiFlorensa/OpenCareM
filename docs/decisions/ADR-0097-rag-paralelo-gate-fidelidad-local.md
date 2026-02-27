# ADR-0097: RAG Paralelo y Gate de Fidelidad Minima en Chat Clinico Local

- Fecha: 2026-02-23
- Estado: Aprobado

## Contexto

El chat clinico local mantenia latencias altas y respuestas de baja utilidad
cuando el LLM caia en timeout o devolvia texto generico. Aunque el pipeline RAG
recuperaba evidencia, faltaban dos mecanismos para robustez operativa:

- paralelizar scoring vectorial y keyword para reducir tiempo de retrieval hibrido;
- bloquear respuestas con soporte insuficiente respecto a chunks recuperados.

## Decision

Se implementa en runtime local:

- retrieval hibrido paralelo opcional con `ThreadPoolExecutor` en
  `RAGRetriever.search_hybrid` controlado por
  `CLINICAL_CHAT_RAG_PARALLEL_HYBRID_ENABLED`;
- gate de fidelidad minima en `BasicGatekeeper` con score de soporte lexical
  configurable por `CLINICAL_CHAT_RAG_FAITHFULNESS_MIN_RATIO`;
- trazabilidad de paralelismo en `interpretability_trace` con
  `hybrid_parallelized=1|0`.

Adicionalmente se calibra preset local en `.env/.env.example` para reducir
timeouts y acotar coste de generacion.

## Consecuencias

### Positivas

- Menor latencia de retrieval hibrido en escenarios con corpus no trivial.
- Menos respuestas no soportadas por evidencia interna.
- Mejor observabilidad para tuning de rendimiento/calidad.

### Riesgos

- El score de fidelidad por solape de tokens puede penalizar parafrasis validas.
- En corpus muy pequenos, el paralelismo puede aportar ganancia marginal.

## Validacion

- `.\venv\Scripts\python.exe -m ruff check app/core/config.py app/services/rag_gatekeeper.py app/services/rag_retriever.py app/tests/test_clinical_chat_operational.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "gatekeeper_flags_low_faithfulness_as_risk or uses_rag_when_enabled"`
