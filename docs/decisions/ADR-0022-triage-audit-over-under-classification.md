# ADR-0022: Auditoria canonica de over/under-triage

- Estado: aceptado
- Fecha: 2026-02-11

## Contexto

El sistema ya permite:

- triaje asistido por IA,
- validacion humana del resultado.

Faltaba un mecanismo explicito para medir desvio entre ambos y operar calidad.

## Decision

Agregar `care_task_triage_audit_logs` con clasificacion estandar:

- `match`
- `under_triage`
- `over_triage`

Y exponer API/metricas para consulta y observabilidad.

## Regla adoptada

Dado que Manchester usa `1` como mayor urgencia:

- `ai > humano` => `under_triage`
- `ai < humano` => `over_triage`

## Consecuencias

Positivas:

- Permite medir seguridad operacional del copiloto.
- Facilita alertas y mejora continua de prompts/modelos.
- Crea base objetiva para revisiones clinicas y QA.

Riesgos:

- Nivel IA puede venir por mapeo de prioridad cuando no haya `triage_level` explicito.

Mitigacion:

- Mantener mapeo documentado y versionado.
- Evolucionar a `triage_level` nativo en workflows siguientes.
