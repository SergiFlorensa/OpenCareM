# ADR-0180: Clinical Writer Focus Mode and Bounded Ollama Options

## Estado

Aceptada

## Contexto

El cuello de botella actual del chat clinico local no esta en retrieval sino en la ultima milla de generacion: el writer basado en Ollama + `llama3.2:3b` sobre CPU. La traza mostraba dos problemas combinados:

- el prompt clinico seguia arrastrando mas contexto del necesario para una tarea de redaccion controlada;
- `_build_ollama_native_options()` elevaba `num_ctx` y `num_predict` por encima de los valores configurados, lo que incrementaba trabajo de decodificacion y presion sobre CPU/RAM.

## Decision

Se introduce un perfil explicito de `focus mode` para el writer clinico nativo:

1. caps de runtime dedicados para clinica:
   - `CLINICAL_CHAT_LLM_CLINICAL_NUM_CTX_TARGET`
   - `CLINICAL_CHAT_LLM_CLINICAL_MAX_OUTPUT_TOKENS`
   - `CLINICAL_CHAT_LLM_CLINICAL_MAX_QUERY_CHARS`
   - `CLINICAL_CHAT_LLM_CLINICAL_MAX_EVIDENCE_ITEMS`
   - `CLINICAL_CHAT_LLM_CLINICAL_MAX_SNIPPET_CHARS`
   - `CLINICAL_CHAT_LLM_CLINICAL_MAX_ENDPOINT_ITEMS`
2. el writer clinico deja de arrastrar dialogo previo cuando `focus mode` esta activo;
3. el prompt clinico queda reducido a consulta + evidencia delimitada + reglas cortas;
4. las `options` de Ollama respetan siempre el techo configurado y ya no lo inflan por defecto.

## Consecuencias

### Positivas

- Menor carga de tokens y menor uso de KV cache para la fase de redaccion final.
- Menor riesgo de timeout por inflado accidental de `num_ctx/num_predict`.
- Menor deriva del writer al eliminar historial conversacional irrelevante en clinica.

### Negativas

- Si los caps del `focus mode` se ajustan demasiado a la baja, algunas respuestas utiles pueden quedarse cortas.
- El cambio no sustituye decisiones futuras de modelo/quantizacion o tuning del runtime de Ollama fuera del backend.

## Validacion

- Tests de settings para caps invalidos.
- Tests del provider para comprobar:
  - respeto de caps clinicos en `options`;
  - recorte de prompt/evidencia;
  - omision de `recent_dialogue` en writer clinico con `focus mode`.
