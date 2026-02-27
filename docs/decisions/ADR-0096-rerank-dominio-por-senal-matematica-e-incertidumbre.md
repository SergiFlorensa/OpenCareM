# ADR-0096: Reordenado de Dominio por Senal Matematica e Incertidumbre

- Fecha: 2026-02-22
- Estado: Aprobado

## Contexto

La capa matematica de TM-133 aportaba trazabilidad, pero no influia en el orden
de dominios usados por el chat. Persistia riesgo de seleccionar rutas no
prioritarias cuando el enrutado por keywords era ambiguo.

## Decision

Se extiende la integracion matematica para:

- reordenar `matched_domains` con `math_top_domain` cuando la confianza supera
  umbral operativo,
- exponer incertidumbre explicita:
  - `margin_top2`
  - `normalized_entropy`
  - `uncertainty_level`
  - `abstention_recommended`
- mantener la logica en modo local sin dependencias de pago.

## Consecuencias

### Positivas

- Mejor coherencia dominio-consulta en casos ambiguos.
- Mayor auditabilidad al distinguir confianza alta vs baja.
- Base directa para activar estrategias de aclaracion/abstencion.

### Riesgos

- Umbrales iniciales pueden requerir ajuste por distribucion real de consultas.
- Riesgo de sesgo por prototipos lexicales si no se curan periodicamente.

## Validacion

- `.\venv\Scripts\python.exe -m ruff check app/services/clinical_math_inference_service.py app/services/clinical_chat_service.py app/tests/test_clinical_chat_operational.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "math_inference_service or domain_rerank_uses_math_top_domain_when_confident"`
