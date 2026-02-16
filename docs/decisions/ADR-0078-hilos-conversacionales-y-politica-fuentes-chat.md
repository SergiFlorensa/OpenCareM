# ADR-0078: Hilos conversacionales y politica de fuentes para chat clinico

## Contexto

Aunque se corrigio el volcado JSON en saludos, faltaba guiar mejor la respuesta inicial
para que el asistente operara con un flujo humano y repetible cuando no hay caso clinico
concreto en el primer turno.

## Decision

- Establecer hilos de respuesta en modo general y en prompt LLM:
  - intencion -> contexto -> fuentes -> accion/siguiente paso.
- Priorizar politica de fuentes internas validadas antes de web (`internal first`).
- En consultas exploratorias, listar dominios disponibles y solicitar datos minimos
  del caso en vez de devolver contenido tecnico crudo.

## Consecuencias

- Mejora la naturalidad y la utilidad del primer turno.
- Mantiene trazabilidad tecnica para auditoria (`reasoning_threads`, `source_policy`).
- La profundidad clinica sigue limitada por el volumen/calidad del catalogo interno vigente.
