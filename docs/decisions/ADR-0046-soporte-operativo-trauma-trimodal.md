# ADR-0046: Soporte operativo de trauma con curva trimodal

## Contexto

La plataforma no tenia un workflow dedicado para trauma que unificara criterios operativos tempranos de alto impacto:

- curva trimodal de mortalidad,
- compromiso de via aerea en trauma laringeo,
- sindromes medulares diferenciales,
- aplastamiento y riesgo renal/metabolico,
- particularidades por perfil (geriatria/pediatria/embarazo),
- hipotermia con umbrales electrofisiologicos,
- clasificacion Gustilo-Anderson para fracturas expuestas.

## Decision

Agregar un motor de soporte operativo de trauma como workflow explicable y trazable:

1. Endpoint nuevo:
- `POST /api/v1/care-tasks/{id}/trauma/recommendation`

2. Workflow trazable:
- `workflow_name=trauma_support_v1`
- `step_name=trauma_operational_assessment`

3. Contrato de salida:
- Prioridad operativa por fase trimodal y TECLA/TICLA.
- Escalado de via aerea por triada laringea y signos de insuficiencia.
- Sospecha sindromica medular (central/anterior/Brown-Sequard).
- Riesgo por aplastamiento, necesidad de ECG seriados y riesgo renal.
- Estrategias por perfil poblacional.
- Estadiaje de hipotermia y alertas por umbrales criticos.
- Grado Gustilo-Anderson y cobertura antibiotica orientativa.
- Matriz `condition_matrix[]` con filas estructuradas de politrauma, choque hemorragico,
  neumotorax a tension, taponamiento cardiaco, TCE, sindrome compartimental y quemaduras,
  incluyendo fuente operacional.

4. Observabilidad:
- `trauma_support_runs_total`
- `trauma_support_runs_completed_total`
- `trauma_support_critical_alerts_total`

## Consecuencias

Positivas:
- Estandariza respuesta operativa inicial ante trauma complejo.
- Mejora trazabilidad auditable de decisiones no diagnosticas.
- Permite monitorizar carga y severidad operativa del dominio trauma.

Riesgos:
- Posible sobre-alerta si no se calibra por centro.
- No sustituye protocolos institucionales ni liderazgo clinico presencial.

## Validacion

- `ruff check` de archivos afectados en API/servicio/metricas/tests.
- `pytest -k trauma_support` sobre `test_care_tasks_api.py` y `test_metrics_endpoint.py` (`4 passed`).
