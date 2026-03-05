# ADR-0173: Recuperacion clinica neutra para consultas genericas

## Contexto

Una vez aislado correctamente el canal del turno actual, persistia otro problema: para consultas clinicas genericas dentro de un dominio correcto, el sistema seguia seleccionando subbloques demasiado especificos del motor operativo.

Ejemplo:

- consulta: `Paciente con dolor abdominal: datos clave y escalado`
- dominio correcto: `gastro_hepato`
- salida no deseada: `diverticulitis`, `hernia crural`, `colecistectomia`

El fallo ya no era mezcla entre canales, sino exceso de especificidad dentro del mismo canal.

## Decision

Se introducen heuristicas de neutralidad clinica en dos capas:

1. `ClinicalChatService._build_catalog_knowledge_sources(...)`
   - para consultas genericas-operativas:
     - penaliza marcadores de subdiagnostico concreto (`diverticul*`, `hernia crural`, `colecistect*`, `colestasis`, etc.),
     - bonifica chunks neutros con `constantes`, `signos de alarma`, `exploracion abdominal`, `signos peritoneales`, `analitica`, `imagen`, `reevaluacion`, `escalado`.

2. `RAGOrchestrator._build_extractive_answer(...)`
   - cuando la query es generica y no contiene esos marcadores especificos:
     - reduce score de frases centradas en subdiagnosticos concretos,
     - aumenta score de frases tipo checklist o evaluacion general.

## Consecuencias

- Las consultas amplias recuperan y sintetizan bloques mas neutros y accionables.
- El sistema evita sobrediagnosticar o anclar un plan a un subtema concreto no pedido por el usuario.
- No cambia el contrato API ni la estructura de almacenamiento.

## Riesgos

- Al ser heuristicas lexicas, pueden infravalorar algun fragmento especifico legitimo si la query es muy corta.
- La calibracion actual esta optimizada para `gastro_hepato`; otros dominios pueden requerir listas de marcadores propias.

## Validacion

- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "neutral_abdominal_chunk or current_turn_keeps_only_current_domain_channel" -o addopts=""`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py -k "over_specific_subdiagnosis_for_generic_abdominal_query or extractive_answer_prefers_operational_doc_for_generic_symptom_query" -o addopts=""`
- `.\venv\Scripts\python.exe -m ruff check app/services/clinical_chat_service.py app/services/rag_orchestrator.py app/tests/test_clinical_chat_operational.py app/tests/test_rag_orchestrator_optimizations.py`
