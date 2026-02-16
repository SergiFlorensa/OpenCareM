# Integracion de Alertmanager

## Objetivo

Completar el flujo de alertas: Prometheus detecta y Alertmanager enruta.

## Servicios

- Prometheus: `http://127.0.0.1:9090`
- Alertmanager: `http://127.0.0.1:9093`

## Que se agrego

1. Servicio `alertmanager` en `docker-compose.yml`.
2. Config base en `ops/alertmanager/alertmanager.yml`.
3. Bloque `alerting` en `ops/prometheus/prometheus.yml` para enviar alertas a Alertmanager.

## Como validar

1. Levantar stack:
- `docker compose up --build`

2. Ver reglas activas en Prometheus:
- `http://127.0.0.1:9090/rules`

3. Ver alertas en Alertmanager:
- `http://127.0.0.1:9093/#/alerts`

## Nota

La configuracion base enruta a receiver `default` sin integracion externa.
El siguiente paso es conectar email/Slack/webhook.


