# TM-049 - Soporte de Interpretacion RX de Torax

## Objetivo

Añadir un motor operativo para ayudar en lectura sistematica de radiografia de torax
sin emitir diagnostico definitivo.

El motor organiza:

- patrones sospechados,
- red flags urgentes,
- acciones recomendadas,
- advertencias por tipo de proyeccion.

## Endpoint nuevo

- `POST /api/v1/care-tasks/{task_id}/chest-xray/interpretation-support`

Entrada: `ChestXRaySupportRequest` (proyeccion, calidad inspiratoria, patron, signos, tamano de lesion).

Salida: `CareTaskChestXRaySupportResponse` con:

- `workflow_name=chest_xray_support_v1`
- `suspected_patterns`
- `urgent_red_flags`
- `suggested_actions`
- `projection_caveats`

## Reglas operativas aplicadas

Archivo: `app/services/chest_xray_support_service.py`

- Patron alveolar + broncograma -> sospecha de ocupacion alveolar.
- Lineas B de Kerley -> orientacion a patron intersticial congestivo.
- Desplazamiento de cisuras -> orientacion a atelectasia.
- Linea pleural + ausencia de trama periferica -> sospecha de neumotorax.
- Neumotorax + desplazamiento mediastinico -> red flag de posible tension.
- AP + cardiomegalia aparente -> advertencia de falsa magnificacion.
- Lesion >=3 cm -> clasificacion operativa como masa.

## Trazabilidad y metricas

Workflow persistido:

- `chest_xray_support_v1`
- paso `chest_xray_interpretation_assessment`

Metricas en `/metrics`:

- `chest_xray_support_runs_total`
- `chest_xray_support_runs_completed_total`
- `chest_xray_support_critical_alerts_total`

## Validacion ejecutada

- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests`
- `.\venv\Scripts\ruff.exe check` en archivos Python modificados

## Limites

- Motor no diagnostico.
- Requiere validacion clinica humana obligatoria.
