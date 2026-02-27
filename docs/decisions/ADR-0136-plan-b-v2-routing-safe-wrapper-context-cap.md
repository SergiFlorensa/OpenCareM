# ADR-0136: Plan B v2 - routing determinista, safe-wrapper y cap de contexto LLM

- Fecha: 2026-02-25
- Estado: Aprobada

## Contexto
El stack local CPU presenta degradacion por dos frentes: consultas complejas que consumen retrieval costoso y respuestas LLM con riesgo de baja alineacion cuando la evidencia recuperada es debil.

## Decision
Se aplican tres controles de bajo riesgo y alto impacto operativo:
1. Cap de utilizacion de contexto LLM (`CLINICAL_CHAT_LLM_MAX_CONTEXT_UTILIZATION_RATIO`, default 0.40) para limitar saturacion de ventana y reducir latencia variable.
2. Enrutado determinista de consulta (`simple|medium|complex`) con fast-path para consultas compactas y salto de busqueda por dominio en consultas complejas.
3. Safe-wrapper explicito en RAG cuando la evidencia cae por debajo de umbral de contexto, antes y despues de validacion (solo post-validacion para respuestas generadas por LLM).

## Consecuencias
- Menor variabilidad de latencia en CPU por recorte de fan-out y menor gasto en pasos no rentables.
- Menor riesgo de respuesta no fundamentada al priorizar abstencion segura con trazabilidad.
- Mayor auditabilidad con nuevas trazas: `rag_query_complexity`, `rag_domain_search_skip_reason`, `rag_safe_wrapper_*`, `rag_context_relevance_pre/post`, `rag_faithfulness_post`, `llm_context_utilization_*`.

## Validacion
- `./venv/Scripts/python.exe -m ruff check app/core/config.py app/services/llm_chat_provider.py app/services/rag_gatekeeper.py app/services/rag_orchestrator.py app/tests/test_rag_orchestrator_optimizations.py app/tests/test_clinical_chat_operational.py app/tests/test_settings_security.py`
- `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py app/tests/test_clinical_chat_operational.py app/tests/test_settings_security.py -k "safe_wrapper or deterministic or llm_provider_build_chat_messages_respects_token_budget or invalid_llm_context_utilization_ratio or invalid_simple_route_max_chunks_vs_hard_limit" -o addopts=""`
