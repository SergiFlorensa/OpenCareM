# ADR-0160: Endurecimiento de Dominio y Preservacion de Respuesta RAG Autoritativa

## Estado

Aprobado

## Contexto

En consultas clinicas reales se observaron dos fallos de calidad:

1. Deriva de dominio por matching fuzzy debil (ej. `lactato` induciendo `lactante` y mezclando
   pediatria con sepsis).
2. Respuestas RAG validas reemplazadas por fallback estructurado evidence-first, perdiendo
   naturalidad conversacional incluso cuando RAG ya habia resuelto la consulta.

El objetivo era corregir ambos problemas sin romper contratos API ni desactivar safeguards de
calidad para respuestas realmente degradadas.

## Decision

1. En `ClinicalChatService._match_domains`:
   - separar scoring de keyword en `direct_score` y `fuzzy_score`,
   - descartar dominios activados solo por fuzzy debil (`fuzzy_score < 2` sin match directo),
   - cuando existe al menos un dominio con match directo, filtrar dominios sin match directo.

2. En ensamblado de respuesta:
   - marcar como `rag_answer_authoritative` solo respuestas RAG con:
     - `rag_status=success`,
     - `rag_validation_status=valid`,
     - sin telemetria `llm_*` en `rag_trace`.
   - evitar `quality_repair -> evidence_first` para ese caso autoritativo.
   - mantener reparacion evidence-first para respuestas no autoritativas o degradadas.

3. En frontend:
   - desactivar `include_protocol_catalog` por defecto para reducir ruido de catalogo en el turno.

## Consecuencias

- Menos mezclas de especialidad por similitud lexical accidental.
- Mejor continuidad conversacional cuando RAG entrega respuesta valida.
- Se mantiene la proteccion de calidad para respuestas pobres/no accionables.
- Sin cambios de schema ni endpoints.

## Validacion

- `./venv/Scripts/python.exe -m ruff check app/services/clinical_chat_service.py app/tests/test_clinical_chat_operational.py`
- `$env:DEBUG='false'; ./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "domain_matching_handles_typo_oftamologia_as_ophthalmology or domain_matching_prioritizes_direct_signal_and_avoids_fuzzy_domain_leak or chat_e2e_uses_rag_when_enabled or chat_e2e_quality_gate_applies_to_rag_answer_too or chat_e2e_fallback_when_rag_validation_warns" -o addopts=""`
- `$env:DEBUG='false'; ./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py -o addopts=""`
- `npm --prefix frontend run build`

## Riesgos pendientes

- El umbral fuzzy puede requerir ajuste con nuevos corpus o jergas locales.
- Algunas salidas RAG con validacion `warning` seguiran cayendo a fallback estructurado por diseño
  de seguridad actual.
