# ADR-0150: RAG Extractivo Coarse-to-Fine Accionable

## Estado

Aprobado

## Contexto

Las respuestas extractivas incluian fragmentos heterogeneos y en ocasiones poco
accionables pese a tener evidencia relevante en la base documental.

## Decision

Se implementa pipeline de seleccion de frases en 3 etapas dentro de
`RAGOrchestrator._build_extractive_answer`:

1. Relevancia a consulta (query overlap + score de retrieval).
2. Evidencia accionable (terminos clinicos operativos y señales numericas).
3. Centralidad y diversidad (score de centralidad + MMR ligero).

Adicionalmente, se mantienen filtros de ruido documental y tecnico.

## Consecuencias

- Respuestas mas coherentes y cercanas a un plan operativo util.
- Menor redundancia entre bullets.
- Mantenimiento simple sin dependencia adicional de modelos generativos.
