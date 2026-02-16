# Guia de Habilidades del Proyecto

Este documento resume el analisis del PDF local y las decisiones para crear skills del proyecto.

## Fuente analizada

- `The-Complete-Guide-to-Building-Skill-for-Claude.pdf` (33 paginas, extraido localmente).
- Guia oficial cargada en entorno: `skill-creator/SKILL.md`.

## Requisitos clave extraidos

1. Frontmatter con `name` + `description` claros.
2. `description` debe explicar:
   - que hace el skill,
   - cuando usarlo (triggers reales).
3. Progressive disclosure:
   - SKILL.md conciso,
   - detalles en `references/`.
4. Evitar documentacion redundante dentro del skill.
5. Validar cada skill con `quick_validate.py`.

## Skills creados

### 1) `tm-orchestrator-workflow`

- Ubicacion: `skills/tm-orchestrator-workflow`
- Uso: orquestar cambios con board + contratos + evidencias + riesgos.

### 2) `tm-api-change-delivery`

- Ubicacion: `skills/tm-api-change-delivery`
- Uso: entregar cambios FastAPI con migraciones, tests y docs alineados.

### 3) `tm-observability-ops`

- Ubicacion: `skills/tm-observability-ops`
- Uso: operar y depurar stack API + Prometheus + Grafana.

## Validacion ejecutada

- `.\venv\Scripts\python.exe .../quick_validate.py skills/tm-orchestrator-workflow`
- `.\venv\Scripts\python.exe .../quick_validate.py skills/tm-api-change-delivery`
- `.\venv\Scripts\python.exe .../quick_validate.py skills/tm-observability-ops`

Resultado: `Skill is valid!` en los 3 casos.

## Como activarlos en Codex

Si quieres que Codex los cargue como skills locales, copia estas carpetas a:

- `C:/Users/SERGI/.codex/skills/`

Ejemplo (PowerShell):

`Copy-Item -Recurse -Force .\skills\tm-* C:\Users\SERGI\.codex\skills\`

Luego reinicia la sesion de Codex CLI para refrescar skills disponibles.

## Riesgos pendientes

- Los skills son rules-first; no invocan tooling externo por si solos.
- Conviene iterarlos con uso real para afinar triggers y reducir over/under-triggering.


