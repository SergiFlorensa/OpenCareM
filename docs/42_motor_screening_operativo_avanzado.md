# TM-047 - Motor de Screening Operativo Avanzado

## Objetivo

Implementar un motor de soporte para urgencias que unifique:

- riesgo geriatrico por reglas interpretables,
- sugerencias de cribado temprano (VIH/sepsis),
- criterios operativos de COVID persistente,
- recomendacion de estrategia long-acting tras fase aguda,
- y control de fatiga de alarmas.

## Endpoint nuevo

- `POST /api/v1/care-tasks/{task_id}/screening/recommendation`

Entrada: `AdvancedScreeningRequest`.

Salida: `CareTaskAdvancedScreeningResponse` con:

- `workflow_name=advanced_screening_support_v1`
- riesgo geriatrico (`low|medium|high`)
- acciones de cribado
- alertas con conteo de generadas/suprimidas
- bandera de candidato long-acting
- bandera de sospecha de COVID persistente

## Reglas destacadas

Archivo: `app/services/advanced_screening_service.py`

- Mayor de 65 + `PAS <115` eleva riesgo operativo.
- Se ponderan movilidad, saturacion, frecuencia cardiaca, sodio y glucosa.
- Se activa sugerencia de cribado VIH ante indicadores operativos (ITS, neumonia, fiebre sin foco, etc.).
- Se activa ruta de sepsis por patrones de alto riesgo.
- COVID persistente: inmunosupresion + positividad >14 dias + clinica persistente + imagen compatible.
- Long-acting: candidato cuando hay estabilidad tras fase aguda y contexto infeccioso elegible.

## Control de fatiga de alarmas

El motor:

- deduplica alertas por clave,
- prioriza severidad alta sobre media,
- limita alertas visibles a un maximo operativo,
- y reporta `alerts_generated_total` y `alerts_suppressed_total`.

## Trazabilidad de agente

Archivo: `app/services/agent_run_service.py`

- Workflow: `advanced_screening_support_v1`
- Paso: `advanced_screening_assessment`
- Entrada y salida persistidas para auditoria.

## Metricas Prometheus

Archivo: `app/metrics/agent_metrics.py`

- `advanced_screening_runs_total`
- `advanced_screening_runs_completed_total`
- `advanced_screening_alerts_generated_total`
- `advanced_screening_alerts_suppressed_total`

## Validacion ejecutada

- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests`

## Limites

- Es un motor no diagnostico y requiere validacion clinica humana obligatoria.
- No reemplaza protocolos institucionales ni juicio medico.
