# ADR-0129: Reparacion quality-first con evidence-first cuando la salida final es degradada

- Fecha: 2026-02-25
- Estado: Aprobada

## Contexto
Aun con `rag_status=success`, parte de las respuestas finales quedaban en `quality_status=degraded` por baja relevancia/accionabilidad.

## Decision
1. En `ClinicalChatService`, despues de calcular quality metrics, si:
   - `response_mode=clinical`
   - `quality_status=degraded`
   - hay evidencia RAG disponible
   entonces se reemplaza la respuesta por `evidence-first` y se recalculan metricas.
2. Se agrega traza: `quality_repair_applied=evidence_first_from_degraded`.
3. Se suben defaults de calidad en entorno:
   - `CLINICAL_CHAT_RAG_ENABLE_GATEKEEPER=true`
   - `CLINICAL_CHAT_RAG_CONTEXT_MIN_RATIO=0.12`
   - `CLINICAL_CHAT_LLM_REWRITE_ENABLED=true`

## Consecuencias
- Mejora groundedness/context relevance al anclar salida en snippets internos.
- Se sacrifica algo de estilo libre a favor de auditabilidad y seguridad clinica.

## Validacion requerida
- Test e2e de reparacion quality-first.
- Benchmark comparativo pre/post con mismo dataset de 5 queries.
