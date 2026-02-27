# ADR-0085: Deteccion clinica automatica robusta y quality gate final

## Estado

Aprobado.

## Contexto

En local aparecian respuestas demasiado genericas para consultas claramente clinicas
(por ejemplo, casos pediatricos febriles), incluso con LLM activo.
Esto degradaba utilidad practica en urgencias y generaba baja confianza operativa.

## Decision

1. Reforzar senales de enrutado clinico en `conversation_mode=auto`:
   - ampliar terminos clinicos base (`pediatrico`, `paciente`, `sospecha`, `febril`, etc.).
2. Aplicar compuerta final de calidad para respuestas clinicas cuando guardrails esta desactivado:
   - si la respuesta final no es accionable/estructurada, forzar fallback clinico determinista.
3. Mantener contrato API estable:
   - sin cambios en request/response.
   - solo se agrega traza interpretativa cuando aplica (`clinical_answer_quality_gate=...`).

## Consecuencias

- Positivas:
  - mejor consistencia de salida en consultas clinicas reales.
  - menos respuestas ambiguas tipo "objetivo clinico..." sin pasos operativos.
  - mejor experiencia en entorno local con hardware limitado.
- Riesgos:
  - en algunos casos limite puede activarse fallback estructurado aunque la respuesta LLM fuese valida pero breve.
  - requiere que clientes toleren nuevas entradas en `interpretability_trace`.

## Validacion

- `.\venv\Scripts\python.exe -m ruff check app/services/clinical_chat_service.py app/tests/test_clinical_chat_operational.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py`
- Tests agregados:
  - `test_auto_mode_detects_clinical_signal_in_pediatric_febrile_query`
  - `test_chat_e2e_forces_structured_fallback_when_llm_answer_is_generic`
