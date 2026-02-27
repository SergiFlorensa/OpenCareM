# ADR-0120: Crawler Web Clinico Polite con Frontier Priorizada y Checkpoint

## Estado
Aprobado

## Contexto
Para mantener frescura del conocimiento clinico sin depender de proveedores de pago, el sistema necesitaba un crawler local que:

- priorice fuentes de alta autoridad,
- respete cortesia por host y `robots.txt`,
- evite duplicados masivos,
- pueda reanudarse tras fallos.

## Decision
Se implementa `WebCrawlerService` + script `crawl_clinical_web` con arquitectura single-node:

1. Seeds iniciales + URL frontier de prioridad (front queues).
2. Back queues por host con invariante de una conexion activa por host.
3. Politica de cortesia: espera minima + multiplicador del tiempo de fetch previo.
4. `robots.txt` por host con cache TTL.
5. Normalizacion canonica de URL y deduplicacion.
6. Deteccion near-duplicate de contenido por shingles + MinHash.
7. Checkpoint JSON de estado (`frontier`, colas host, seen urls, firmas) para resume.
8. Persistencia a markdown por host en `docs/web_raw/` + `crawl_manifest.jsonl`.

## Consecuencias

### Positivas
- Base reproducible de crawling etico para alimentar RAG.
- Reanudacion operativa tras caidas sin perder frontier.
- Reduccion de ruido por contenido duplicado.

### Costes
- Arquitectura single-node (no distribuida).
- Heuristicas de spider-trap aun basicas.

## Validacion
- `./venv/Scripts/python.exe -m ruff check app/services/web_crawler_service.py app/scripts/crawl_clinical_web.py app/tests/test_web_crawler_service.py app/services/__init__.py`
- `./venv/Scripts/python.exe -m pytest -q app/tests/test_web_crawler_service.py -o addopts=""`
- `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "test_chat_e2e_uses_rag_when_enabled" -o addopts=""`

## Riesgos pendientes
- Falta particion distribuida por documentos para escala multi-nodo.
- Falta hardening avanzado de spider-traps dinamicas (patrones infinitos).
- Falta modulo de recrawl incremental por tasa de cambio estimada por host/path.
