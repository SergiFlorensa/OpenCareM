# ADR-0016: Integracion baseline de Alertmanager

## Contexto

Prometheus ya evaluaba alertas, pero faltaba un componente de enrutado para manejo operativo real.

## Decision

Integrar Alertmanager en Docker Compose y conectar Prometheus via bloque `alerting`.

Configuracion inicial:

- receiver unico `default` (sin canal externo todavia)
- agrupacion por `alertname/service/component`

## Consecuencias

Beneficios:

- Flujo completo de alerta detectada -> alerta enrutada.
- Base para aÃ±adir Slack/email/webhook sin rediseÃ±o.

Costes:

- Componente extra que operar en entorno local.

## Validacion

- `docker compose config`
- `http://127.0.0.1:9093/#/alerts`



