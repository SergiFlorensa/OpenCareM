# ADR-0094: Contratos Operativos por Dominio en Chat Clinico

- Fecha: 2026-02-22
- Estado: Aprobado

## Contexto

La capa logica (TM-130/TM-131) mejoro consistencia, pero faltaba una forma
estandar de devolver planes operativos por especialidad con datos minimos
obligatorios y criterios de escalado estructurados.

## Decision

Se integra `ClinicalProtocolContractsService` en el flujo de chat clinico con:

- contratos por dominio (fase 1):
  - `nephrology`
  - `gynecology_obstetrics`
- estado de contrato por turno:
  - `ready`
  - `needs_data`
  - `partial`
  - `blocked_contradiction`
- trazas nuevas `contract_*` en `interpretability_trace`.
- guard de seguridad: si el contrato marca `force_structured_fallback`, se
  evita cierre LLM libre y se devuelve respuesta estructurada.

## Consecuencias

### Positivas

- Respuesta mas predecible y auditable por especialidad.
- Menor riesgo de recomendaciones con datos clinicos insuficientes.
- Escalable: permite añadir dominios nuevos como contratos versionados.

### Riesgos

- Cobertura inicial limitada a dos dominios; requiere extension progresiva.
- Posibles falsos positivos de `needs_data` en consultas muy breves.

## Validacion

- `.\venv\Scripts\python.exe -m ruff check app/services/clinical_protocol_contracts_service.py app/services/clinical_chat_service.py app/services/__init__.py app/tests/test_clinical_chat_operational.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "logic_engine or protocol_contract"`
