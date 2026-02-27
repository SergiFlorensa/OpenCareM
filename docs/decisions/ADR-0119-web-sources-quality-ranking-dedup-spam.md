# ADR-0119: Calidad de Web Sources con Deduplicacion, Anti-Spam y Ranking de Autoridad

## Estado
Aprobado

## Contexto
El chat clinico ya permitia fuentes web en dominios de whitelist, pero quedaban tres huecos operativos:

- duplicados y casi-duplicados en snippets,
- ruido por resultados tipo spam/clickbait dentro de dominios permitidos,
- ausencia de ordenacion explicita por autoridad/relevancia en `web_sources`.

Esto afectaba fidelidad y latencia perceptual al consumir evidencia web en modo `deep_search`.

## Decision
Se integra un pipeline de calidad en `ClinicalChatService._fetch_web_sources` con estas capas:

1. Canonizacion de URL para deduplicacion basica (`scheme+host+path`).
2. Deteccion near-duplicate usando shingles de palabras + firma MinHash.
3. Filtro heuristico anti-spam basado en titulo/snippet/url.
4. Scoring y ordenacion por:
   - autoridad de dominio (prior de dominios clinicos),
   - relevancia lexical de consulta (overlap sobre titulo/snippet).
5. Trazabilidad en `interpretability_trace` con claves `web_search_*`.

## Consecuencias

### Positivas
- Mejora de precision de `web_sources` sin cambiar contrato HTTP.
- Menos redundancia de evidencia en respuestas.
- Mejor auditabilidad de decisiones de filtrado/ranking web.

### Costes
- Aumento leve de CPU en fase de post-procesado web.
- Heuristicas requieren calibracion periodica.

## Validacion
- `./venv/Scripts/python.exe -m ruff check app/services/clinical_chat_service.py app/tests/test_clinical_chat_operational.py`
- `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "web_source_quality_filter or fetch_web_sources_returns_error_trace_when_request_fails" -o addopts=""`
- `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "test_chat_e2e_uses_rag_when_enabled" -o addopts=""`

## Riesgos pendientes
- La autoridad de dominio es un prior local, no una señal de grafo web global.
- Cloaking no se detecta de forma robusta sin fetch/render de pagina final.
- Umbrales de spam/near-duplicate pueden necesitar ajuste por telemetria real.
