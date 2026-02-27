# ADR-0101: Parser booleano con precedencia, frases y spell correction local

- Fecha: 2026-02-24
- Estado: Aprobado

## Contexto

Tras TM-144, el candidate retrieval ya usa FTS5 y postings booleanos, pero:

- el parser booleano era secuencial (sin precedencia real ni parentesis);
- no habia soporte explicito de frases (`"..."`);
- la tolerancia a errores ortograficos era limitada.

Esto afectaba recall y precision en consultas clinicas reales escritas en lenguaje natural.

## Decision

Se amplian capacidades en `HybridRetriever`:

- parser booleano con tokens, parentesis y precedencia:
  - `NOT > AND > OR`;
  - insercion de `AND` implicito entre operandos adyacentes;
  - conversion a RPN (shunting-yard) y evaluacion sobre postings.
- soporte de frases en retrieval FTS:
  - operandos entre comillas se consultan como phrase query.
- spell correction local opcional:
  - sugerencia por distancia de edicion (Levenshtein) sobre `fts5vocab`;
  - aplicacion solo cuando no hay postings para un termino;
  - sin dependencias de pago ni servicios externos.

Nuevos flags:

- `CLINICAL_CHAT_RAG_SPELL_CORRECTION_ENABLED`
- `CLINICAL_CHAT_RAG_SPELL_MAX_EDIT_DISTANCE`

## Consecuencias

### Positivas

- mejor robustez en consultas con operadores complejos;
- mejor match para terminos clinicos compuestos;
- menor fallo por typos comunes en preguntas de guardia.

### Riesgos

- correccion ortografica puede introducir falsos positivos en terminos raros;
- expresiones booleanas muy largas pueden subir latencia del candidate stage.

## Validacion

- `.\venv\Scripts\python.exe -m ruff check app/services/rag_retriever.py app/core/config.py app/tests/test_rag_retriever.py app/tests/test_settings_security.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_rag_retriever.py app/tests/test_settings_security.py -o addopts=""`
