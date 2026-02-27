# ADR-0107: Ranking lexical RAG con tf-idf por zonas, coseno y normalizacion pivotada

- Fecha: 2026-02-24
- Estado: Aprobado

## Contexto

El ranking keyword previo usaba conteos simples de coincidencias, con sensibilidad limitada a estructura documental y sesgo por longitud de chunk.

## Decision

Se reemplaza el scoring keyword por un esquema `tf-idf` con:

1. Ponderacion por zonas configurables:
   - `title`, `section`, `body`, `keywords`, `custom_questions`.
2. `tf` sublineal por zona: `1 + log(tf)`.
3. `idf` suavizado en el pool candidato: `log((N+1)/(df+1)) + 1`.
4. Similitud por coseno entre vector de consulta y documento.
5. Penalizacion pivotada por longitud de chunk para reducir sesgo de documentos largos.
6. Mezcla hibrida vector+keyword usando score normalizado real por canal.

## Implementacion

- `app/services/rag_retriever.py`
  - nuevo scorer keyword: `tfidf_zone_cosine_pivoted`.
  - normalizacion de scores para fusion hibrida.
- `app/core/config.py`
  - nuevos settings de pesos de zona y parametros tf-idf/pivot.
- `.env` / `.env.example`
  - defaults para nuevos parametros.
- tests:
  - `app/tests/test_rag_retriever.py`
  - `app/tests/test_settings_security.py`

## Consecuencias

### Positivas

- mejor precision lexical para consultas clinicas especificas.
- mejor uso de metadatos del documento (`title/source_file`) y estructura (`section_path`).
- menos sesgo por chunks largos.

### Negativas / Riesgos

- `idf` sobre pool candidato (no corpus global) puede introducir variacion entre consultas.
- configurar mal pesos de zona puede reducir recall en algunos dominios.

## Validacion

- `./venv/Scripts/python.exe -m ruff check app/services/rag_retriever.py app/core/config.py app/tests/test_rag_retriever.py app/tests/test_settings_security.py`
- `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_retriever.py app/tests/test_settings_security.py -o addopts=""`
- `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "uses_rag_when_enabled" -o addopts=""`
