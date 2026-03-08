# ADR-0178: Context packs vecinos por documento antes del LLM

## Estado

Aceptado

## Contexto

Tras introducir chunking por seccion y compresion extractiva, seguia faltando una pieza para reducir fragmentacion semantica:

- un chunk aislado puede ser correcto, pero insuficiente para responder con coherencia
- recuperar demasiados chunks crudos vuelve a inflar el contexto y reintroduce ruido
- materializar una jerarquia `parent-child` completa en base de datos seria mas costoso y arriesgado en esta fase

Necesitabamos una capa intermedia, ligera y reversible, que diese al compresor un bloque algo mas estable sin tocar el schema.

## Decision

Se adopta una expansion en runtime de `context packs` antes de `assemble_rag_context`:

1. Cada chunk recuperado puede ampliarse con vecinos del mismo documento usando `chunk_index +/- radius`.
2. El radio queda limitado por configuracion (`CLINICAL_CHAT_RAG_CONTEXT_PACK_RADIUS`) y acotado a `0..3`.
3. Si dos semillas generan la misma ventana, la segunda se deduplica.
4. El pack resultante se entrega al ensamblador y al compresor extractivo como una unidad temporal.

## Consecuencias

### Positivas

- Se reduce la probabilidad de que el LLM vea frases demasiado huérfanas.
- El compresor trabaja sobre bloques mas coherentes y cercanos a una `emulated page`.
- No se requieren migraciones ni nuevos nodos persistidos.
- La estrategia es barata para CPU local porque actua sobre pocas ventanas y despues vuelve a comprimir.

### Limitaciones

- Depende de que `chunk_index` refleje orden documental fiable.
- No sustituye una jerarquia persistida si en el futuro se quiere `parent-child retrieval` real.
- Si el radio sube demasiado, el contexto previo a compresion crece y puede penalizar latencia.

## Validacion

- `pytest -q app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py -o addopts=""`
- `ruff check app/core/config.py app/services/rag_orchestrator.py app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py`

## Riesgos pendientes

- Conviene validar con corpus PDF complejos si algunos documentos tienen `chunk_index` correcto pero secciones adyacentes semantica y clinicamente pobres.
- El ajuste por defecto (`radius=1`) es conservador; subirlo requiere medicion real de latencia y calidad.
