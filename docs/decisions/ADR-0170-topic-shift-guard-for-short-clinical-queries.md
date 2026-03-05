# ADR-0170: Topic-shift guard for short clinical queries

## Estado

Aceptada

## Contexto

Consultas clinicas cortas pero autonomas, como `Paciente con dolor abdominal: datos clave y escalado`, estaban entrando en la reescritura con historial solo por tener 8 tokens o menos.

Eso contaminaba el retrieval con el tema previo de la sesion, por ejemplo `oncologia`, y acababa generando bloques mixtos en respuestas que debian pertenecer a un unico dominio.

## Decision

Se endurece la clasificacion previa a la reescritura contextual:

- una consulta corta ya no se considera follow-up por longitud solamente;
- si la consulta tiene senal clinica autonoma y keyword hits de dominio, no se mezcla con historial salvo que haya referencias contextuales explicitas.

Esto sigue la recomendacion de clasificar mejor la necesidad de transformacion de consulta antes de recuperar evidencia.

## Consecuencias

Positivas:

- se reduce la deriva de dominio entre turnos;
- mejora la precision de `matched_domains` en cambios reales de tema;
- el RAG recupera menos ruido de la sesion previa.

Negativas:

- algunos follow-ups muy cortos pero mal formulados pueden necesitar mas pistas explicitas (`y ahora`, `y su dosis`) para activar reescritura.

## Validacion

- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py app/tests/test_clinical_chat_operational.py -o addopts=""`
- reproduccion local de topic shift:
  - turno 1: oncologia
  - turno 2: `Paciente con dolor abdominal: datos clave y escalado`
  - resultado: `effective_specialty=gastro_hepato`, `query_expanded=0`, `matched_domains=gastro_hepato`
