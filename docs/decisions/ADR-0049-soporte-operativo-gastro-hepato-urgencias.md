# ADR-0049: Soporte Operativo Gastro-Hepato para Urgencias

- Fecha: 2026-02-13
- Estado: Aprobado

## Contexto

El proyecto disponia de motores clinico-operativos, pero faltaba una capa gastro-hepato
que unificara:

- urgencias vasculares/hemodinamicas digestivas,
- red flags radiologicas abdominales de mal pronostico,
- criterios quirurgicos iniciales trazables,
- alertas de seguridad farmacologica y pruebas funcionales/geneticas clave.

## Decision

Crear el workflow `gastro_hepato_support_v1` y exponerlo mediante:

- `POST /api/v1/care-tasks/{task_id}/gastro-hepato/recommendation`

Persistir trazas en `agent_runs/agent_steps` con `run_output.gastro_hepato_support`.

Agregar metricas Prometheus:

- `gastro_hepato_support_runs_total`
- `gastro_hepato_support_runs_completed_total`
- `gastro_hepato_support_critical_alerts_total`

## Consecuencias

### Positivas

- Estandariza decisiones operativas digestivas/hepatobiliares de urgencias.
- Mejora la priorizacion de casos con alto riesgo de deterioro rapido.
- Aumenta observabilidad con trazas y metricas dedicadas.
- No requiere migraciones de BD (reutiliza trazas existentes).

### Riesgos

- Riesgo de uso fuera de alcance si se interpreta como diagnostico definitivo.
- Sensibilidad/especificidad depende de calibracion local y contexto epidemiologico.
- Dependencia de disponibilidad de endoscopia, Doppler y TAC.

## Mitigaciones

- Mantener advertencia de no diagnostico en la salida del motor.
- Validacion humana obligatoria en todos los escenarios.
- Revisiones periodicas de reglas y ajustes por centro.
