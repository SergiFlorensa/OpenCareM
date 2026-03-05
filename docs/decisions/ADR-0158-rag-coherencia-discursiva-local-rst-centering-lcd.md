# ADR-0158: Coherencia Discursiva Local en RAG (RST Heuristico, Centering y LCD)

## Estado

Aprobado

## Contexto

Aunque el retrieval RAG ya tenia verificacion y filtros de ruido, seguian apareciendo
respuestas con fragmentos correctos pero poco cohesionados (mezcla de contexto editorial
con pasos operativos). En entorno offline se necesitaba mejorar coherencia sin depender de
modelos grandes adicionales.

## Decision

1. Incorporar un reranking discursivo ligero sobre chunks verificados:
   - clasificacion heuristica `nucleus/satellite` inspirada en RST;
   - inferencia de zona argumentativa (`aim|method|result|none`);
   - puntuacion claim/premise por marcadores lexicales.
2. Aplicar foco por entidad saliente (centering):
   - extraccion de entidades clave de la consulta;
   - puntuacion de continuidad de entidad por chunk.
3. Incorporar cohesion lexical y LCD local:
   - cohesion por solape/recurrencia de terminos;
   - discriminador de coherencia entre oraciones consecutivas;
   - penalizacion de orden no natural (inicio con conectores anaforicos).
4. Exponer control por configuracion:
   - `CLINICAL_CHAT_RAG_DISCOURSE_COHERENCE_ENABLED`
   - `CLINICAL_CHAT_RAG_DISCOURSE_MIN_SCORE`
   - `CLINICAL_CHAT_RAG_DISCOURSE_MAX_SATELLITE_RATIO`
   - `CLINICAL_CHAT_RAG_DISCOURSE_LCD_MIN_SCORE`

## Consecuencias

- Mayor probabilidad de seleccionar fragmentos operativos coherentes.
- Menor entrada de texto satelite/editorial al ensamblado final.
- Sin cambios de schema API ni de base de datos.
- Requiere calibracion por subdominio para evitar perdida de recall en textos breves.

## Validacion

- `./venv/Scripts/python.exe -m ruff check app/core/config.py app/services/rag_orchestrator.py app/services/clinical_chat_service.py app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py`
- `$env:DEBUG='false'; ./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py -o addopts=""`
- Resultado: `135 passed`.

## Riesgos pendientes

- El etiquetado RST/argumentativo es heuristico, no parser discursivo entrenado.
- En documentos muy cortos, LCD puede ser poco discriminativo y depender mas del retrieval base.
