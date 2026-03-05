# ADR-0156: Verificador de Evidencia, ECoRAG Iterativo y Citas Granulares

## Estado

Aprobado

## Contexto

Tras introducir segmentacion multi-intento, persistian dos riesgos operativos:

- fragmentos recuperados con relevancia superficial que degradaban la accionabilidad;
- composicion de contexto con longitud fija, sin criterio explicito de suficiencia evidencial.

Ademas, se necesitaba reforzar grounding con citas mas precisas sin abrir cambios de
esquema en base de datos.

## Decision

1. Agregar una etapa de verificacion posterior a retrieval:
   - score `cross-encoder proxy` sobre query/chunk;
   - umbral configurable (`CLINICAL_CHAT_RAG_VERIFIER_MIN_SCORE`);
   - minimo de fragmentos verificados configurable (`CLINICAL_CHAT_RAG_VERIFIER_MIN_CHUNKS`).
2. Si la verificacion falla, intentar recuperacion lexical (`keyword_only`) antes de abstener.
3. Si sigue faltando evidencia verificada:
   - activar safe-wrapper de abstencion cuando esta habilitado;
   - en modo sin safe-wrapper, usar best-effort para no bloquear flujo legacy.
4. Aplicar reflexion iterativa de evidencialidad (ECoRAG-like) sobre chunks:
   - seleccion incremental hasta alcanzar umbral de suficiencia;
   - backfill minimo para no dejar contexto vacio.
5. Enriquecer chunks ensamblados con metadatos de cita:
   - `source_title` y `source_page` (derivado por parseo de seccion);
   - render final anclado a `titulo + seccion + pagina + source`.

## Consecuencias

- Menor paso de ruido a generacion y mayor control de alucinacion por falta de evidencia.
- Mejor trazabilidad en auditoria via `rag_verifier_*` y `rag_ecorag_*`.
- Citas mas granulares sin migraciones DB.
- Mayor necesidad de calibrar umbrales para evitar perdida de recall en consultas cortas.

## Validacion

- `./venv/Scripts/python.exe -m ruff check app/services/rag_orchestrator.py app/services/rag_prompt_builder.py app/core/config.py app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py`
- `$env:DEBUG='false'; ./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py -o addopts=""`
- Resultado: `122 passed`.

## Riesgos pendientes

- El score proxy no reemplaza un cross-encoder neuronal entrenado; requiere calibracion continua.
- Extraccion de pagina por regex depende del formato textual de `section_path`.
