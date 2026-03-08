# ADR-0179: Prompt de redaccion clinica controlada sobre evidencia delimitada

## Estado

Aceptado

## Contexto

El retrieval clinico ya estaba devolviendo evidencia razonable, pero la fase final de redaccion seguia fallando en dos modos:

- cuando el LLM respondia, el gatekeeper rechazaba la salida por baja fidelidad
- cuando el prompt era demasiado largo, el writer local (`llama3.2:3b` en CPU) agotaba el presupuesto y el sistema caia a fallback extractivo

Hacia falta cerrar la tarea del modelo: dejar de pedirle una sintesis abierta y pedirle una reformulacion estricta sobre evidencia ya seleccionada.

## Decision

Se adopta un prompt clinico nativo mas controlado:

1. El prompt del usuario se estructura en bloques delimitados:
   - `CONSULTA`
   - `EVIDENCIA`
   - `REGLAS`
2. La evidencia interna se limita y se etiqueta con ids (`[S1]`, `[S2]`, `[E1]`).
3. Se introduce una abstencion exacta cuando no hay evidencia verificada.
4. Se reduce el numero de fuentes/snippets por turno para bajar carga de tokens.
5. Se amplia ligeramente el presupuesto de salida del writer clinico para evitar cortes demasiado agresivos.

## Consecuencias

### Positivas

- El prompt es mas corto y mas determinista.
- La tarea del modelo pasa de "razonar sobre contexto libre" a "reformular evidencia delimitada".
- Se reduce el riesgo de introducir conocimiento general no soportado.

### Limitaciones

- En este hardware, el writer local sigue pudiendo agotar tiempo aunque el prompt sea mejor.
- La mejora del prompt no sustituye una futura separacion mas radical entre `evidence pack` y `writer`.

## Validacion

- `pytest -q app/tests/test_clinical_chat_operational.py -k "native_clinical_prompt_uses_controlled_delimited_evidence_pack or native_clinical_prompt_without_sources_forces_exact_abstention or ollama_native_options_expand_clinical_output_budget" -o addopts=""`
- `ruff check app/services/llm_chat_provider.py app/tests/test_clinical_chat_operational.py`
- Prueba real: la misma consulta clinica baja de ~602 a ~380 tokens de entrada estimados, pero el writer local sigue agotando `90s`.

## Riesgos pendientes

- La siguiente iteracion debe reducir aun mas el trabajo del writer o introducir una etapa de redaccion mas ligera.
- No conviene seguir inflando reglas de prompt; el margen restante es arquitectonico, no verbal.
