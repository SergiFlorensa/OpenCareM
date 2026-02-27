# ADR-0093: Logica Formal Extendida en Chat Clinico (Godel + Consistencia + Abstencion)

- Fecha: 2026-02-22
- Estado: Aprobado

## Contexto

El motor logico inicial (TM-130) resolvia reglas deterministas y contradicciones,
pero faltaban mecanismos formales para:

- firmar estructuralmente la secuencia de acciones recomendadas,
- verificar consistencia/terminacion de la derivacion,
- abstenerse cuando la evidencia fuera insuficiente o inconsistente.

## Decision

Se extiende `ClinicalLogicEngineService` con:

- Codificacion estructural tipo Godel para secuencias de pasos operativos.
- Decodificacion de roundtrip para validar integridad de la secuencia.
- Firma beta simplificada de la secuencia para trazabilidad compacta.
- Minimizacion acotada para detectar primer paso de escalado.
- Evaluacion de consistencia formal con tres estados:
  - `consistent`
  - `inconsistent`
  - `insufficient_evidence`
- Senal de abstencion (`abstention_required`) que fuerza fallback estructurado en
  `ClinicalChatService` cuando existe riesgo de cierre inseguro.

## Consecuencias

### Positivas

- Mayor auditabilidad de la logica aplicada por turno.
- Menor riesgo de cerrar respuestas con base insuficiente.
- Trazas mas utiles para QA y tuning en local sin costes externos.

### Riesgos

- La codificacion estructural es acotada (diseno pragmatica, no demostrador formal completo).
- Puede aumentar falsos positivos de abstencion en consultas extremadamente breves.

## Validacion

- `.\venv\Scripts\python.exe -m ruff check app/services/clinical_logic_engine_service.py app/services/clinical_chat_service.py app/tests/test_clinical_chat_operational.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "logic_engine"`
