# ADR-0017: Pivot de dominio a Clinical Ops Copilot

## Estado

Aceptada

## Contexto

El proyecto crecio como `API Gestor de Tareas` y ahora necesita una direccion de producto mas cercana a casos reales de alto valor.

Se busca evolucionar hacia operaciones clinicas asistidas por agentes, manteniendo seguridad, trazabilidad y observabilidad.

## DecisiÃ³n

Adoptar un pivot incremental a `Clinical Ops Copilot`:

- Mantener compatibilidad de `Task` en corto plazo.
- Introducir `CareTask` como recurso paralelo.
- Aplicar limites de dominio: sistema operativo, no diagnostico.
- Priorizar estandares e interoperabilidad en fases futuras (FHIR/SMART).

## Consecuencias

Positivas:

- Reduce riesgo de ruptura en clientes actuales.
- Permite aprendizaje progresivo con entregas pequenas.
- Mantiene base tecnica ya validada (auth, agents, metrics, alerts).

Negativas:

- Incrementa complejidad temporal por coexistencia de dos modelos.
- Exige disciplina documental para evitar deriva semantica.

## Plan de rollout

1. Fase 1: contratos, roadmap y guia didactica.
2. Fase 2: modelo `CareTask` + migracion Alembic.
3. Fase 3: endpoints y pruebas de regresion.
4. Fase 4: frontend de operaciones y trazas.



