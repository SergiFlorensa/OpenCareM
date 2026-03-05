# ADR-0161: Modo de Evaluacion Relajada del Pipeline de Chat

## Estado

Aprobado

## Contexto

El equipo necesitaba evaluar la calidad real de salida conversacional con RAG interno sin
interferencia de capas de fallback rigidas. En modo estricto, algunas respuestas validas del
modelo quedaban sobreescritas por salvaguardas (safe-wrapper, gates de calidad y fallbacks
estructurados), dificultando el diagnostico fino del pipeline.

## Decision

Se incorpora un flag opcional por request en chat:

- `pipeline_relaxed_mode` (bool, default `false`).

Cuando `true`, el pipeline opera en perfil `evaluation`:

1. En `RAGOrchestrator`:
   - desactiva efectivamente safe-wrapper y gatekeeper (`rag_*_effective_enabled=0`),
   - mantiene retrieval y ensamblado, pero evita abstenciones rigidas automáticas.

2. En `ClinicalChatService`:
   - desactiva gates de calidad/fallbacks rigidos del ensamblado final
     (uncertainty gate, rag_validation gate, llm quality gates, contract/logic forced fallback,
     final clinical quality gate y quality repair automatico).

3. En frontend interno:
   - se envia `pipeline_relaxed_mode=true` por defecto para pruebas hasta nuevo aviso.

El modo estricto permanece como comportamiento por defecto para compatibilidad y despliegue seguro.

## Consecuencias

- Permite evaluar respuesta real del modelo + RAG con menor “rigidez” de salida.
- Facilita tuning de prompts/ranking/chunks sin ruido de fallback forzado.
- Aumenta riesgo semantico si se usa en produccion sin criterio (al bajar barreras).

## Validacion

- `./venv/Scripts/python.exe -m ruff check app/schemas/clinical_chat.py app/services/clinical_chat_service.py app/services/rag_orchestrator.py app/tests/test_clinical_chat_operational.py app/tests/test_rag_orchestrator_optimizations.py`
- `$env:DEBUG='false'; ./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py -o addopts=""`
- `npm --prefix frontend run build`

## Riesgos pendientes

- Requiere disciplina operativa: volver a `pipeline_relaxed_mode=false` para validaciones de seguridad final.
- Algunas salidas en modo relajado pueden ser menos conservadoras en abstención.
