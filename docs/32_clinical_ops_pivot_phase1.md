# Clinical Ops Pivot - Fase 1

## Objetivo

Mover el proyecto de un `Gestor de Tareas` generico a un enfoque `Clinical Ops Copilot` de forma incremental.

Importante: esta fase NO crea diagnostico medico. Solo organiza, prioriza y traza trabajo operativo.

## Que conseguimos en esta fase

- Mantener lo que ya funciona (`tasks`, `agents`, `auth`, observabilidad).
- Definir lenguaje y estructura para evolucionar a `CareTask`.
- Evitar reescritura grande de golpe.

## Paso a paso (didactico)

1. Congelar la base actual
- No se elimina ningun endpoint existente.
- Se protege la compatibilidad para no romper tests ni clientes.

2. Definir el nuevo vocabulario
- `Task` actual = unidad de trabajo generica.
- `CareTask` futuro = unidad operativa clinica (no diagnostica).
- Diferencia clave: `CareTask` incorpora prioridad clinica operativa y SLA.

3. Preparar contratos antes de codigo
- API contract: que cambia y que no.
- Data contract: nuevos campos planificados.
- Test plan: como sabremos que no rompimos nada.

4. Elegir estrategia de migracion segura
- Primero coexistencia (`Task` y `CareTask` en paralelo).
- Luego migracion gradual de consumidores.
- Al final, decidir deprecacion de `Task` si aplica.

## Primer alcance tecnico aprobado

- Recurso paralelo `CareTask` (fase posterior, no en este documento).
- Campos previstos:
  - `clinical_priority` (`low|medium|high|critical`)
  - `specialty`
  - `sla_target_minutes`
  - `human_review_required`
  - `risk_flags`

## Validacion minima de fase

- La API actual sigue respondiendo igual.
- Los tests de agentes y triage siguen en verde.
- La documentacion refleja el nuevo norte del producto.

## Riesgos y mitigaciones

- Riesgo: mezclar semantica de producto (`Task` vs `CareTask`).
  - Mitigacion: contratos explicitos y rollout por fases.
- Riesgo: intentar ir demasiado rapido.
  - Mitigacion: una entrega por fase con evidencia verificable.

## Siguiente entrega recomendada

Implementar `CareTask` en paralelo (modelo, schema, endpoints v1) sin quitar `Task`.


