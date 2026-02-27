# ADR-0092: Motor Logico Clinico Determinista en Chat

- Fecha: 2026-02-22
- Estado: Aprobado

## Contexto

El flujo conversacional clinico dependia demasiado de componentes generativos.
Se necesitaba una capa previa de inferencia formal, auditable y barata para
reducir respuestas genericas y mejorar seguridad operativa.

## Decision

Se incorpora `ClinicalLogicEngineService` con:

- reglas deterministas por dominio (estilo secuente: premisas -> acciones),
- detector de contradicciones textuales de alto impacto,
- resumen epistemico basico (hechos reportados/inferidos/confirmados).

La salida se integra en:

- `extracted_facts` (`logic_rule:*`, `logic_contradictions:*`),
- `interpretability_trace` (`logic_*`),
- fallback clinico (bloque "logico formal").

## Consecuencias

### Positivas

- Menor dependencia del LLM para decisiones operativas criticas.
- Mayor trazabilidad y auditoria de por que se prioriza una accion.
- Coste computacional local bajo.

### Riesgos

- Reglas iniciales limitadas: requieren curacion incremental por especialidad.
- El detector de contradicciones textual es baseline (no NLU profundo).

## Validacion

- `.\venv\Scripts\python.exe -m ruff check app/services/clinical_logic_engine_service.py app/services/clinical_chat_service.py app/services/__init__.py app/tests/test_clinical_chat_operational.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "logic_engine or psychology or interrogatory"`
