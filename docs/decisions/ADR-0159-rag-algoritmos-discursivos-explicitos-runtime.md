# ADR-0159: Algoritmos Discursivos Explicitos en Runtime para RAG Clinico

## Estado

Aprobado

## Contexto

Se requeria que la mejora de coherencia no fuera solo heuristica superficial, sino basada
en calculos y funciones concretas ejecutadas en tiempo real durante la conversacion del chat.
El objetivo era que el usuario percibiera respuestas mas enfocadas y menos ruido editorial
sin depender de infraestructura pesada.

## Decision

Extender el reranking discursivo con algoritmos explicitos en codigo y uso efectivo en el
pipeline de `RAGOrchestrator`:

1. `EDU segmentation` para dividir chunks en unidades de discurso.
2. `TextTiling` ligero (coseno entre ventanas vecinas) para detectar continuidad/rupturas topicas.
3. `Lexical chaining` para densidad de cadenas semanticas del campo medico.
4. `LSA-like coherence` basada en TF-IDF compacto sobre EDUs.
5. `Local Coherence Discriminator (LCD)` con operaciones vectoriales:
   - concatenacion,
   - diferencia,
   - valor absoluto de la diferencia,
   - producto elemento a elemento.
6. `Entity Grid` para medir continuidad y cambios de entidad saliente.

Todos los puntajes se mezclan en el score discursivo y modifican el orden final de chunks
antes del ensamblado de respuesta.

## Consecuencias

- Mayor coherencia local y topical en respuestas con evidencia interna.
- Mejor trazabilidad operacional via `rag_discourse_top_*`.
- Aumento marginal de CPU por chunk (acotado a `top-k` recuperado).
- Sin cambios de schema API ni base de datos.

## Validacion

- `./venv/Scripts/python.exe -m ruff check app/services/rag_orchestrator.py app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py`
- `$env:DEBUG='false'; ./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py -o addopts=""`
- `$env:DEBUG='false'; ./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py -o addopts=""`
- Resultado: `216 passed`.

## Riesgos pendientes

- La calidad de segmentacion EDU depende de reglas lexicales y puede requerir ajuste por corpus.
- El modulo LSA-like es compacto (no full SVD global), priorizando coste bajo en entorno local.
