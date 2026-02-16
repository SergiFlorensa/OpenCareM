# ADR-0074: Continuidad contextual local y priorizacion de endpoint chat en Ollama

- Fecha: 2026-02-16
- Estado: Aprobado

## Contexto

El chat clinico mostraba respuestas demasiado plantilladas en follow-ups
("y ahora?", "resume", etc.) cuando el modelo local no mantenia hilo
suficiente o cuando el motor caia en fallback. Para un entorno de urgencias,
la continuidad y la accionabilidad son criticas.

## Decision

Aplicar tres cambios sobre el motor local (sin APIs de pago):

1. **Continuidad de follow-up**:
   - expandir consultas cortas con el ultimo turno de sesion (`query_expanded`)
     para mejorar matching y recuperacion contextual.
2. **Ollama conversational-first**:
   - intentar inferencia por `POST /api/chat` con historial corto de turnos.
   - usar `POST /api/generate` como fallback tecnico.
3. **Fallback clinico accionable**:
   - reformatear salida rule-based en bloques operativos (priorizacion,
     contexto, evidencia y cierre), reduciendo texto de plantilla.

## Consecuencias

### Positivas

- Mejor continuidad entre turnos sin depender de servicios cloud.
- Mayor naturalidad cuando el modelo local esta disponible.
- Mejor utilidad operativa incluso en fallback.

### Riesgos

- El comportamiento conversacional depende del modelo local elegido.
- Equipos con 16GB pueden degradar latencia usando modelos demasiado grandes.

## Mitigaciones

- Perfil recomendado para 16GB (`llama3.1:8b`, `num_ctx=4096`, `top_p=0.9`).
- Trazabilidad ampliada (`llm_endpoint`, `query_expanded`).
- Fallback determinista disponible sin romper contrato.

## Validacion

- `.\venv\Scripts\python.exe -m ruff check app/services/clinical_chat_service.py app/services/llm_chat_provider.py app/core/config.py app/tests/test_care_tasks_api.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k "chat_continuity_filters_control_facts_from_memory or chat_follow_up_query_reuses_previous_context_for_domain_matching or chat_message"`
