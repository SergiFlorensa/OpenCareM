# ADR-0089: Psicologia de Decision en Chat Clinico (Fechner + Prospect)

- Fecha: 2026-02-22
- Estado: Aprobado

## Contexto

En escenarios de urgencias, el usuario no siempre procesa riesgo de forma lineal.
El chat necesitaba una capa de comunicacion de riesgo mas humana sin salir del
marco operativo y no diagnostico.

## Decision

Se integra una capa local ligera en backend:

- Servicio nuevo: `app/services/clinical_decision_psychology_service.py`.
- Capacidades:
  - estimacion psicofisica tipo Fechner para intensidad/cambio percibido de sintomas,
  - framing de riesgo inspirado en Prospect Theory (`loss_avoidance_*`, `gain_focus_*`).
- Integracion en `ClinicalChatService`:
  - agrega hechos derivados (`risk_level`, `risk_frame`, `fechner_*`),
  - amplia `interpretability_trace` con claves `prospect_*` y `fechner_*`,
  - refuerza fallback clinico con linea de comunicacion de riesgo operativo.

## Consecuencias

Positivas:

- Mejora la claridad al explicar por que priorizar acciones inmediatas.
- Reduce respuestas frias/genericas en fallback sin depender de APIs externas.
- Aumenta auditabilidad (trazas explicitas).

Costes/Riesgos:

- Heuristicas iniciales; requieren calibracion clinica progresiva.
- No sustituye protocolos locales ni razonamiento medico presencial.

## Validacion

- `.\venv\Scripts\python.exe -m ruff check app/services/clinical_decision_psychology_service.py app/services/clinical_chat_service.py app/services/__init__.py app/tests/test_clinical_chat_operational.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "psychology or interrogatory or quality_gate or rag_validation_warns"`
