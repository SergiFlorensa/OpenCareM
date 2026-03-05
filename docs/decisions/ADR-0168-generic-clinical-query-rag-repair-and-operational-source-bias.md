# ADR-0168: Reparacion de RAG extractivo degradado y sesgo a fuente operativa en consultas clinicas genericas

## Contexto

Se observaron respuestas de chat con formato `RAG extractivo` que recuperaban fragmentos
especificos de `docs/pdf_raw` para consultas clinicas genericas y operativas, por ejemplo
`Paciente con dolor abdominal: datos clave y escalado`.

El problema no era solo de dominio. El pipeline podia:

- recuperar chunks correctos a nivel de especialidad (`gastro_hepato`),
- seleccionar como frase top un fragmento demasiado especifico de un PDF,
- y publicar ese extractivo sin pasar a una reparacion `evidence_first`, aunque la respuesta
  fuese degradada respecto a la intencion real de la consulta.

## Decision

Se introducen tres ajustes coordinados:

1. En el fallback extractivo del RAG se aplica un sesgo adicional por tipo de fuente y por
   intencion de consulta:
   - se favorecen motores operativos y secciones con marcadores de accion clinica,
   - se penalizan PDFs `pdf_raw` cuando la consulta es generica-operativa y el metadato de
     fuente no aporta foco suficiente.
2. El orden de priorizacion de fuentes internas pasa a favorecer `docs/*.md` operativos frente a
   `docs/pdf_raw/*` cuando el score es comparable.
3. Las respuestas `RAG extractivo` degradadas ya pueden repararse mediante
   `evidence_first`, en lugar de quedar excluidas por empezar con `Resumen operativo...`.

## Consecuencias

### Positivas

- Menos respuestas clinicamente inadecuadas para consultas sintomaticas genericas.
- Mejor alineacion entre la intencion del usuario y el tipo de documento recuperado.
- Mejor uso de los motores operativos ya presentes en el repositorio.

### Riesgos

- Una consulta muy corta pero realmente orientada a una entidad especifica podria necesitar
  mas señal lexical para no perder prioridad frente al motor operativo.
- El sesgo a fuente operativa no sustituye al reranking semantico ni a la necesidad de
  mejorar chunking/indexacion en PDFs largos.

## Validacion

- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py -k "generic_symptom_query or operational_docs_over_pdf"`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "extractive_rag_answer_with_evidence_first"`
