# ADR-0182: Clinical Writer-Lite Chat and Lexicalizer Fallback

## Estado

Aceptada

## Contexto

Tras introducir `focus mode`, pack adaptativo de evidencia y salida estructurada opcional, el cuello de botella restante seguia concentrado en la ultima milla del writer clinico local:

- `llama3.2:3b` en CPU agotaba presupuesto al escribir respuestas clinicas largas;
- el intento de `structured output` via `format` no mejoraba el throughput del camino critico;
- cuando el writer devolvia `done_reason=length`, la salida quedaba truncada y el sistema podia acabar en fallback generico.

La evidencia publica revisada (RECOMP, EXIT, ECoRAG-lite, docs de Ollama) apuntaba a reducir aun mas la carga del writer y a no repetir escritores pesados tras un `TimeoutError`.

## Decision

Se redefine el writer clinico en `focus mode` con dos reglas:

1. `writer-lite`
   - se usa `api/chat` con solo dos mensajes (`system` + `user`);
   - el `user` contiene consulta corta y evidencia ultracorta etiquetada;
   - no se arrastra dialogo previo ni se exige `format` JSON en el camino critico;
   - el writer se ejecuta con caps estrictos de `num_ctx` y `num_predict`.

2. `lexicalizer fallback`
   - si el primer intento devuelve `TimeoutError`, no se lanza un segundo writer pesado;
   - si la salida llega truncada (`done_reason=length` / `max_tokens`), se repara localmente;
   - la reparacion usa lexicalizacion determinista de la evidencia ya filtrada.

## Consecuencias

### Positivas

- Se reduce el tiempo real de la ultima milla en CPU local.
- Se evita gastar presupuesto en un segundo intento LLM que suele fracasar por la misma causa fisica.
- Se elimina el fallback generico de baja utilidad cuando si existe evidencia interna valida.

### Negativas

- La lexicalizacion local es mas extractiva que una redaccion neuronal completa.
- Puede aparecer repeticion de bullets o cierre menos natural si la evidencia de entrada es muy pobre.
- El writer puede seguir necesitando ajuste fino por especialidad si el 3B se corta con frecuencia.

## Validacion

- Tests de timeouts en `focus mode`.
- Tests de `prompt echo` con recuperacion por `chat_quick_recovery`.
- Tests de desactivacion del `structured output` en el camino critico.
- Tests de reparacion por lexicalizador tras truncado.
- Sonda real con consulta `Paciente con dolor agudo postoperatorio: datos clave y escalado`:
  - antes: >70s y/o fallback generico;
  - despues: ~31s, `llm_used=true`, `llm_endpoint=chat`, `llm_post_repair=lexicalizer`.
