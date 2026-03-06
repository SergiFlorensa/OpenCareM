# 94. Chat Clinico Operativo: Ollama local, trazabilidad y seguridad (runbook interno)

## Objetivo

Operar chat clinico con modelo local (Ollama) en modo open source, con
trazabilidad por turno, guardas de seguridad y fallback operativo.

## Alcance oficial de este runbook

Incluido:

- Motor local OSS para chat (`Ollama`) en infraestructura propia.
- Logica de agentes, trazas operativas y metricas de calidad.
- Automatizacion de calidad en repositorio (hooks, checks, tests).

Excluido (no aplicar en este proyecto):

- Suscripciones, billing por token o pasarelas de pago.
- Apps moviles nativas.
- Integraciones de mensajeria externa (Telegram, WhatsApp, Signal, Discord).

## Configuracion recomendada (`.env`)

```env
CLINICAL_CHAT_LLM_ENABLED=true
CLINICAL_CHAT_LLM_PROVIDER=ollama
CLINICAL_CHAT_LLM_BASE_URL=http://127.0.0.1:11434
CLINICAL_CHAT_LLM_MODEL=llama3.2:3b
CLINICAL_CHAT_LLM_NUM_CTX=1024
CLINICAL_CHAT_LLM_MAX_INPUT_TOKENS=640
CLINICAL_CHAT_LLM_PROMPT_MARGIN_TOKENS=256
CLINICAL_CHAT_LLM_TEMPERATURE=0.2
CLINICAL_CHAT_LLM_TOP_P=0.9
CLINICAL_CHAT_LLM_TIMEOUT_SECONDS=40
CLINICAL_CHAT_LLM_MAX_OUTPUT_TOKENS=220
CLINICAL_CHAT_RAG_ENABLED=true
CLINICAL_CHAT_RAG_RETRIEVER_BACKEND=chroma
CLINICAL_CHAT_RAG_MAX_CHUNKS=3
CLINICAL_CHAT_PDF_PARSER_BACKEND=mineru
CLINICAL_CHAT_PDF_MINERU_TRANSPORT=cli
CLINICAL_CHAT_PDF_MINERU_CLI_COMMAND=mineru
CLINICAL_CHAT_PDF_MINERU_CLI_METHOD=txt
CLINICAL_CHAT_PDF_MINERU_CLI_BACKEND=pipeline
CLINICAL_CHAT_PDF_MINERU_DEVICE=cpu
CLINICAL_CHAT_PDF_MINERU_PARSE_FORMULAS=false
CLINICAL_CHAT_PDF_MINERU_PARSE_TABLES=true
CLINICAL_CHAT_PDF_MINERU_TIMEOUT_SECONDS=900
CLINICAL_CHAT_PDF_MINERU_FAIL_OPEN=true
CLINICAL_CHAT_GUARDRAILS_ENABLED=false
```

## Instalacion local de Ollama

1. Instalar Ollama segun SO desde documentacion oficial.
2. Levantar servicio local: `ollama serve`.
3. Descargar modelo recomendado para 16GB RAM: `ollama pull llama3.2:3b`.
4. Verificar modelo disponible: `ollama list`.

Recomendacion operativa: con 16GB RAM evitar modelos mayores de 14B para no
degradar latencia durante guardia.

## Instalacion local de MinerU (OSS, sin coste por token)

Uso previsto en este proyecto:

- Parsing PDF local por CLI (`mineru`) para `docs/pdf_raw`.
- Sin dependencia obligatoria de servicio HTTP aparte.
- Sin billing por token; el coste es solo local (CPU/RAM/disco y descarga de modelos).

Instalacion recomendada en el `venv` del proyecto:

1. `.\venv\Scripts\python.exe -m pip install -U "mineru[all]"`
2. Verificar CLI disponible: `.\venv\Scripts\mineru.exe --help`

Configuracion recomendada:

