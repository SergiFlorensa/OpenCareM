# ADR-0155: RAG Multi-Intento con Reranking Accionable y Grounding Fino

## Estado

Aprobado

## Contexto

El pipeline RAG del chat clinico tenia buen recall general, pero degradaba en consultas
compuestas (por ejemplo, oncologia + sepsis) y en respuestas con ruido enciclopedico.
Los sintomas principales eran:

- recuperacion plana sin segmentar subintenciones de la consulta;
- mezcla de chunks de dominios vecinos;
- snippets con baja accionabilidad clinica;
- composicion final con citas poco especificas.

Ademas, se necesitaba mejorar precision sin acoplar el cambio a un rollout obligatorio de
embeddings.

## Decision

1. Introducir segmentacion multi-intento configurable antes del retrieval hibrido global:
   - dividir la consulta en segmentos;
   - clasificar cada segmento con `ClinicalSVMDomainService`;
   - ejecutar retrieval por segmento y fusionar resultados deduplicados.
2. Incorporar reranking extractivo por accionabilidad clinica:
   - score combinado de overlap/evidencia/retrieval + densidad de verbos de accion;
   - penalizacion por ratio alto de verbos auxiliares (AUX-like tokens);
   - umbrales configurables para excluir frases poco operativas.
3. Mejorar grounding en composicion final:
   - citas en formato `section + source leaf` para anclaje fino.
4. Endurecer calidad por subdominio:
   - umbrales dinamicos de `answer/context/groundedness` segun dominios detectados.
5. Mantener fuera de alcance cambios funcionales en `embedding_service`:
   - los cambios de embeddings no forman parte de este paquete.

## Consecuencias

- Mejor separacion de intenciones clinicas en casos compuestos.
- Menor probabilidad de respuesta con ruido editorial y mayor foco en acciones.
- Trazabilidad ampliada por nuevas claves `rag_multi_intent_*` y umbrales de calidad.
- Mayor sensibilidad de configuracion: umbrales muy estrictos pueden reducir recall.

## Validacion

- `./venv/Scripts/python.exe -m ruff check app/services/clinical_chat_service.py app/services/rag_orchestrator.py app/core/config.py app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py`
- `$env:DEBUG='false'; ./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py -o addopts=""`
- Resultado: `113 passed`.

## Riesgos pendientes

- Calibracion de umbrales `CLINICAL_CHAT_RAG_ACTION_*` por subdominio en trafico real.
- Dependencia de marcadores lexicales para segmentacion en consultas cortas o ambiguas.
