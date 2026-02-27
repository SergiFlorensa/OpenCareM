# ADR-0137: Modo RAG Extractivo Forzado + Relajacion de Filtro de Especialidad

## Estado
Aceptado

## Contexto
El stack local en CPU presenta variabilidad de latencia y fallos de inferencia LLM (`TimeoutError`, `BudgetExhausted`) que degradan el chat en frontend.
Ademas, parte de los `failed_retrieval` ocurre cuando el filtro `specialty` es demasiado estricto para la evidencia disponible.

## Decision
1. Introducir `CLINICAL_CHAT_RAG_FORCE_EXTRACTIVE_ONLY` para omitir generacion LLM en la ruta clinica RAG sincrona.
2. Mantener salida evidence-first extractiva cuando hay chunks.
3. En retrieval, si la busqueda con `specialty_filter` retorna vacio, ejecutar un reintento con backend legacy sin filtro de especialidad (una sola vez).
4. Trazar explicitamente el comportamiento con claves `rag_force_extractive_only`, `rag_llm_skipped_reason`, `rag_retriever_specialty_relaxation*`.

## Consecuencias
### Positivas
- Menor dependencia de inferencia LLM local inestable.
- Menor probabilidad de timeout en request sincrona.
- Menor tasa de `failed_retrieval` por sobre-filtrado de especialidad.
- Mayor auditabilidad operacional en `interpretability_trace`.

### Negativas
- Menor fluidez conversacional comparado con salida generativa.
- Puede aumentar respuestas conservadoras si la evidencia recuperada es limitada.

## Alternativas consideradas
- Mantener flujo actual con tuning incremental del LLM local: no eliminaba la variabilidad de forma fiable.
- Migrar a infraestructura GPU/servicios pagos: descartado por restriccion de coste.

## Validacion
- `./venv/Scripts/python.exe -m ruff check app/core/config.py app/services/rag_orchestrator.py app/services/clinical_chat_service.py app/tests/test_rag_orchestrator_optimizations.py app/tests/test_clinical_chat_operational.py`
- `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py -o addopts=""`
- `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "force_extractive_only or rag_failed_retrieval or rag_failed_generation" -o addopts=""`
