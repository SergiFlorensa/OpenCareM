# ADR-0021: Catalogo canonico Manchester para prioridad y SLA

- Estado: aceptado
- Fecha: 2026-02-11

## Contexto

Para evolucionar a SHORT/START/META y auditoria de over/under-triage,
necesitamos primero una referencia estable de niveles de prioridad.

## Decision

Definir `TriageLevel` como recurso canonico y exponer:

- `GET /api/v1/clinical-context/triage-levels/manchester`

con 5 niveles, color y SLA objetivo en minutos.

## Consecuencias

Positivas:

- Unifica lenguaje entre API, agentes, UI y QA.
- Facilita medicion de cumplimiento por tiempos.
- Reduce ambiguedad en reglas futuras de enrutamiento.

Riesgos:

- Si el centro usa parametros distintos, requerira versionado por sede.

Mitigacion:

- Mantener este catalogo como baseline `urgencias_es_v1`.
- Versionar futuras variantes por hospital/servicio.
