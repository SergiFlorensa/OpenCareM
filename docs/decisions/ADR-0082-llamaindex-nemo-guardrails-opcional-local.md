# ADR-0082: Integracion opcional LlamaIndex + Chroma + NeMo Guardrails con fallback local

## Estado

Aprobada

## Contexto

El chat clinico ya dispone de RAG hibrido local y fallback seguro. Se requiere subir
calidad de retrieval y control de salida, manteniendo:

- arquitectura sin servicios de pago,
- ejecucion local con Ollama,
- no ruptura de contrato API ni disponibilidad del sistema.

## Decision

1. Incorporar backend retrieval configurable en runtime:
   - `legacy` (actual),
   - `llamaindex` (opcional),
   - `chroma` (opcional).
2. Incorporar capa opcional de validacion/reescritura de respuesta con NeMo Guardrails.
3. Definir ambos componentes como opt-in con fail-safe:
   - si faltan dependencias o config, el chat cae automaticamente al flujo previo.
4. No introducir cambios de payload ni nuevos endpoints.

## Implementacion

- `app/services/llamaindex_retriever.py`
- `app/services/chroma_retriever.py`
- `app/services/nemo_guardrails_service.py`
- `app/services/rag_orchestrator.py` (selector de backend + fallback a legacy)
- `app/services/clinical_chat_service.py` (aplicacion guardrails post-respuesta)
- flags nuevos en `app/core/config.py` y `.env*`
- dependencias opcionales en `requirements.optional-rag-guardrails.txt`

## Consecuencias

Positivas:

- Retrieval semantico opcional mas robusto en corpus interno.
- Capa adicional de control de salida sin bloquear disponibilidad por defecto.
- Mayor observabilidad via `interpretability_trace`.

Negativas / tradeoffs:

- Mayor complejidad operativa y potencial aumento de latencia.
- Configuracion de guardrails requiere calibracion para evitar sobre-filtrado.

## Validacion

- `ruff check` sobre modulos afectados.
- `pytest -q app/tests/test_settings_security.py`
- `pytest -q app/tests/test_nemo_guardrails_service.py`
- `pytest -q app/tests/test_clinical_chat_operational.py`
- `pytest -q app/tests/test_care_tasks_api.py -k chat`
