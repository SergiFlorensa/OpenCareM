# ADR-0177: Chunking por seccion y compresion extractiva de contexto antes del LLM

## Estado

Aceptado

## Contexto

El cuello de botella principal del chat clinico local ya no estaba solo en el transporte a Ollama, sino en la calidad y volumen de la informacion que llegaba al modelo:

- los chunks heredados podian mezclar contenido de varias secciones o perder contexto al recuperarse aislados
- el LLM recibia fragmentos demasiado crudos, con ruido suficiente para degradar calidad y latencia en CPU local
- en consultas clinicas genericas, el sistema seguia necesitando reducir tokens sin vaciar por completo la evidencia util

La arquitectura anterior comprimía por solape de consulta, pero seguia trabajando sobre chunks con semantica demasiado plana.

## Decision

Se adopta una arquitectura intermedia en dos capas antes del LLM:

1. **Chunking estructurado por seccion en ingesta**
   - el chunker respeta fronteras de seccion cuando la estructura fuente esta disponible
   - se evita arrastrar overlap entre secciones distintas
   - los nuevos chunks pueden incluir decontextualizacion breve (`Documento`, `Seccion`, `Contenido`) para preservar significado al recuperarse fuera de su documento

2. **Compresion extractiva por oracion en ensamblado RAG**
   - el ensamblador divide cada chunk recuperado en oraciones
   - puntua cada oracion frente a la consulta
   - selecciona un maximo configurable por chunk y un maximo global
   - recompone el contexto en el orden original del documento
   - si la relevancia total cae por debajo del umbral, puede devolver contexto vacio en lugar de enviar ruido al LLM

## Consecuencias

### Positivas

- El LLM recibe menos texto y mas evidencia util.
- Se reduce la dependencia de prompts clinicos largos para reconstruir contexto perdido.
- La ingesta queda mas preparada para corpus PDF complejos extraidos por MinerU.
- Se facilita una evolucion posterior hacia rerankers/compresores mas sofisticados sin cambiar el contrato principal del chat.

### Limitaciones

- La decontextualizacion aumenta el texto bruto almacenado por chunk nuevo.
- La compresion extractiva actual es heuristica; no sustituye un reranker neuronal cuando el hardware lo permita.
- El beneficio completo exige reingestar progresivamente los documentos que sigan indexados con chunks antiguos.

## Validacion

- `pytest -q app/tests/test_chunking.py app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py -o addopts=""`
- `pytest -q app/tests/test_document_ingestion_service.py app/tests/test_ingest_clinical_docs_script.py -o addopts=""`
- `ruff check app/core/chunking.py app/core/config.py app/services/document_ingestion_service.py app/services/rag_prompt_builder.py app/services/rag_orchestrator.py app/tests/test_chunking.py app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py`

## Riesgos pendientes

- Conviene medir por especialidad si el umbral de compresion vacia demasiado contexto en consultas con sinonimia alta.
- Algunos documentos pueden requerir ajustar longitud maxima del prefijo de decontextualizacion para no sobredimensionar embeddings.
- La reingesta parcial puede coexistir temporalmente con corpus antiguo y nuevo; hay que hacerlo por lotes controlados.
