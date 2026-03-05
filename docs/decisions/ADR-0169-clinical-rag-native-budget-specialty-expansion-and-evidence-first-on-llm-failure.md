# ADR-0169: Clinical RAG native budget, specialty expansion and evidence-first on LLM failure

## Estado

Aceptada

## Contexto

En consultas clinicas genericas como `Paciente con dolor abdominal: datos clave y escalado`, el pipeline podia degradarse por dos razones combinadas:

- configuracion local de presupuesto pre-LLM demasiado estricta (`CLINICAL_CHAT_RAG_MAX_TOTAL_LATENCY_MS=3000` y `CLINICAL_CHAT_RAG_LLM_MIN_REMAINING_BUDGET_MS=2900`), lo que bloqueaba la llamada al LLM casi siempre;
- recuperacion dominada por PDFs especificos del subdominio cuando la consulta era operativa y generica, produciendo snippets correctos pero irrelevantes para la intencion real.

Ademas, si el LLM fallaba a nivel de transporte, el chat podia seguir mostrando el extractivo degradado en lugar de caer a una respuesta `evidence_first` apoyada por motores operativos.

## Decision

Se aplican tres cambios coordinados:

1. Presupuesto nativo de Ollama endurecido contra configuraciones fragiles.
   - El gate pre-LLM ahora limita dinamicamente el minimo restante en estilo nativo de Ollama a un cap pequeno y fijo.
   - Se elevan los defaults locales de latencia a `12000/400` para evitar bloqueos artificiales en portatiles.

2. Expansion de consulta por especialidad para casos genericos-operativos.
   - Gastro-hepato, oftalmologia y SCASEST reciben expansion lexical controlada cuando la consulta es generica y operativa.
   - Esto empuja retrieval hacia motores operativos y secciones accionables.

3. Fallback seguro cuando el LLM falla.
   - Si RAG devuelve un extractivo por error LLM, el chat rechaza ese candidato y prefiere `evidence_first` cuando hay fuentes internas operativas disponibles.

## Consecuencias

Positivas:

- se reduce el numero de `latency_budget_exhausted_pre_llm` artificiales en estilo nativo;
- las consultas genericas operativas recuperan mejor motores por especialidad;
- cuando el LLM cae, el usuario ve una salida mas util y menos sesgada por PDFs especificos.

Negativas:

- el tiempo total por turno puede subir respecto al cap historico de 3s;
- las expansiones por especialidad requieren seguimiento para evitar sobreajuste semantico.

## Validacion

- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py -o addopts=""`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -o addopts=""`
- `.\venv\Scripts\python.exe -m ruff check app/services/rag_orchestrator.py app/services/clinical_chat_service.py app/tests/test_rag_orchestrator_optimizations.py app/tests/test_clinical_chat_operational.py`
