# Motor conversacional neuronal open source (v2)

## Objetivo

Mejorar naturalidad, coherencia y velocidad percibida del chat mediante un
motor neuronal local, manteniendo seguridad clinica y trazabilidad.

## Arquitectura aplicada

1. **Deteccion de modo**
   - `auto` decide entre `general` y `clinical` por senales clinicas.
2. **RAG operativo**
   - contexto de memoria de sesion/paciente + fuentes internas + web (whitelist).
3. **Generacion neuronal local**
   - proveedor `Ollama` via `POST /api/chat` con historial corto.
   - fallback automatico a `POST /api/generate` si el endpoint chat falla o devuelve vacio.
4. **Fallback determinista**
   - si el LLM falla/no esta activo, responde motor rule-based.
5. **Continuidad de follow-up**
   - consultas cortas de seguimiento se expanden con el ultimo turno (`query_expanded`)
     para conservar el hilo clinico.

## Configuracion

Variables en settings:

- `CLINICAL_CHAT_LLM_ENABLED`
- `CLINICAL_CHAT_LLM_PROVIDER` (`ollama`)
- `CLINICAL_CHAT_LLM_BASE_URL`
- `CLINICAL_CHAT_LLM_MODEL`
- `CLINICAL_CHAT_LLM_TIMEOUT_SECONDS`
- `CLINICAL_CHAT_LLM_MAX_OUTPUT_TOKENS`
- `CLINICAL_CHAT_LLM_TEMPERATURE`
- `CLINICAL_CHAT_LLM_NUM_CTX`
- `CLINICAL_CHAT_LLM_TOP_P`

## Flujo de respuesta

- Si `LLM_ENABLED=true`:
  - se construyen mensajes con contexto reciente y fuentes.
  - se intenta `/api/chat` (mejor continuidad conversacional).
  - se registra latencia/modelo/endpoint en `interpretability_trace`.
- Si falla:
  - se conserva respuesta operativa por reglas sin romper SLA de producto.

## Recomendacion de despliegue local

1. Instalar y arrancar Ollama.
2. Descargar modelo instruccional quantizado (8B recomendado para latencia en 16GB).
3. Activar en `.env`:
   - `CLINICAL_CHAT_LLM_ENABLED=true`
   - `CLINICAL_CHAT_LLM_BASE_URL=http://127.0.0.1:11434`
   - `CLINICAL_CHAT_LLM_NUM_CTX=4096`
   - `CLINICAL_CHAT_LLM_TOP_P=0.9`
4. Reiniciar backend.

## Seguridad clinica

- El chat clinico mantiene advertencia de no diagnostico.
- Fuentes web siguen filtradas por dominios permitidos.
- Trazabilidad completa del turno en `agent_runs` y `care_task_chat_messages`.
