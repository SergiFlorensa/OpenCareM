# ADR-0100: Candidate Retrieval con Indice Invertido (FTS5) y Postings Booleanos

- Fecha: 2026-02-24
- Estado: Aprobado

## Contexto

El retrieval hibrido actual hacia `DocumentChunk` hacia escaneo amplio de corpus
(`.all()`), penalizando latencia y escalabilidad en CPU local.

Se requiere aplicar principios de IR clasico (indice invertido + postings) sin
costes externos y sin romper contrato de API.

## Decision

Se incorpora en `HybridRetriever` una fase de candidate generation basada en:

- indice invertido FTS5 local sobre `document_chunks` (`document_chunks_fts`);
- postings por termino con listas ordenadas por `chunk_id`;
- interseccion lineal (merge O(x+y)) para terminos `AND`;
- union/diferencia para `OR/NOT` basicos;
- heuristica de orden por menor DF (listas mas cortas primero).

Detalles de implementacion:

- bootstrap lazy/best-effort del indice FTS y triggers de sincronizacion;
- fallback automatico a escaneo completo cuando FTS no esta disponible;
- nuevos flags de runtime:
  - `CLINICAL_CHAT_RAG_FTS_CANDIDATE_ENABLED`
  - `CLINICAL_CHAT_RAG_FTS_CANDIDATE_POOL`

## Consecuencias

### Positivas

- menor pool de candidatos para scoring vectorial/lexical;
- mejor latencia media de retrieval en corpus creciente;
- trazabilidad explicita del camino de candidate selection.

### Riesgos

- dependencia de soporte FTS5 en build SQLite local;
- parser booleano simplificado (sin precedencia completa con parentesis).

## Validacion

- `.\venv\Scripts\python.exe -m ruff check app/services/rag_retriever.py app/core/config.py app/tests/test_rag_retriever.py app/tests/test_settings_security.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_rag_retriever.py app/tests/test_settings_security.py -o addopts=""`
