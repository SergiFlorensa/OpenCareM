# TM-042: Contexto de operaciones clinicas de urgencias (ES)

## Por que se integra ahora

Acabamos de cerrar el ciclo:

- triaje de `CareTask`,
- aprobacion humana,
- trazabilidad completa.

El siguiente paso logico es darle al sistema un vocabulario realista de urgencias.
Sin eso, los agentes y tests se quedan en ejemplos inventados.

## Que se ha integrado

Se crea API de consulta de contexto:

- `GET /api/v1/clinical-context/resumen`
- `GET /api/v1/clinical-context/areas`
- `GET /api/v1/clinical-context/circuitos`
- `GET /api/v1/clinical-context/roles`
- `GET /api/v1/clinical-context/procedimientos`
- `GET /api/v1/clinical-context/procedimientos/{clave}`
- `GET /api/v1/clinical-context/estandares`

## Contenido modelado

### 1) Areas y ubicaciones operativas

- Consultas/Intermedios: 14
- Camas monitorizadas: 31 (4 aislamiento)
- Observacion: 18 (objetivo maximo 36h)
- Sillones: 16
- Zonas de seguridad: roja/contaminada y verde/limpia

### 2) Circuitos de triaje operativo

- Circuito 1 (ambulantes)
  - Reglas de entrada y acciones tempranas de seguridad.
- Circuito 2 (encamados)
  - Priorizacion de traslado y destino monitorizado/observacion.

### 3) Roles operativos

- Celador
- Enfermeria/TCAE
- Medico de apoyo
- Admision

Cada rol incluye responsabilidades y permisos sugeridos para evolucionar RBAC.

### 4) Checklists de procedimientos

- Montaje del sistema LUCAS
- Test de elevacion pasiva de piernas (PRL)

Se guardan como secuencia de pasos reutilizable por AgentSteps.

### 5) Estandares de seguimiento

- Objetivo de tiempo de episodio en urgencias.
- Estancia maxima en observacion.
- Numero de variables base para modelos predictivos de ingreso.

## Como usarlo en IA/agentes

1. Prompt de sistema:
   - Inyectar `resumen`, `circuitos` y `estandares`.
2. Reglas de triaje:
   - Mapear sintomas/contexto operativo a circuito recomendado.
3. Auditoria:
   - Comparar tiempos reales vs estandares de referencia.
4. Frontend:
   - Mostrar catalogos y checklist sin hardcodear en la UI.

## Limites de seguridad

- Este contexto es operacional, no diagnostico.
- No sustituye protocolos oficiales del centro sanitario.
- No sustituye criterio clinico profesional.
- Sirve para entrenamiento, simulacion y soporte de flujo.

## Validacion ejecutada

- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_context_api.py`

Resultado:

- `5 passed`
