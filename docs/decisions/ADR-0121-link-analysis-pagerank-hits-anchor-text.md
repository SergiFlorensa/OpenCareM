# ADR-0121: Link Analysis para Ranking de Fuentes Web (Anchor Text + PageRank + HITS)

## Estado
Aprobado

## Contexto
El chat clinico ya aplicaba filtrado de spam/duplicados y un score heuristico de autoridad+relevancia para `web_sources` (TM-164). Faltaba incorporar senales de grafo para distinguir mejor fuentes autoritativas y mejorar trazabilidad en consultas amplias:

- PageRank global,
- PageRank especifico de tema clinico,
- HITS (hubs/authorities),
- uso del anchor text entrante como senal semantica adicional.

## Decision
Se implementa una capa de analisis de enlaces local con artefacto offline:

1. Nuevo servicio `WebLinkAnalysisService`:
   - construccion de snapshot desde `crawl_manifest.jsonl`,
   - calculo de PageRank global por iteracion de potencia,
   - calculo de Topic-Specific PageRank con personalizacion en dominios confiables,
   - calculo de HITS global y HITS de base-set orientado a consulta,
   - agregacion de terminos de anchor text por URL destino.
2. Nuevo script `python -m app.scripts.build_web_link_analysis` para generar:
   - `docs/web_raw/link_analysis_snapshot.json`.
3. Enriquecimiento del crawler (`WebCrawlerService`) para persistir en manifiesto:
   - `outgoing_links`,
   - `outgoing_anchor_texts`,
   - `outgoing_edges` (url+anchor).
4. Integracion en `ClinicalChatService`:
   - blend configurable entre `quality_score` base y `link_score`,
   - trazas `web_search_link_analysis_*` en `interpretability_trace`.

## Consecuencias

### Positivas
- Ranking web con autoridad basada en estructura de enlaces y no solo heuristica de dominio.
- Mejor cobertura semantica via anchor text entrante.
- Mayor auditabilidad del pipeline web por trazas explicitas de link-analysis.

### Costes
- Nuevo artefacto operativo (snapshot) a regenerar tras recrawls.
- Mayor complejidad en pipeline web (componente offline + cache runtime).

## Validacion
- `./venv/Scripts/python.exe -m ruff check app/services/web_link_analysis_service.py app/services/web_crawler_service.py app/services/clinical_chat_service.py app/scripts/build_web_link_analysis.py app/tests/test_web_link_analysis_service.py app/tests/test_web_crawler_service.py app/tests/test_clinical_chat_operational.py app/tests/test_settings_security.py app/core/config.py app/services/__init__.py`
- `./venv/Scripts/python.exe -m pytest -q app/tests/test_web_link_analysis_service.py -o addopts=""`
- `./venv/Scripts/python.exe -m pytest -q app/tests/test_web_crawler_service.py -o addopts=""`
- `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "web_source_quality" -o addopts=""`
- `./venv/Scripts/python.exe -m pytest -q app/tests/test_settings_security.py -k "web_link_analysis" -o addopts=""`
- `./venv/Scripts/python.exe -m app.scripts.build_web_link_analysis --help`

## Riesgos pendientes
- HITS orientado a consulta opera sobre base-set acotado (heuristico) y no sobre grafo completo.
- El snapshot puede quedar desactualizado si no se recompone tras nuevos crawls.
- La calidad de `anchor_relevance` depende de densidad/calidad de anchors en el corpus crawleado.
