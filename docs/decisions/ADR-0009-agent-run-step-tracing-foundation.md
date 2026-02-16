# ADR-0009: Fundacion de AgentRun y AgentStep para trazabilidad

## Contexto

Queremos evolucionar el proyecto hacia sistemas de agentes productivos.
Para eso, no basta con devolver respuestas: necesitamos registrar como decidio el agente, en que paso, con que entrada/salida y si uso fallback.

## Decision

Implementar una base de ejecucion agente con dos entidades:

- `AgentRun`: estado global de una corrida de workflow.
- `AgentStep`: traza por paso con `input/output/decision/fallback/error`.

Exponer endpoint inicial:

- `POST /api/v1/agents/run`

Flujo de trabajo inicial soportado:

- `task_triage_v1`

## Consecuencias

Beneficios:

- Base fuerte para testing/evaluation de agentes.
- Depuracion clara de fallos por paso.
- Preparado para coste/latencia por workflow y por paso.

Costes:

- Mas tablas y complejidad de persistencia.
- Necesidad de definir politicas de retencion de trazas en fases futuras.

## Validacion

- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_agents_api.py`




