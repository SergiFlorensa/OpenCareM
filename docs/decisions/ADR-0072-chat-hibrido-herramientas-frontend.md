# ADR-0072: Chat hibrido con herramientas en frontend

- Fecha: 2026-02-15
- Estado: Aprobado

## Contexto

El MVP inicial permitia trazabilidad clinica, pero la experiencia de uso no era
suficientemente intuitiva para flujo real de urgencias. Ademas, el motor de chat
respondia siempre en formato operativo estricto, incluso para consultas no
clinicas.

## Decision

Adoptar un modelo hibrido:

1. Frontend con selector de herramientas y modo conversacional.
2. Backend con deteccion automatica de modo de respuesta (`general`/`clinical`)
   usando:
   - señales clinicas en la consulta,
   - palabras clave de dominios,
   - herramienta seleccionada.
3. Mantener la seguridad existente:
   - whitelist web estricta,
   - advertencia no diagnostica en flujo clinico.

## Consecuencias

### Positivas

- Mejor UX para profesionales: flujo tipo asistente moderno con controles claros.
- Conversacion libre posible sin romper el soporte clinico.
- Trazabilidad reforzada para auditoria (`response_mode`, `tool_mode`).

### Riesgos

- Mayor complejidad en front-end y en logica de decision del chat.
- Riesgo de expectativas altas en modo general sin modelo generativo dedicado.

## Mitigaciones

- Mantener trazas interpretables en cada respuesta.
- Forzar uso de fuentes seguras en `deep_search`.
- Evolucion futura a streaming y motores generativos especializados.

## Validacion

- `cd frontend && npm run build`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k chat`