```env
CLINICAL_CHAT_PDF_PARSER_BACKEND=mineru
CLINICAL_CHAT_PDF_MINERU_TRANSPORT=cli
CLINICAL_CHAT_PDF_MINERU_CLI_COMMAND=mineru
CLINICAL_CHAT_PDF_MINERU_CLI_METHOD=txt
CLINICAL_CHAT_PDF_MINERU_CLI_BACKEND=pipeline
CLINICAL_CHAT_PDF_MINERU_DEVICE=cpu
CLINICAL_CHAT_PDF_MINERU_PARSE_FORMULAS=false
CLINICAL_CHAT_PDF_MINERU_PARSE_TABLES=true
CLINICAL_CHAT_PDF_MINERU_RENDER_TIMEOUT_SECONDS=300
CLINICAL_CHAT_PDF_MINERU_CPU_INTRA_OP_THREADS=2
CLINICAL_CHAT_PDF_MINERU_CPU_INTER_OP_THREADS=1
CLINICAL_CHAT_PDF_MINERU_WINDOWED_ENABLED=true
CLINICAL_CHAT_PDF_MINERU_WINDOW_THRESHOLD_PAGES=24
CLINICAL_CHAT_PDF_MINERU_WINDOW_SIZE_PAGES=12
CLINICAL_CHAT_PDF_MINERU_TIMEOUT_SECONDS=900
CLINICAL_CHAT_PDF_MINERU_FAIL_OPEN=true
CLINICAL_CHAT_PDF_OCR_MODE=region_selective
CLINICAL_CHAT_PDF_LAYOUT_READING_ORDER_ENABLED=true
CLINICAL_CHAT_PDF_FILTER_REPEATED_EDGE_TEXT_ENABLED=true
```

Notas operativas:

- Si `mineru` no esta instalado o falla, el backend degrada a `pypdf` por `fail-open`.
- El parser mantiene compatibilidad con el nombre CLI legacy `magic-pdf` si existiera en el entorno.
- En local CPU se recomienda `CLINICAL_CHAT_PDF_MINERU_CLI_METHOD=txt` para PDFs digitales; si tu corpus tiene escaneados, cambia a `auto` u `ocr`.
- Para corpus clinico local, deja `CLINICAL_CHAT_PDF_MINERU_PARSE_FORMULAS=false` y `CLINICAL_CHAT_PDF_MINERU_PARSE_TABLES=true`: reduce coste y mantiene tablas utiles.
- Para PDFs grandes en CPU, activa ventanas: `CLINICAL_CHAT_PDF_MINERU_WINDOWED_ENABLED=true`; el parser trocea por rangos de pagina (`-s/-e`) y fusiona resultados.
- `CLINICAL_CHAT_PDF_MINERU_CPU_INTRA_OP_THREADS` y `CLINICAL_CHAT_PDF_MINERU_CPU_INTER_OP_THREADS` limitan la contencion del parser con otros procesos locales.
- `CLINICAL_CHAT_PDF_MINERU_RENDER_TIMEOUT_SECONDS` evita que renderizados lentos bloqueen un lote entero.
- El primer arranque de `mineru` puede tardar varios minutos porque descarga modelos locales y algunos PDF densos en CPU superan varios minutos; por eso el timeout recomendado sube a `900s` para ingesta offline.
- Si quieres seguir usando un servicio MinerU aparte, cambia `CLINICAL_CHAT_PDF_MINERU_TRANSPORT=http`.
- MinerU mejora layout/lectura/tablas, pero no sustituye evaluacion offline del corpus ni garantiza precision del 100%.

## Ingesta de corpus clinico (sin ruido operativo)

Comando recomendado (corpus clinico por defecto en `docs/`):

- `python -m app.scripts.ingest_clinical_docs --backfill-specialty`

Opcional (si quieres incluir `agents/shared`, no recomendado para respuestas clinicas):

