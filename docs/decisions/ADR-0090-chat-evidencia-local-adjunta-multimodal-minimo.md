# ADR-0090: Chat Clinico con Evidencia Local Adjunta (Multimodal Minimo)

- Fecha: 2026-02-22
- Estado: Aprobado

## Contexto

El chat clinico necesitaba incorporar evidencia local del caso (informes, PDF, imagen con metadatos, bloques EHR) sin depender de APIs externas ni servicios de pago.

## Decision

Se extiende el request de chat con `local_evidence` (max 5 items) y se integra esa evidencia en el turno como fuentes internas de alta prioridad.

Cada item permite:

- `title`
- `modality` (`note|report|pdf|image|ehr_structured|lab_panel`)
- `source`
- `content`
- `metadata`

La evidencia se:

- sanea con `ExternalContentSecurity`,
- incorpora a `knowledge_sources` como `type=local_evidence`,
- refleja en `extracted_facts` (`evidencia_local:<modalidad>`),
- queda auditada en `interpretability_trace` (`local_evidence_items`, `local_evidence_modalities`).

## Consecuencias

### Positivas

- Mejora grounding de respuestas con evidencia del caso real.
- Permite flujo "multimodal minimo" en local, sin nuevo esquema DB.
- Trazabilidad completa para auditoria clinica.

### Riesgos

- Si el contenido adjunto es pobre, puede introducir ruido contextual.
- No procesa pixeles ni DICOM en esta fase; solo texto/metadatos.

## Validacion

- `.\venv\Scripts\python.exe -m ruff check app/schemas/clinical_chat.py app/services/clinical_chat_service.py app/tests/test_clinical_chat_operational.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "local_evidence or psychology or interrogatory"`
