# ADR-0088: Interrogatorio Activo Bayes+DEIG en Chat Clinico

- Fecha: 2026-02-22
- Estado: Aprobado

## Contexto

El chat clinico tendia a responder con planes generales incluso cuando faltaban
datos criticos de entrada. En esos casos, el modelo podia degradar calidad o
derivar a fallback demasiado pronto.

Se requiere un paso previo de aclaracion en consultas incompletas para reducir
incertidumbre antes de generar un plan operativo.

## Decision

Se incorpora un motor de interrogatorio activo opcional:

- Servicio nuevo: `app/services/diagnostic_interrogatory_service.py`.
- Metodo base:
  - candidatos con prior por dominio,
  - actualizacion bayesiana con evidencia observada,
  - ranking de preguntas por DEIG (`IG + divergence + concentration`).
- Integracion en `ClinicalChatService.create_message` con short-circuit:
  - si hay alta incertidumbre y el dominio esta soportado, se devuelve
    pregunta de aclaracion en ese turno,
  - se evita invocar LLM/RAG en ese turno para reducir latencia y ruido.

Activacion por request (default desactivado para compatibilidad):

- `enable_active_interrogation`
- `interrogation_max_turns`
- `interrogation_confidence_threshold`

## Consecuencias

Positivas:

- Menos respuestas inventadas o genericas cuando faltan datos clave.
- Menor latencia en turnos de aclaracion (no se invoca LLM/RAG).
- Trazabilidad adicional en `interpretability_trace` (`interrogatory_*`, `deig_score`).

Costes/Riesgos:

- Cambia el patron de UX: algunos turnos responden con pregunta en vez de plan final.
- Cobertura inicial limitada a dominios modelados (fase 1).

## Validacion

- `.\venv\Scripts\python.exe -m ruff check app/services/diagnostic_interrogatory_service.py app/services/clinical_chat_service.py app/schemas/clinical_chat.py app/tests/test_clinical_chat_operational.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "interrogatory or quality_gate or rag_validation_warns"`

## Rollout

- Fase 1: opt-in via payload (default `false`).
- Cuando se valide en uso real, evaluar activacion por defecto y extension a mas dominios.