- `python -m app.scripts.ingest_clinical_docs --include-shared --backfill-specialty`

Notas:

- El script aplica mapeo de especialidad por defecto para `docs/45_*` a `docs/86_*`.
- El flag `--backfill-specialty` rellena `specialty` en documentos/chunks ya existentes.

## Flujo de inferencia

- Endpoint preferido: `POST /api/chat`.
- Fallback automatico: `POST /api/generate`.
- Si el LLM falla o hace timeout, el sistema devuelve fallback operativo no
  diagnostico con prioridades, riesgos, checklist y advertencia de validacion
  humana.

## Trazabilidad clinica visible

Cada respuesta debe exponer en `interpretability_trace`:

- `llm_used`
- `llm_model`
- `llm_endpoint`
- `llm_latency_ms`
- `query_expanded`
- `matched_endpoints`
- `llm_input_tokens_budget`
- `llm_input_tokens_estimated`
- `llm_prompt_truncated`
- `llm_rewrite_status`
- `prompt_injection_detected`
- `quality_status`

## Politica web/RAG y whitelist

- Mantener `CLINICAL_CHAT_WEB_STRICT_WHITELIST=true`.
- Solo usar dominios permitidos en `CLINICAL_CHAT_WEB_ALLOWED_DOMAINS`.
- Si no hay politica valida de seguridad clinica, no activar RAG web en
  produccion.
- Toda fuente web devuelta debe incluir `url` y `snippet`.

## Flujo operativo del equipo (scripts internos)

Base de comandos adaptada al repo:

- `powershell -ExecutionPolicy Bypass -File scripts/dev_workflow.ps1 -Action dev`
- `powershell -ExecutionPolicy Bypass -File scripts/dev_workflow.ps1 -Action build`
- `powershell -ExecutionPolicy Bypass -File scripts/dev_workflow.ps1 -Action check`
- `powershell -ExecutionPolicy Bypass -File scripts/dev_workflow.ps1 -Action test`
- `powershell -ExecutionPolicy Bypass -File scripts/dev_workflow.ps1 -Action test-e2e`

Setup de hooks para staged files:

- `powershell -ExecutionPolicy Bypass -File scripts/setup_hooks.ps1`
- Hooks definidos en `.pre-commit-config.yaml` (`ruff --fix`, `black`, verificacion `ruff`).

## Ejemplos de prompts clinicos

- "Paciente con sepsis y lactato 4, prioriza acciones 0-10 minutos."
- "resume"
- "y ahora?"
- "que hago si persiste hipotension?"

## Interrogatorio activo opcional (Bayes + DEIG)

El endpoint de chat permite activar un turno de aclaracion previa cuando faltan
datos clinicos:

- `enable_active_interrogation`: `true|false` (default `false`)
- `interrogation_max_turns`: `1..10` (default `3`)
- `interrogation_confidence_threshold`: `0.5..0.99` (default `0.93`)

Ejemplo de uso en request JSON:

- `"enable_active_interrogation": true`
- `"interrogation_max_turns": 3`
- `"interrogation_confidence_threshold": 0.95`

Trazas esperadas:

- `interrogatory_enabled`
- `interrogatory_active`
- `interrogatory_reason`
- `interrogatory_domain` (si aplica)
- `deig_score` (si aplica)

## Ejecucion de pruebas

- Backend lint:
  - `python -m ruff check app/services/clinical_chat_service.py app/services/llm_chat_provider.py app/tests/test_clinical_chat_operational.py`
- Tests chat:
  - `python -m pytest -q app/tests/test_clinical_chat_operational.py`
- Frontend build:
  - `cd frontend && npm run build`

## Riesgos pendientes

- Las metricas de calidad son heuristicas y requieren calibracion continua.
- El rendimiento final depende del modelo local y del hardware.
- Los hooks mejoran higiene, pero no sustituyen revisiones clinicas ni de seguridad.

