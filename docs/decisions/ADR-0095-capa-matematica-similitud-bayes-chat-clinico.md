# ADR-0095: Capa Matematica de Similitud y Bayes en Chat Clinico

- Fecha: 2026-02-22
- Estado: Aprobado

## Contexto

El chat clinico ya incorporaba enrutado por dominio, logica formal, contratos por
especialidad y RAG local. Faltaba una capa matematica explicable y ligera para:

- cuantificar cercania consulta-dominio,
- priorizar riesgo operativo con una senal numerica estable,
- dejar trazabilidad auditable sin depender de servicios de pago.

## Decision

Se integra `ClinicalMathInferenceService` en el flujo de chat clinico con:

- similitud por producto interno normalizado (coseno),
- penalizacion de ruido por distancia L2,
- combinacion de likelihood local por dominio (`0.75*cos + 0.25*(1/(1+L2))`),
- actualizacion Bayes simplificada para obtener posterior por dominio,
- score operativo derivado por probabilidad top (`high|medium|low`).

Sin cambios de endpoint y sin cambios de esquema.

## Consecuencias

### Positivas

- Mayor interpretabilidad de la decision de dominio (`math_*`).
- Señal cuantitativa reproducible para priorizacion.
- Costo computacional bajo y ejecucion 100% local.

### Riesgos

- Capa basada en prototipos de palabras clave: requiere mantenimiento por dominio.
- Si la consulta es demasiado corta o ambigua, el posterior puede ser poco separable.

## Validacion

- `.\venv\Scripts\python.exe -m ruff check app/services/clinical_math_inference_service.py app/services/clinical_chat_service.py app/services/__init__.py app/tests/test_clinical_chat_operational.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "math_inference_service"`
