# ADR-0181: Adaptive Evidence Pack and Structured Clinical Writer

## Estado

Aceptada

## Contexto

El `focus mode` del writer clinico redujo el contexto y el tiempo de espera, pero no eliminaba dos fallos de salida:

- el modelo podia devolver eco del propio prompt;
- el writer seguia generando texto libre, lo que complicaba mantener fidelidad y formato estable en CPU local.

Las fuentes recientes sobre RAG y compresion contextual apuntan a dos ideas compatibles con nuestro backend:

1. empaquetar solo la evidencia minima viable antes del writer;
2. pedir al writer una salida mas acotada y estructurada.

## Decision

Se adopta una capa adicional en el writer clinico local:

1. `adaptive evidence pack`
   - prioriza evidencia por solapamiento con la consulta;
   - acumula items hasta cubrir un minimo de evidencia util (`CLINICAL_CHAT_LLM_CLINICAL_MIN_EVIDENCE_CHARS`);
   - evita pasar siempre el mismo numero fijo de fragmentos.

2. `structured clinical writer`
   - cuando el writer clinico nativo esta en `focus mode`, se solicita salida JSON estructurada via `format` de Ollama;
   - el backend parsea y reformatea ese JSON a una respuesta clinica legible;
   - si la respuesta del modelo no cumple el contrato, se considera fallida y se mantiene la degradacion segura.

## Consecuencias

### Positivas

- Menos superficie para `prompt echo`.
- Menos variabilidad en el formato del writer.
- Mejor alineacion entre evidencia recuperada y respuesta final.

### Negativas

- Depende de que el runtime de Ollama soporte correctamente `format` para el modelo/configuracion usada.
- Si el JSON sale malformado, la respuesta se descarta y se pierde el intento neuronal.

## Validacion

- Tests del pack adaptativo de evidencia.
- Tests del payload estructurado enviado a Ollama.
- Tests del parseo y formateo de salida clinica estructurada.
