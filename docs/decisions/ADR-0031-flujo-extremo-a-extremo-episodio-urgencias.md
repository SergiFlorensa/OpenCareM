# ADR-0031: Flujo Extremo-a-Extremo de Episodio de Urgencias

## Estado

Aprobado

## Contexto

El sistema tenia motores por modulo (sepsis, medico-legal, screening, etc.)
pero faltaba una estructura unificada para representar el proceso completo
de urgencias desde llegada hasta cierre del episodio.

## Decision

Crear el recurso `EmergencyEpisode` con:

- etapas del flujo operativo,
- transiciones validadas por reglas de negocio,
- timestamps de hitos,
- endpoint de KPIs de tiempos.

## Consecuencias

### Positivas

- estandariza proceso extremo-a-extremo,
- habilita analitica de tiempos por etapa,
- facilita auditoria operativa y mejora continua.

### Riesgos / Costes

- mayor complejidad de estado y validaciones,
- necesidad de gobernar bien etapas para no divergir del proceso real.

## Validacion

- tests de happy-path completo,
- tests de transicion invalida y reglas obligatorias,
- regresion completa de `app/tests`.
