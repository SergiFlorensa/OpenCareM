# 96. Adaptacion del blueprint de agentes OSS a uso interno

## Problema que resuelve

Necesitamos aprovechar patrones de producto basados en agentes sin arrastrar
capas que no aportan valor al contexto actual del repo (suscripciones,
movil, mensajeria externa).

## Decision de alcance

Aplicar:

- Logica de agentes y separacion de modos conversacionales.
- Flujo operativo reproducible de desarrollo/calidad.
- Trazabilidad y validacion por capas.

No aplicar:

- Suscripciones o monetizacion por tokens.
- Aplicaciones moviles nativas.
- Integraciones Telegram/WhatsApp/Signal/Discord.

## Bloque operativo minimo (adaptado al stack actual)

Se estandariza una base de ejecucion local:

- `dev`: `scripts/dev_workflow.ps1 -Action dev`
- `build`: `scripts/dev_workflow.ps1 -Action build`
- `check`: `scripts/dev_workflow.ps1 -Action check`
- `test`: `scripts/dev_workflow.ps1 -Action test`
- `test-e2e`: `scripts/dev_workflow.ps1 -Action test-e2e`

Objetivo: evitar variaciones entre desarrolladores y simplificar CI local.

## Pre-commit inteligente (solo staged)

Se agrega `.pre-commit-config.yaml` con hooks locales para Python staged:

- `ruff check --fix`
- `black`
- `ruff check` de verificacion

Beneficio: calidad automatica sin ejecutar chequeos innecesarios sobre todo el
repositorio en cada commit.

## Setup de onboarding

Se agrega `scripts/setup_hooks.ps1` para:

- instalar `pre-commit`,
- instalar hooks en `.git/hooks`,
- validar configuracion de hooks,
- opcionalmente ejecutar hooks sobre todo el repo (`-RunAllFiles`).

## Arquitectura de modos del motor

Se mantiene el enfoque actual:

- `response_mode=general` para consultas no clinicas.
- `response_mode=clinical` para respuesta protocolizada y trazable.
- Proveedor LLM local opcional (`Ollama`) con fallback deterministico.

Esto permite evolucionar experiencia conversacional sin acoplarla a canales
externos ni a logica de billing.

## Testing por capas (pragmatico)

1. Calidad estatica: `ruff`, `black`, `mypy`.
2. Regresion rapida: `pytest -q`.
3. Flujo conversacional focalizado: tests chat/e2e (`-Action test-e2e`).

## Plan de validacion de esta adaptacion

- Validar config de hooks:
  - `python -m pre_commit validate-config`
- Validar flujo de calidad:
  - `powershell -ExecutionPolicy Bypass -File scripts/dev_workflow.ps1 -Action check`
- Validar flujo de chat focalizado:
  - `powershell -ExecutionPolicy Bypass -File scripts/dev_workflow.ps1 -Action test-e2e`

## Riesgos pendientes

- Requiere disciplina inicial del equipo para ejecutar `setup_hooks`.
- `test-e2e` cubre chat principal, pero no reemplaza regresion completa.
- Si cambian contratos de chat/API, hay que sincronizar esta guia y handoffs.
