"""
GUÍA DE INTEGRACIÓN: Inyectar RAG en clinical_chat_service.py

Este archivo muestra cómo integrar el RAG Orchestrator en create_message().

UBICACIÓN: Reemplazar líneas 1296-1310 en app/services/clinical_chat_service.py

ANTES (actual):
    llm_answer, llm_trace = LLMChatProvider.generate_answer(
        query=safe_query,
        response_mode=response_mode,
        ... (resto de parámetros)
    )

DESPUÉS (con RAG):
    # Importar al inicio del archivo:
    # from app.services.rag_orchestrator import RAGOrchestrator
    # from app.core.config import settings

    llm_answer = None
    llm_trace = {}

    if settings.RAG_ENABLED:
        # Usar RAG si está habilitado
        try:
            orchestrator = RAGOrchestrator(db=db)
            llm_answer, rag_trace = orchestrator.process_query_with_rag(
                query=safe_query,
                response_mode=response_mode,
                effective_specialty=effective_specialty,
                tool_mode=tool_mode,
                matched_domains=matched_domains,
                memory_facts_used=memory_facts_used,
                patient_summary=patient_summary,
                patient_history_facts_used=patient_history_facts_used,
                knowledge_sources=knowledge_sources,
                web_sources=web_sources,
                recent_dialogue=recent_dialogue,
                endpoint_results=endpoint_recommendations,
                care_task_id=care_task.id,
            )
            llm_trace.update(rag_trace)

            # Si RAG falla, fallback a LLMChatProvider
            if not llm_answer:
                llm_answer, llm_secondary_trace = LLMChatProvider.generate_answer(
                    query=safe_query,
                    response_mode=response_mode,
                    effective_specialty=effective_specialty,
                    tool_mode=tool_mode,
                    matched_domains=matched_domains,
                    matched_endpoints=matched_endpoints,
                    memory_facts_used=memory_facts_used,
                    patient_summary=patient_summary,
                    patient_history_facts_used=patient_history_facts_used,
                    knowledge_sources=knowledge_sources,
                    web_sources=web_sources,
                    recent_dialogue=recent_dialogue,
                    endpoint_results=endpoint_recommendations,
                )
                llm_trace.update(llm_secondary_trace)
        except Exception as e:
            # Si RAG lanza excepción, fallback silencioso
            logger.warning(f"RAG failed, falling back to LLMChatProvider: {e}")
            llm_answer, llm_trace = LLMChatProvider.generate_answer(
                query=safe_query,
                response_mode=response_mode,
                effective_specialty=effective_specialty,
                tool_mode=tool_mode,
                matched_domains=matched_domains,
                matched_endpoints=matched_endpoints,
                memory_facts_used=memory_facts_used,
                patient_summary=patient_summary,
                patient_history_facts_used=patient_history_facts_used,
                knowledge_sources=knowledge_sources,
                web_sources=web_sources,
                recent_dialogue=recent_dialogue,
                endpoint_results=endpoint_recommendations,
            )
    else:
        # Si RAG está deshabilitado, usar LLMChatProvider directamente
        llm_answer, llm_trace = LLMChatProvider.generate_answer(
            query=safe_query,
            response_mode=response_mode,
            effective_specialty=effective_specialty,
            tool_mode=tool_mode,
            matched_domains=matched_domains,
            matched_endpoints=matched_endpoints,
            memory_facts_used=memory_facts_used,
            patient_summary=patient_summary,
            patient_history_facts_used=patient_history_facts_used,
            knowledge_sources=knowledge_sources,
            web_sources=web_sources,
            recent_dialogue=recent_dialogue,
            endpoint_results=endpoint_recommendations,
        )

PASOS A SEGUIR:

1. Agregar imports al inicio de clinical_chat_service.py:
   from app.services.rag_orchestrator import RAGOrchestrator

2. Reemplazar el bloque LLMChatProvider.generate_answer() (líneas 1296-1310)
   con el código DESPUÉS mostrado arriba

3. Ejecutar migraciones:
   alembic upgrade head

4. Actualizar .env:
   RAG_ENABLED=true
   RAG_CHUNK_SIZE_TOKENS=384
   RAG_EMBEDDINGS_MODEL=nomic-embed-text

5. Ingestar documentos:
   python -m app.scripts.ingest_clinical_docs

6. Prueba funcional:
   curl -X POST http://localhost:8000/api/v1/care-tasks/1/chat/messages ...
"""
