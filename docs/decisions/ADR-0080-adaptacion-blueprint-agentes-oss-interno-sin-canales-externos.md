# ADR-0080: Adaptacion de blueprint de agentes OSS interno sin canales externos

## Contexto

El equipo quiere adoptar patrones de producto basados en agentes para mejorar
calidad, trazabilidad y operacion del software, pero sin introducir
complejidad no prioritaria:

- sin suscripciones/billing por token,
- sin app movil,
- sin integraciones con mensajeria externa.

Adicionalmente, faltaba una base unificada de scripts operativos y hooks de
calidad sobre staged files para acelerar contribucion sin degradar higiene.

## Decision

1. Mantener el foco en arquitectura y logica de agentes dentro del backend y
   frontend web actual.
2. Excluir de alcance roadmap de suscripciones, mobile y canales externos.
3. Estandarizar flujo operativo local con:
   - `scripts/dev_workflow.ps1` (`dev`, `build`, `check`, `test`, `test-e2e`).
   - `scripts/setup_hooks.ps1` para onboarding y setup de hooks.
   - `.pre-commit-config.yaml` para staged files en Python.
4. Formalizar el recorte y la adopcion en documentacion:
   - `docs/94_chat_clinico_operativo_ollama_local_runbook.md`
   - `docs/96_adaptacion_blueprint_agentes_oss_interno.md`
   - contratos compartidos y tablero TM-109.

## Consecuencias

Positivas:

- Menos friccion para contribuir con un flujo operativo unico.
- Mejor higiene de commits por hooks automatizados en staged files.
- Direccion tecnica mas clara: foco en core de agentes y calidad interna.

Costes:

- Requiere onboarding del equipo para usar `setup_hooks`.
- Hay que mantener sincronizadas guias, contratos y scripts en cada cambio.

## Validacion

- `python -m pre_commit validate-config`
- `powershell -ExecutionPolicy Bypass -File scripts/dev_workflow.ps1 -Action check`
- `powershell -ExecutionPolicy Bypass -File scripts/dev_workflow.ps1 -Action test-e2e`
