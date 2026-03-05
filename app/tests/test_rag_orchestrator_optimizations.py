from array import array
from types import SimpleNamespace

from app.models.clinical_document import ClinicalDocument
from app.models.document_chunk import DocumentChunk
from app.services.rag_orchestrator import RAGOrchestrator
from app.services.rag_prompt_builder import RAGContextAssembler


def _vec_bytes(values: list[float]) -> bytes:
    buff = array("f")
    buff.extend(values)
    return buff.tobytes()


def test_adaptive_k_short_query_with_high_risk_marker(monkeypatch):
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_ADAPTIVE_K_ENABLED",
        True,
    )
    monkeypatch.setattr("app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_MAX_CHUNKS", 5)
    monkeypatch.setattr("app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_MIN_CHUNKS", 3)
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_MAX_CHUNKS_HARD",
        12,
    )

    k, trace = RAGOrchestrator._resolve_adaptive_k("K 6.2 con oliguria")

    assert k == 5
    assert trace["rag_adaptive_k_reason"] == "short_query+high_risk_raise_to_base"


def test_adaptive_k_disabled_uses_bounded_base(monkeypatch):
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_ADAPTIVE_K_ENABLED",
        False,
    )
    monkeypatch.setattr("app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_MAX_CHUNKS", 9)
    monkeypatch.setattr("app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_MIN_CHUNKS", 3)
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_MAX_CHUNKS_HARD",
        6,
    )

    k, trace = RAGOrchestrator._resolve_adaptive_k("consulta breve")

    assert k == 6
    assert trace["rag_adaptive_k_enabled"] == "0"
    assert trace["rag_adaptive_k_reason"] == "disabled"


def test_mmr_rerank_prioritizes_diversity(monkeypatch):
    monkeypatch.setattr("app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_MMR_LAMBDA", 0.5)
    orchestrator = RAGOrchestrator(db=SimpleNamespace())

    monkeypatch.setattr(
        orchestrator.legacy_retriever.embedding_service,
        "embed_text",
        lambda text: ([1.0, 0.0], {"embedding_source": "test"}),
    )

    chunk_a = SimpleNamespace(id=1, chunk_embedding=_vec_bytes([1.0, 0.0]), _rag_score=1.0)
    chunk_b = SimpleNamespace(id=2, chunk_embedding=_vec_bytes([1.0, 0.0]), _rag_score=0.2)
    chunk_c = SimpleNamespace(id=3, chunk_embedding=_vec_bytes([0.0, 1.0]), _rag_score=0.3)

    selected, trace = orchestrator._apply_mmr_rerank(
        query="hiperkalemia grave",
        chunks=[chunk_a, chunk_b, chunk_c],
        top_k=2,
    )

    assert [int(getattr(item, "id")) for item in selected] == [1, 3]
    assert trace["rag_mmr_enabled"] == "1"
    assert trace["rag_mmr_selected"] == "2"


def test_context_compression_keeps_overlap_sentences():
    chunks = [
        {
            "id": 10,
            "text": (
                "Texto administrativo sin valor clinico para esta consulta. "
                "En neutropenia febril se debe activar ruta rapida con toma de cultivos y "
                "antibiotico temprano. "
                "Otra frase irrelevante de cierre."
            ),
            "section": "Oncologia > Neutropenia febril",
            "source": "docs/76_motor_operativo_oncologia_urgencias.md",
            "score": 0.8,
        }
    ]

    compressed, trace = RAGContextAssembler.compress_rag_context(
        query="neutropenia febril y antibiotico",
        chunks=chunks,
        max_chars_per_chunk=120,
    )

    assert len(compressed[0]["text"]) <= 120
    assert "neutropenia" in compressed[0]["text"].lower()
    assert trace["rag_context_compressed"] == "1"


def test_extractive_answer_filters_non_clinical_noise():
    answer = RAGOrchestrator._build_extractive_answer(
        query="Oliguria con hiperkalemia y QRS ancho",
        matched_domains=["nephrology"],
        chunks=[
            {
                "text": (
                    "# Motor Operativo de Nefrologia en Urgencias\n"
                    "python.exe -m pytest app/tests/test_x.py\n"
                    "Hiperkalemia con QRS ancho requiere monitorizacion ECG continua y "
                    "tratamiento inmediato."
                ),
                "section": "Nefrologia > Hiperkalemia",
                "source": "docs/73_motor_operativo_nefrologia_urgencias.md",
            }
        ],
    )

    assert answer is not None
    lowered = answer.lower()
    assert "hiperkalemia" in lowered
    assert "pytest" not in lowered
    assert "python.exe" not in lowered
    assert "motor operativo" not in lowered


def test_extractive_answer_prioritizes_query_overlap_over_noise_chunks():
    answer = RAGOrchestrator._build_extractive_answer(
        query="Shock septico con lactato alto y hipotension",
        matched_domains=["sepsis"],
        chunks=[
            {
                "text": "Bloqueo de ganglio impar en dolor perineal cronico refractario.",
                "section": "Paliativos > Dolor perineal",
                "source": "docs/78_motor_operativo_cuidados_paliativos_urgencias.md",
                "score": 0.95,
            },
            {
                "text": (
                    "Shock septico con hipotension y lactato elevado: activar bundle "
                    "inicial, hemocultivos y antibiotico precoz."
                ),
                "section": "Sepsis > Bundle inicial",
                "source": "docs/47_motor_sepsis_urgencias.md",
                "score": 0.35,
            },
        ],
    )

    assert answer is not None
    lowered = answer.lower()
    assert "shock septico" in lowered
    assert "lactato" in lowered


def test_extractive_answer_coarse_to_fine_prefers_actionable_sentences():
    answer = RAGOrchestrator._build_extractive_answer(
        query="Sepsis con hipotension y lactato elevado, pasos iniciales",
        matched_domains=["sepsis"],
        chunks=[
            {
                "text": (
                    "Resumen historico del servicio. "
                    "En sepsis con hipotension y lactato elevado se debe priorizar bundle, "
                    "cultivos y antibiotico precoz en primera hora. "
                    "Texto general administrativo sin accion clinica concreta."
                ),
                "section": "Sepsis > Bundle inicial",
                "source": "docs/47_motor_sepsis_urgencias.md",
                "score": 0.7,
            }
        ],
    )

    assert answer is not None
    lowered = answer.lower()
    assert "bundle" in lowered
    assert "antibiotico" in lowered


def test_query_overlap_log_scaling_rewards_relevant_sentence():
    short_score = RAGOrchestrator._query_overlap_score(
        query_tokens={"sepsis", "lactato"},
        text="Sepsis con lactato elevado y shock.",
    )
    long_score = RAGOrchestrator._query_overlap_score(
        query_tokens={"sepsis", "lactato", "hipotension", "qsofa", "cultivos", "bundle"},
        text="Sepsis con lactato elevado y shock.",
    )
    assert short_score > 0
    assert long_score > 0
    assert short_score >= long_score


def test_generative_proxy_score_prefers_well_formed_sentence():
    query_tokens = {"sepsis", "lactato"}
    good = RAGOrchestrator._generative_proxy_score(
        query_tokens=query_tokens,
        text="En sepsis con lactato alto, iniciar bundle y monitorizacion estrecha.",
    )
    poor = RAGOrchestrator._generative_proxy_score(
        query_tokens=query_tokens,
        text="sepsis lactato",
    )
    assert good > poor


def test_local_coherence_discriminator_prefers_natural_sentence_order():
    ordered = (
        "Sepsis con hipotension y lactato elevado en urgencias. "
        "Por ello se debe activar bundle, extraer hemocultivos e iniciar antibiotico precoz. "
        "Despues reevaluar perfusion y tendencia de lactato."
    )
    shuffled = (
        "Despues reevaluar perfusion y tendencia de lactato. "
        "Sepsis con hipotension y lactato elevado en urgencias. "
        "Por ello se debe activar bundle, extraer hemocultivos e iniciar antibiotico precoz."
    )

    ordered_score = RAGOrchestrator._local_coherence_discriminator_score(ordered)
    shuffled_score = RAGOrchestrator._local_coherence_discriminator_score(shuffled)

    assert ordered_score >= shuffled_score


def test_texttiling_topic_score_prefers_consistent_subtopic_blocks():
    query_tokens = {"sepsis", "lactato", "antibiotico", "bundle"}
    coherent_edus = [
        "Sepsis con lactato elevado y signos de hipoperfusion en urgencias",
        "Activar bundle, extraer hemocultivos e iniciar antibiotico precoz",
        "Reevaluar lactato y perfusion despues de la reanimacion inicial",
    ]
    mixed_edus = [
        "Sepsis con lactato elevado y signos de hipoperfusion en urgencias",
        "Oncologia de mama y receptor HER2 en escenarios ambulatorios",
        "Reevaluar lactato y perfusion despues de la reanimacion inicial",
    ]

    coherent_score = RAGOrchestrator._texttiling_topic_score(
        query_tokens=query_tokens,
        edus=coherent_edus,
    )
    mixed_score = RAGOrchestrator._texttiling_topic_score(
        query_tokens=query_tokens,
        edus=mixed_edus,
    )
    assert coherent_score > mixed_score


def test_lexical_chain_cohesion_score_rewards_medical_chain_density():
    query_tokens = {"sepsis", "lactato", "antibiotico", "cultivos"}
    dense_edus = [
        "Sepsis con lactato y lactatemia elevada en contexto infeccioso",
        "Antibiotico precoz y cultivos en sepsis grave con hipoperfusion",
        "Reevaluacion de lactato y respuesta al bundle de sepsis",
    ]
    sparse_edus = [
        "Documento introductorio con contexto historico general",
        "Descripcion de conceptos sin acciones clinicas operativas",
        "Texto editorial sin campo semantico claro para urgencias",
    ]

    dense_score = RAGOrchestrator._lexical_chain_cohesion_score(
        query_tokens=query_tokens,
        edus=dense_edus,
    )
    sparse_score = RAGOrchestrator._lexical_chain_cohesion_score(
        query_tokens=query_tokens,
        edus=sparse_edus,
    )
    assert dense_score > sparse_score


def test_entity_grid_coherence_prefers_continue_over_shift():
    salient = {"sepsis", "lactato", "hipotension"}
    continue_edus = [
        "Sepsis con hipotension y lactato elevado en la llegada a urgencias",
        "Sepsis con lactato persistente requiere reevaluacion hemodinamica continua",
        "Sepsis refractaria con hipotension demanda escalado vasopresor precoz",
    ]
    shift_edus = [
        "Sepsis con hipotension y lactato elevado en la llegada a urgencias",
        "Trauma toracico cerrado con neumotorax a tension y drenaje",
        "SCASEST de alto riesgo con troponina positiva y ECG dinamico",
    ]

    continue_score = RAGOrchestrator._entity_grid_coherence_score(
        edus=continue_edus,
        salient_entities=salient,
    )
    shift_score = RAGOrchestrator._entity_grid_coherence_score(
        edus=shift_edus,
        salient_entities=salient,
    )
    assert continue_score > shift_score


def test_discourse_rerank_prioritizes_nucleus_action_chunk(monkeypatch):
    orchestrator = RAGOrchestrator(db=SimpleNamespace())
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_DISCOURSE_COHERENCE_ENABLED",
        True,
    )
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_DISCOURSE_MIN_SCORE",
        0.10,
    )
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_DISCOURSE_MAX_SATELLITE_RATIO",
        0.50,
    )
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_DISCOURSE_LCD_MIN_SCORE",
        0.10,
    )

    satellite = SimpleNamespace(
        id=901,
        chunk_text=(
            "Introduccion historica y contexto editorial sobre la evolucion del concepto de sepsis."
        ),
        section_path="Sepsis > Introduccion y contexto",
        _rag_score=0.95,
    )
    nucleus = SimpleNamespace(
        id=902,
        chunk_text=(
            "Sepsis con hipotension y lactato alto: activar bundle, hemocultivos, antibiotico "
            "precoz y reevaluacion hemodinamica."
        ),
        section_path="Sepsis > Protocolo operativo inicial",
        _rag_score=0.55,
    )

    reranked, trace = orchestrator._apply_discourse_coherence_rerank(
        query="Sepsis con lactato alto e hipotension",
        chunks=[satellite, nucleus],
    )

    assert reranked
    assert int(getattr(reranked[0], "id")) == 902
    assert trace["rag_discourse_enabled"] == "1"
    assert trace["rag_discourse_top_role"] == "nucleus"
    assert "rag_discourse_top_texttiling" in trace
    assert "rag_discourse_top_entity_grid" in trace


def test_extractive_answer_adds_dose_safety_note_when_no_numeric_dose_found():
    answer = RAGOrchestrator._build_extractive_answer(
        query="Cual es la dosis de heparina en este contexto?",
        matched_domains=["scasest"],
        chunks=[
            {
                "text": (
                    "En SCASEST con heparina se prioriza monitorizacion, estratificacion de riesgo "
                    "y vigilancia de sangrado."
                ),
                "section": "SCASEST > Ruta inicial",
                "source": "docs/49_motor_scasest_urgencias.md",
                "score": 0.8,
            }
        ],
    )
    assert answer is not None
    assert "No se identifica dosis explicita" in answer


def test_select_retriever_backend_supports_elastic_with_specialty():
    backend, reason = RAGOrchestrator._select_retriever_backend(
        query="Paciente con dolor toracico y troponina positiva",
        specialty_filter="scasest",
        configured_backend="elastic",
    )
    assert backend == "elastic"
    assert reason == "specialty_semantic_priority"


def test_rag_latency_budget_skips_llm_and_uses_extractive_fallback(monkeypatch):
    orchestrator = RAGOrchestrator(db=SimpleNamespace())
    llm_called = {"value": False}

    def fake_llm(**kwargs):  # noqa: ARG001
        llm_called["value"] = True
        return "respuesta llm", {"llm_used": "true"}

    monkeypatch.setattr(
        "app.services.rag_orchestrator.LLMChatProvider.generate_answer",
        fake_llm,
    )
    monkeypatch.setattr("app.services.rag_orchestrator.settings.CLINICAL_CHAT_LLM_ENABLED", True)
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_FORCE_EXTRACTIVE_ONLY",
        False,
    )
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_MAX_TOTAL_LATENCY_MS",
        1,
    )
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_LLM_MIN_REMAINING_BUDGET_MS",
        900,
    )
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_EXTRACTIVE_FALLBACK_ENABLED",
        True,
    )
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_EXTRACTIVE_FALLBACK_MAX_ITEMS",
        2,
    )

    chunk = SimpleNamespace(
        id=101,
        chunk_text=(
            "Hiperkalemia con QRS ancho requiere monitorizacion ECG continua, "
            "calcio IV y medidas de desplazamiento transcelular."
        ),
        section_path="Nefrologia > Hiperkalemia",
        tokens_count=42,
        keywords=[],
        custom_questions=[],
        specialty="nephrology",
        content_type="markdown",
        _rag_score=0.9,
        document=SimpleNamespace(source_file="docs/73_motor_operativo_nefrologia_urgencias.md"),
    )

    monkeypatch.setattr(
        orchestrator,
        "_resolve_adaptive_k",
        lambda query: (1, {"rag_adaptive_k_enabled": "0"}),
    )
    monkeypatch.setattr(
        orchestrator,
        "_search_with_configured_backend",
        lambda query, k, specialty_filter: (
            [chunk],
            {"vector_search_latency_ms": "1"},
            "hybrid",
        ),
    )

    answer, trace = orchestrator.process_query_with_rag(
        query="Oliguria con hiperkalemia y QRS ancho",
        response_mode="clinical",
        effective_specialty="nephrology",
        matched_domains=[],
    )

    assert llm_called["value"] is False
    assert answer is not None
    assert trace["rag_status"] == "success"
    assert trace["rag_generation_mode"] == "extractive_fallback_llm_error"
    assert trace["rag_llm_skipped_reason"] == "latency_budget_exhausted_pre_llm"


def test_early_goal_test_returns_extractive_answer_without_llm(monkeypatch):
    orchestrator = RAGOrchestrator(db=SimpleNamespace())
    llm_called = {"value": False}

    def fake_llm(**kwargs):  # noqa: ARG001
        llm_called["value"] = True
        return "respuesta llm", {"llm_used": "true"}

    monkeypatch.setattr(
        "app.services.rag_orchestrator.LLMChatProvider.generate_answer",
        fake_llm,
    )
    monkeypatch.setattr("app.services.rag_orchestrator.settings.CLINICAL_CHAT_LLM_ENABLED", True)
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_SAFE_WRAPPER_ENABLED",
        False,
    )
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_EARLY_GOAL_TEST_ENABLED",
        True,
    )
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_FACT_ONLY_MODE_ENABLED",
        True,
    )
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_EARLY_GOAL_MIN_SCORE",
        0.1,
    )
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_EARLY_GOAL_MIN_ACTIONABILITY",
        0.1,
    )
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_EARLY_GOAL_MIN_RETRIEVAL_SCORE",
        0.1,
    )
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_QUERY_CACHE_ENABLED",
        False,
    )

    chunk = SimpleNamespace(
        id=501,
        chunk_text=(
            "Sepsis con hipotension y lactato elevado: activar bundle, hemocultivos y "
            "antibiotico precoz en la primera hora."
        ),
        section_path="Sepsis > Bundle inicial",
        tokens_count=28,
        keywords=[],
        custom_questions=[],
        specialty="sepsis",
        content_type="markdown",
        _rag_score=0.92,
        document=SimpleNamespace(source_file="docs/47_motor_sepsis_urgencias.md"),
    )
    monkeypatch.setattr(
        orchestrator,
        "_resolve_adaptive_k",
        lambda query: (1, {"rag_adaptive_k_enabled": "0"}),
    )
    monkeypatch.setattr(
        orchestrator,
        "_search_with_configured_backend",
        lambda query, k, specialty_filter: (
            [chunk],
            {"vector_search_latency_ms": "2"},
            "hybrid",
        ),
    )

    answer, trace = orchestrator.process_query_with_rag(
        query="Sepsis con lactato alto e hipotension, pasos iniciales",
        response_mode="clinical",
        effective_specialty="sepsis",
        matched_domains=[],
    )

    assert answer is not None
    assert llm_called["value"] is False
    assert trace["rag_generation_mode"] == "early_goal_extractive"
    assert trace["rag_early_goal_triggered"] == "1"
    assert trace["llm_used"] == "false"


def test_query_cache_exact_hit_avoids_second_retrieval(monkeypatch):
    orchestrator = RAGOrchestrator(db=SimpleNamespace())
    retrieval_calls = {"value": 0}

    monkeypatch.setattr("app.services.rag_orchestrator.settings.CLINICAL_CHAT_LLM_ENABLED", False)
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_SAFE_WRAPPER_ENABLED",
        False,
    )
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_QUERY_CACHE_ENABLED",
        True,
    )
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_QUERY_CACHE_TTL_SECONDS",
        300,
    )
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_QUERY_CACHE_MAX_ENTRIES",
        256,
    )
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_EARLY_GOAL_TEST_ENABLED",
        True,
    )
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_FACT_ONLY_MODE_ENABLED",
        True,
    )
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_EARLY_GOAL_MIN_SCORE",
        0.1,
    )
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_EARLY_GOAL_MIN_ACTIONABILITY",
        0.1,
    )
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_EARLY_GOAL_MIN_RETRIEVAL_SCORE",
        0.1,
    )

    chunk = SimpleNamespace(
        id=601,
        chunk_text="Hiperkalemia con QRS ancho: administrar calcio IV y monitorizar ECG.",
        section_path="Nefrologia > Hiperkalemia",
        tokens_count=16,
        keywords=[],
        custom_questions=[],
        specialty="nephrology",
        content_type="markdown",
        _rag_score=0.88,
        document=SimpleNamespace(source_file="docs/73_motor_operativo_nefrologia_urgencias.md"),
    )

    def fake_search(query, k, specialty_filter):  # noqa: ARG001
        retrieval_calls["value"] += 1
        return [chunk], {"vector_search_latency_ms": "2"}, "hybrid"

    monkeypatch.setattr(orchestrator, "_search_with_configured_backend", fake_search)

    first_answer, first_trace = orchestrator.process_query_with_rag(
        query="Hiperkalemia con QRS ancho en urgencias",
        response_mode="clinical",
        effective_specialty="nephrology",
        matched_domains=[],
    )
    second_answer, second_trace = orchestrator.process_query_with_rag(
        query="Hiperkalemia con QRS ancho en urgencias",
        response_mode="clinical",
        effective_specialty="nephrology",
        matched_domains=[],
    )

    assert first_answer is not None
    assert second_answer is not None
    assert first_trace["rag_query_cache_hit"] == "0"
    assert second_trace["rag_query_cache_hit"] == "1"
    assert second_trace["rag_query_cache_hit_type"] == "exact"
    assert retrieval_calls["value"] == 1


def test_query_cache_subset_pruning_reuses_resolvable_state(monkeypatch):
    orchestrator = RAGOrchestrator(db=SimpleNamespace())
    retrieval_calls = {"value": 0}

    monkeypatch.setattr("app.services.rag_orchestrator.settings.CLINICAL_CHAT_LLM_ENABLED", False)
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_SAFE_WRAPPER_ENABLED",
        False,
    )
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_QUERY_CACHE_ENABLED",
        True,
    )
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_QUERY_CACHE_TTL_SECONDS",
        300,
    )
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_QUERY_CACHE_MAX_ENTRIES",
        256,
    )
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_EARLY_GOAL_TEST_ENABLED",
        True,
    )
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_EARLY_GOAL_MIN_SCORE",
        0.1,
    )
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_EARLY_GOAL_MIN_ACTIONABILITY",
        0.1,
    )
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_EARLY_GOAL_MIN_RETRIEVAL_SCORE",
        0.1,
    )

    chunk = SimpleNamespace(
        id=701,
        chunk_text=(
            "Shock septico con lactato elevado e hipotension: activar bundle inicial, "
            "hemocultivos y antibiotico precoz."
        ),
        section_path="Sepsis > Bundle inicial",
        tokens_count=22,
        keywords=[],
        custom_questions=[],
        specialty="sepsis",
        content_type="markdown",
        _rag_score=0.91,
        document=SimpleNamespace(source_file="docs/47_motor_sepsis_urgencias.md"),
    )

    def fake_search(query, k, specialty_filter):  # noqa: ARG001
        retrieval_calls["value"] += 1
        return [chunk], {"vector_search_latency_ms": "2"}, "hybrid"

    monkeypatch.setattr(orchestrator, "_search_with_configured_backend", fake_search)

    first_answer, _ = orchestrator.process_query_with_rag(
        query="Shock septico con lactato alto e hipotension refractaria, bundle inicial",
        response_mode="clinical",
        effective_specialty="sepsis",
        matched_domains=[],
    )
    second_answer, second_trace = orchestrator.process_query_with_rag(
        query="Shock lactato alto",
        response_mode="clinical",
        effective_specialty="sepsis",
        matched_domains=[],
    )

    assert first_answer is not None
    assert second_answer is not None
    assert second_trace["rag_query_cache_hit"] == "1"
    assert second_trace["rag_query_cache_hit_type"] == "subset_prune"
    assert second_trace["rag_belief_state_pruned"] == "1"
    assert retrieval_calls["value"] == 1


def test_domain_search_is_skipped_when_query_is_long(monkeypatch):
    orchestrator = RAGOrchestrator(db=SimpleNamespace())

    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_SKIP_DOMAIN_SEARCH_TOKENS_OVER",
        1,
    )
    monkeypatch.setattr("app.services.rag_orchestrator.settings.CLINICAL_CHAT_LLM_ENABLED", False)
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_EXTRACTIVE_FALLBACK_ENABLED",
        True,
    )

    def fail_domain_search(*args, **kwargs):  # noqa: ARG001
        raise AssertionError("domain search should have been skipped")

    monkeypatch.setattr(orchestrator.legacy_retriever, "search_by_domain", fail_domain_search)

    chunk = SimpleNamespace(
        id=102,
        chunk_text="Manejo inicial de sepsis con lactato elevado y reanimacion guiada.",
        section_path="Sepsis > Bundle inicial",
        tokens_count=18,
        keywords=[],
        custom_questions=[],
        specialty="sepsis",
        content_type="markdown",
        _rag_score=0.8,
        document=SimpleNamespace(source_file="docs/47_motor_sepsis_urgencias.md"),
    )
    monkeypatch.setattr(
        orchestrator,
        "_resolve_adaptive_k",
        lambda query: (1, {"rag_adaptive_k_enabled": "0"}),
    )
    monkeypatch.setattr(
        orchestrator,
        "_search_with_configured_backend",
        lambda query, k, specialty_filter: (
            [chunk],
            {"vector_search_latency_ms": "3"},
            "hybrid",
        ),
    )

    answer, trace = orchestrator.process_query_with_rag(
        query="Paciente con sepsis, lactato alto e hipotension refractaria",
        response_mode="clinical",
        effective_specialty="sepsis",
        matched_domains=["sepsis"],
    )

    assert answer is not None
    assert trace["rag_status"] == "success"
    assert trace["rag_domain_search_skipped"] == "1"


def test_deterministic_complex_route_skips_domain_search(monkeypatch):
    orchestrator = RAGOrchestrator(db=SimpleNamespace())

    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_SKIP_DOMAIN_SEARCH_TOKENS_OVER",
        99,
    )
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_DETERMINISTIC_ROUTING_ENABLED",
        True,
    )
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_COMPLEX_ROUTE_FORCE_SKIP_DOMAIN_SEARCH",
        True,
    )
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_DETERMINISTIC_COMPLEX_MIN_TOKENS",
        8,
    )
    monkeypatch.setattr("app.services.rag_orchestrator.settings.CLINICAL_CHAT_LLM_ENABLED", False)
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_SAFE_WRAPPER_ENABLED",
        False,
    )

    def fail_domain_search(*args, **kwargs):  # noqa: ARG001
        raise AssertionError(
            "domain search should have been skipped by deterministic complex route"
        )

    monkeypatch.setattr(orchestrator.legacy_retriever, "search_by_domain", fail_domain_search)

    chunk = SimpleNamespace(
        id=103,
        chunk_text="Oliguria e hiperkalemia: estabilizar membrana y monitorizar ECG.",
        section_path="Nefrologia > Hiperkalemia",
        tokens_count=20,
        keywords=[],
        custom_questions=[],
        specialty="nephrology",
        content_type="markdown",
        _rag_score=0.82,
        document=SimpleNamespace(source_file="docs/73_motor_operativo_nefrologia_urgencias.md"),
    )
    monkeypatch.setattr(
        orchestrator,
        "_resolve_adaptive_k",
        lambda query: (2, {"rag_adaptive_k_enabled": "0"}),
    )
    monkeypatch.setattr(
        orchestrator,
        "_search_with_configured_backend",
        lambda query, k, specialty_filter: (
            [chunk],
            {"vector_search_latency_ms": "4"},
            "hybrid",
        ),
    )

    answer, trace = orchestrator.process_query_with_rag(
        query="Oliguria con hiperkalemia y QRS ancho: acciones inmediatas y criterios de dialisis.",
        response_mode="clinical",
        effective_specialty="nephrology",
        matched_domains=["nephrology"],
    )

    assert answer is not None
    assert trace["rag_status"] == "success"
    assert trace["rag_query_complexity"] == "complex"
    assert trace["rag_domain_search_skipped"] == "1"
    assert trace["rag_domain_search_skip_reason"] == "deterministic_complex_route"


def test_safe_wrapper_pre_generation_skips_llm_when_context_is_low(monkeypatch):
    orchestrator = RAGOrchestrator(db=SimpleNamespace())
    llm_called = {"value": False}

    def fake_llm(**kwargs):  # noqa: ARG001
        llm_called["value"] = True
        return "respuesta llm", {"llm_used": "true"}

    monkeypatch.setattr(
        "app.services.rag_orchestrator.LLMChatProvider.generate_answer",
        fake_llm,
    )
    monkeypatch.setattr("app.services.rag_orchestrator.settings.CLINICAL_CHAT_LLM_ENABLED", True)
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_SAFE_WRAPPER_ENABLED",
        True,
    )
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_SAFE_WRAPPER_MIN_CONTEXT_RATIO",
        0.85,
    )

    chunk = SimpleNamespace(
        id=104,
        chunk_text="Documento administrativo sin relacion clinica directa para esta consulta.",
        section_path="Administrativo > Sin relevancia clinica",
        tokens_count=15,
        keywords=[],
        custom_questions=[],
        specialty="general",
        content_type="markdown",
        _rag_score=0.9,
        document=SimpleNamespace(source_file="docs/66_motor_operativo_critico_transversal_urgencias.md"),
    )

    monkeypatch.setattr(
        orchestrator,
        "_resolve_adaptive_k",
        lambda query: (1, {"rag_adaptive_k_enabled": "0"}),
    )
    monkeypatch.setattr(
        orchestrator,
        "_search_with_configured_backend",
        lambda query, k, specialty_filter: (
            [chunk],
            {"vector_search_latency_ms": "2"},
            "hybrid",
        ),
    )

    answer, trace = orchestrator.process_query_with_rag(
        query="Neutropenia febril oncologica: pasos 0-10 y 10-60.",
        response_mode="clinical",
        effective_specialty="oncology",
        matched_domains=[],
    )

    assert llm_called["value"] is False
    assert answer is not None
    assert "No hay evidencia interna suficiente" in answer
    assert trace["rag_generation_mode"] == "safe_wrapper_abstain"
    assert trace["rag_safe_wrapper_triggered"] == "1"


def test_safe_wrapper_pre_generation_is_disabled_in_relaxed_pipeline_mode(monkeypatch):
    orchestrator = RAGOrchestrator(db=SimpleNamespace())
    llm_called = {"value": False}

    def fake_llm(**kwargs):  # noqa: ARG001
        llm_called["value"] = True
        return "respuesta llm relajada", {"llm_used": "true", "llm_endpoint": "chat"}

    monkeypatch.setattr(
        "app.services.rag_orchestrator.LLMChatProvider.generate_answer",
        fake_llm,
    )
    monkeypatch.setattr("app.services.rag_orchestrator.settings.CLINICAL_CHAT_LLM_ENABLED", True)
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_SAFE_WRAPPER_ENABLED",
        True,
    )
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_SAFE_WRAPPER_MIN_CONTEXT_RATIO",
        0.85,
    )

    chunk = SimpleNamespace(
        id=1404,
        chunk_text="Documento administrativo sin relacion clinica directa para esta consulta.",
        section_path="Administrativo > Sin relevancia clinica",
        tokens_count=15,
        keywords=[],
        custom_questions=[],
        specialty="general",
        content_type="markdown",
        _rag_score=0.9,
        document=SimpleNamespace(source_file="docs/66_motor_operativo_critico_transversal_urgencias.md"),
    )
    monkeypatch.setattr(
        orchestrator,
        "_resolve_adaptive_k",
        lambda query: (1, {"rag_adaptive_k_enabled": "0"}),
    )
    monkeypatch.setattr(
        orchestrator,
        "_search_with_configured_backend",
        lambda query, k, specialty_filter: (
            [chunk],
            {"vector_search_latency_ms": "2"},
            "hybrid",
        ),
    )

    answer, trace = orchestrator.process_query_with_rag(
        query="Neutropenia febril oncologica: pasos 0-10 y 10-60.",
        response_mode="clinical",
        effective_specialty="oncology",
        matched_domains=[],
        pipeline_relaxed_mode=True,
    )

    assert llm_called["value"] is True
    assert answer == "respuesta llm relajada"
    assert trace["rag_pipeline_profile"] == "evaluation"
    assert trace["rag_safe_wrapper_effective_enabled"] == "0"
    assert "rag_safe_wrapper_triggered" not in trace


def test_build_rag_sources_prioritizes_high_score_before_source_type():
    orchestrator = RAGOrchestrator(db=SimpleNamespace())
    chunks = [
        {
            "section": "Documento PDF menos relevante",
            "source": "docs/pdf_raw/guia_A.pdf",
            "text": "Texto clinico de soporte A con menor relevancia.",
            "score": 0.21,
        },
        {
            "section": "Documento markdown mas relevante",
            "source": "docs/73_motor_operativo_nefrologia_urgencias.md",
            "text": "Hiperkalemia con QRS ancho requiere accion inmediata.",
            "score": 0.89,
        },
    ]
    sources = orchestrator._build_rag_knowledge_sources(chunks)
    assert sources
    assert sources[0]["source"] == "docs/73_motor_operativo_nefrologia_urgencias.md"


def test_build_rag_sources_excludes_non_clinical_chat_docs():
    orchestrator = RAGOrchestrator(db=SimpleNamespace())
    chunks = [
        {
            "text": "Contenido operativo de oncologia con acciones y umbrales clinicos.",
            "section": "Oncologia > Neutropenia",
            "source": "docs/76_motor_operativo_oncologia_urgencias.md",
            "score": 0.60,
        },
        {
            "text": "Contrato de chat y arquitectura conversacional.",
            "section": "Chat clinico > Contrato",
            "source": "docs/88_chat_clinico_especialidad_contexto_longitudinal.md",
            "score": 0.95,
        },
    ]
    sources = orchestrator._build_rag_knowledge_sources(chunks)
    assert sources
    assert all("88_chat_clinico" not in source["source"] for source in sources)
    assert any("76_motor_operativo_oncologia" in source["source"] for source in sources)


def test_non_clinical_source_filter_blocks_pre_motor_docs():
    assert (
        RAGOrchestrator._looks_like_non_clinical_source(
            "docs/37_contexto_operaciones_clinicas_urgencias_es.md"
        )
        is True
    )
    assert (
        RAGOrchestrator._looks_like_non_clinical_source(
            "docs/47_motor_sepsis_urgencias.md"
        )
        is False
    )


def test_drop_noisy_chunks_filters_non_clinical_source_files():
    noisy_chunk = SimpleNamespace(
        id=2001,
        chunk_text="Texto valido pero de documento de arquitectura de chat.",
        document=SimpleNamespace(
            source_file="docs/88_chat_clinico_especialidad_contexto_longitudinal.md"
        ),
    )
    clinical_chunk = SimpleNamespace(
        id=2002,
        chunk_text="Sepsis con hipotension y lactato elevado: activar bundle.",
        document=SimpleNamespace(source_file="docs/47_motor_sepsis_urgencias.md"),
    )
    filtered, trace = RAGOrchestrator._drop_noisy_chunks([noisy_chunk, clinical_chunk])
    assert len(filtered) == 1
    assert int(getattr(filtered[0], "id")) == 2002
    assert trace["rag_chunks_noise_filtered"] == "1"


def test_infer_query_intents_detects_pharmacology_and_steps():
    intents, expansion_terms, trace = RAGOrchestrator._infer_query_intents(
        query="Farmacos y pasos a seguir para manejo inicial en urgencias",
    )
    assert "pharmacology" in intents
    assert "steps_actions" in intents
    assert "dosis" in expansion_terms
    assert trace["rag_query_intents_detected"] != "none"


def test_infer_query_intents_detects_referral_followup_and_similar_cases():
    intents, expansion_terms, trace = RAGOrchestrator._infer_query_intents(
        query=(
            "Cuando derivar, que seguimiento proponer y valorar otros casos parecidos "
            "en esta especialidad"
        ),
    )
    assert "referral" in intents
    assert "follow_up" in intents
    assert "similar_cases" in intents
    assert "interconsulta" in expansion_terms
    assert "control evolutivo" in expansion_terms
    assert "casos comparables" in expansion_terms
    assert trace["rag_query_intents_detected"] != "none"


def test_force_extractive_only_mode_skips_llm_and_returns_extractive(monkeypatch):
    orchestrator = RAGOrchestrator(db=SimpleNamespace())
    llm_called = {"value": False}

    def fake_llm(**kwargs):  # noqa: ARG001
        llm_called["value"] = True
        return "respuesta llm", {"llm_used": "true"}

    monkeypatch.setattr(
        "app.services.rag_orchestrator.LLMChatProvider.generate_answer",
        fake_llm,
    )
    monkeypatch.setattr("app.services.rag_orchestrator.settings.CLINICAL_CHAT_LLM_ENABLED", True)
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_FORCE_EXTRACTIVE_ONLY",
        True,
    )
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_SAFE_WRAPPER_ENABLED",
        False,
    )
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_EXTRACTIVE_FALLBACK_ENABLED",
        True,
    )

    chunk = SimpleNamespace(
        id=1201,
        chunk_text=(
            "Neutropenia febril en oncologia: iniciar hemocultivos, antibiotico precoz y "
            "monitorizacion hemodinamica en primera hora."
        ),
        section_path="Oncologia > Neutropenia febril",
        tokens_count=32,
        keywords=[],
        custom_questions=[],
        specialty="oncology",
        content_type="markdown",
        _rag_score=0.88,
        document=SimpleNamespace(source_file="docs/76_motor_operativo_oncologia_urgencias.md"),
    )
    monkeypatch.setattr(
        orchestrator,
        "_resolve_adaptive_k",
        lambda query: (1, {"rag_adaptive_k_enabled": "0"}),
    )
    monkeypatch.setattr(
        orchestrator,
        "_search_with_configured_backend",
        lambda query, k, specialty_filter: ([chunk], {"vector_search_latency_ms": "2"}, "hybrid"),
    )

    answer, trace = orchestrator.process_query_with_rag(
        query="Neutropenia febril oncologica: pasos iniciales",
        response_mode="clinical",
        effective_specialty="oncology",
        matched_domains=[],
    )

    assert llm_called["value"] is False
    assert answer is not None
    assert trace["rag_status"] == "success"
    assert trace["rag_generation_mode"] == "extractive_forced_mode"
    assert trace["rag_llm_skipped_reason"] == "force_extractive_only"
    assert trace["llm_error"] == "ForcedExtractiveMode"


def test_search_backend_relaxes_specialty_filter_when_no_hits(monkeypatch):
    orchestrator = RAGOrchestrator(db=SimpleNamespace())
    calls: list[str | None] = []
    recovered_chunk = SimpleNamespace(id=2201, _rag_score=0.61)

    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_RETRIEVER_BACKEND",
        "legacy",
    )

    def fake_search_hybrid(query, db, *, k, specialty_filter=None):  # noqa: ARG001
        calls.append(specialty_filter)
        if specialty_filter:
            return [], {"hybrid_search_chunks_found": "0"}
        return [recovered_chunk], {"hybrid_search_chunks_found": "1"}

    monkeypatch.setattr(orchestrator.legacy_retriever, "search_hybrid", fake_search_hybrid)

    chunks, trace, strategy = orchestrator._search_with_configured_backend(
        query="Consulta con termino de especialidad sin cobertura puntual",
        k=2,
        specialty_filter="oncology",
    )

    assert strategy == "hybrid_specialty_relaxation"
    assert len(chunks) == 1
    assert calls == ["oncology", None]

    assert trace["rag_retriever_specialty_relaxation"] == "1"
    assert trace["rag_retriever_specialty_original"] == "oncology"


def test_qa_shortcut_hit_skips_domain_and_backend_search(monkeypatch):
    orchestrator = RAGOrchestrator(db=SimpleNamespace(query=lambda *args, **kwargs: None))

    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_QA_SHORTCUT_ENABLED",
        True,
    )
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_LLM_ENABLED",
        False,
    )
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_EXTRACTIVE_FALLBACK_ENABLED",
        True,
    )
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_SAFE_WRAPPER_ENABLED",
        False,
    )
    monkeypatch.setattr(
        orchestrator,
        "_resolve_adaptive_k",
        lambda query: (2, {"rag_adaptive_k_enabled": "0"}),
    )

    shortcut_chunk = SimpleNamespace(
        id=401,
        chunk_text=(
            "En neutropenia febril oncologica se recomienda toma de cultivos "
            "y antibioterapia empirica precoz."
        ),
        section_path="Oncologia > Neutropenia febril",
        tokens_count=22,
        keywords=["neutropenia", "fiebre"],
        custom_questions=["Neutropenia febril oncologica: pasos iniciales"],
        specialty="oncology",
        content_type="markdown",
        _rag_score=0.92,
        document=SimpleNamespace(source_file="docs/76_motor_operativo_oncologia_urgencias.md"),
    )

    monkeypatch.setattr(
        orchestrator,
        "_match_precomputed_qa_chunks",
        lambda query, specialty_filter, k: (
            [shortcut_chunk],
            {
                "rag_qa_shortcut_enabled": "1",
                "rag_qa_shortcut_hit": "1",
                "rag_qa_shortcut_hits": "1",
                "rag_qa_shortcut_top_score": "0.920",
            },
        ),
    )

    def fail_domain(*args, **kwargs):  # noqa: ARG001
        raise AssertionError("domain search should be skipped after qa shortcut hit")

    def fail_backend(*args, **kwargs):  # noqa: ARG001
        raise AssertionError("backend retrieval should be skipped after qa shortcut hit")

    monkeypatch.setattr(orchestrator.legacy_retriever, "search_by_domain", fail_domain)
    monkeypatch.setattr(orchestrator, "_search_with_configured_backend", fail_backend)

    answer, trace = orchestrator.process_query_with_rag(
        query="Neutropenia febril oncologica: pasos iniciales",
        response_mode="clinical",
        effective_specialty="oncology",
        matched_domains=["oncology"],
    )

    assert answer is not None
    assert trace["rag_status"] == "success"
    assert trace["rag_retrieval_strategy"] == "qa_shortcut"
    assert trace["rag_qa_shortcut_hit"] == "1"


def test_qa_shortcut_domain_misalignment_falls_back_to_hybrid(monkeypatch):
    orchestrator = RAGOrchestrator(db=SimpleNamespace())

    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_QA_SHORTCUT_ENABLED",
        True,
    )
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_LLM_ENABLED",
        False,
    )
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_EXTRACTIVE_FALLBACK_ENABLED",
        True,
    )
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_SAFE_WRAPPER_ENABLED",
        False,
    )
    monkeypatch.setattr(
        orchestrator,
        "_resolve_adaptive_k",
        lambda query: (1, {"rag_adaptive_k_enabled": "0"}),
    )

    qa_chunk = SimpleNamespace(
        id=1701,
        chunk_text="Urgencias ginecologicas con dolor pelvico y sangrado vaginal.",
        section_path="Ginecologia > Triaje inicial",
        tokens_count=18,
        keywords=[],
        custom_questions=[],
        specialty="gynecology_obstetrics",
        content_type="markdown",
        _rag_score=0.40,
        document=SimpleNamespace(
            source_file="docs/85_motor_operativo_ginecologia_obstetricia_urgencias.md"
        ),
    )
    psych_chunk = SimpleNamespace(
        id=1702,
        chunk_text="Paciente con agitacion psicomotriz: contencion verbal y evaluacion de riesgo.",
        section_path="Psiquiatria > Manejo inicial",
        tokens_count=20,
        keywords=[],
        custom_questions=[],
        specialty="psychiatry",
        content_type="markdown",
        _rag_score=0.82,
        document=SimpleNamespace(source_file="docs/70_motor_operativo_psiquiatria_urgencias.md"),
    )

    monkeypatch.setattr(
        orchestrator,
        "_match_precomputed_qa_chunks",
        lambda query, specialty_filter, k: (
            [qa_chunk],
            {
                "rag_qa_shortcut_enabled": "1",
                "rag_qa_shortcut_hit": "1",
                "rag_qa_shortcut_top_score": "0.40",
            },
        ),
    )
    monkeypatch.setattr(
        orchestrator.legacy_retriever,
        "search_by_domain",
        lambda matched_domains, db, query, k: ([], {"domain_search_hits": "0"}),
    )
    monkeypatch.setattr(
        orchestrator,
        "_search_with_configured_backend",
        lambda query, k, specialty_filter, keyword_only=False: (
            [psych_chunk],
            {"vector_search_latency_ms": "2"},
            "hybrid",
        ),
    )

    answer, trace = orchestrator.process_query_with_rag(
        query="casos de pacientes psiquiatricos en urgencias",
        response_mode="clinical",
        effective_specialty="general",
        matched_domains=["psychiatry"],
    )

    assert answer is not None
    assert trace["rag_qa_shortcut_reason"] == "domain_misalignment"
    assert trace["rag_retrieval_strategy"] == "hybrid"


def test_qa_shortcut_matching_returns_chunk_for_precomputed_questions(db_session, monkeypatch):
    orchestrator = RAGOrchestrator(db=db_session)
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_QA_SHORTCUT_MIN_SCORE",
        0.45,
    )
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_QA_SHORTCUT_TOP_K",
        2,
    )
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_QA_SHORTCUT_MAX_CANDIDATES",
        50,
    )

    doc = ClinicalDocument(
        title="Motor Oncologia",
        source_file="docs/76_motor_operativo_oncologia_urgencias.md",
        specialty="oncology",
        version=1,
        content_hash="1" * 64,
    )
    db_session.add(doc)
    db_session.flush()

    db_session.add(
        DocumentChunk(
            document_id=doc.id,
            chunk_text=(
                "En neutropenia febril oncologica se debe iniciar monitorizacion, "
                "hemocultivos y antibioterapia empirica."
            ),
            chunk_index=0,
            section_path="Oncologia > Neutropenia febril",
            tokens_count=24,
            chunk_embedding=b"test",
            keywords=["neutropenia", "fiebre", "oncologia"],
            custom_questions=[
                "Neutropenia febril oncologica: pasos iniciales y fuentes internas"
            ],
            specialty="oncology",
            content_type="paragraph",
        )
    )
    db_session.commit()

    chunks, trace = orchestrator._match_precomputed_qa_chunks(
        query="Neutropenia febril oncologica: pasos iniciales",
        specialty_filter="oncology",
        k=2,
    )

    assert chunks
    assert trace["rag_qa_shortcut_hit"] == "1"
    assert trace["rag_qa_shortcut_hits"] in {"1", "2"}


def test_qa_shortcut_matching_allows_chunks_without_specialty(db_session, monkeypatch):
    orchestrator = RAGOrchestrator(db=db_session)
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_QA_SHORTCUT_MIN_SCORE",
        0.30,
    )

    doc = ClinicalDocument(
        title="Guia General",
        source_file="docs/48_flujo_extremo_a_extremo_episodio_urgencias.md",
        specialty=None,
        version=1,
        content_hash="2" * 64,
    )
    db_session.add(doc)
    db_session.flush()

    db_session.add(
        DocumentChunk(
            document_id=doc.id,
            chunk_text=(
                "En shock septico con lactato alto se prioriza bundle inicial con cultivos, "
                "antibiotico temprano y soporte hemodinamico."
            ),
            chunk_index=0,
            section_path="Operativa critica > Sepsis",
            tokens_count=30,
            chunk_embedding=b"test",
            keywords=["shock", "septico", "lactato"],
            custom_questions=["Shock septico: bundle inicial y pasos operativos"],
            specialty=None,
            content_type="paragraph",
        )
    )
    db_session.commit()

    chunks, trace = orchestrator._match_precomputed_qa_chunks(
        query="Shock septico con lactato alto: bundle inicial",
        specialty_filter="general",
        k=2,
    )

    assert chunks
    assert trace["rag_qa_shortcut_hit"] == "1"


def test_generic_fallback_domain_skips_domain_search(monkeypatch):
    orchestrator = RAGOrchestrator(db=SimpleNamespace(query=lambda *args, **kwargs: None))

    monkeypatch.setattr("app.services.rag_orchestrator.settings.CLINICAL_CHAT_LLM_ENABLED", False)
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_QA_SHORTCUT_ENABLED",
        False,
    )
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_EXTRACTIVE_FALLBACK_ENABLED",
        True,
    )
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_SAFE_WRAPPER_ENABLED",
        False,
    )

    def fail_domain_search(*args, **kwargs):  # noqa: ARG001
        raise AssertionError("domain search should be skipped in generic fallback mode")

    monkeypatch.setattr(orchestrator.legacy_retriever, "search_by_domain", fail_domain_search)

    chunk = SimpleNamespace(
        id=998,
        chunk_text="Manejo inicial de dolor toracico con troponina positiva.",
        section_path="SCASEST > Ruta inicial",
        tokens_count=14,
        keywords=[],
        custom_questions=["Dolor toracico con troponina positiva: ruta inicial"],
        specialty="scasest",
        content_type="paragraph",
        _rag_score=0.81,
        document=SimpleNamespace(source_file="docs/49_motor_scasest_urgencias.md"),
    )

    monkeypatch.setattr(
        orchestrator,
        "_resolve_adaptive_k",
        lambda query: (2, {"rag_adaptive_k_enabled": "0"}),
    )
    monkeypatch.setattr(
        orchestrator,
        "_search_with_configured_backend",
        lambda query, k, specialty_filter: ([chunk], {"hybrid_search_chunks_found": "1"}, "hybrid"),
    )

    answer, trace = orchestrator.process_query_with_rag(
        query="Dolor toracico con troponina positiva",
        response_mode="clinical",
        effective_specialty="general",
        matched_domains=["critical_ops"],
    )

    assert answer is not None
    assert trace["rag_domain_search_skipped"] == "1"
    assert trace["rag_domain_search_skip_reason"] == "generic_domain_fallback_bypass"


def test_multi_intent_segment_plan_detects_compound_query(monkeypatch):
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_MULTI_INTENT_ENABLED",
        True,
    )
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_MULTI_INTENT_MAX_SEGMENTS",
        4,
    )
    plan, trace = RAGOrchestrator._build_multi_intent_segment_plan(
        query=(
            "Paciente oncologico con neutropenia febril y sepsis con hipotension refractaria "
            "en primeras horas."
        ),
        effective_specialty="general",
        matched_domains=["critical_ops"],
    )

    assert len(plan) >= 2
    assert trace["rag_multi_intent_plan_size"] != "0"
    specialties = {str(item.get("specialty_filter")) for item in plan}
    assert "oncology" in specialties or "sepsis" in specialties


def test_multi_intent_search_merges_chunks_from_each_segment():
    orchestrator = RAGOrchestrator(db=SimpleNamespace())

    chunk_a = SimpleNamespace(id=201, _rag_score=0.50)
    chunk_b = SimpleNamespace(id=301, _rag_score=0.40)

    responses = iter(
        [
            ([chunk_a], {"hybrid_search_chunks_found": "1"}, "hybrid"),
            ([chunk_b], {"hybrid_search_chunks_found": "1"}, "hybrid"),
        ]
    )
    orchestrator._search_with_configured_backend = lambda **kwargs: next(responses)  # type: ignore[method-assign]

    selected, trace = orchestrator._search_multi_intent_segments(
        segment_plan=[
            {
                "segment": "neutropenia febril oncologica",
                "specialty_filter": "oncology",
                "top_probability": 0.8,
            },
            {
                "segment": "sepsis con hipotension refractaria",
                "specialty_filter": "sepsis",
                "top_probability": 0.7,
            },
        ],
        k=3,
        keyword_only=False,
    )

    assert len(selected) == 2
    assert trace["rag_multi_intent_chunks"] == "2"
    assert trace["rag_multi_intent_segment_1_hits"] == "1"
    assert trace["rag_multi_intent_segment_2_hits"] == "1"


def test_extractive_answer_prioritizes_actionable_sentences_over_aux_noise():
    answer = RAGOrchestrator._build_extractive_answer(
        query="Sepsis con hipotension: acciones iniciales",
        matched_domains=["sepsis"],
        chunks=[
            {
                "text": (
                    "El paciente ha sido y puede estar en evaluacion general durante todo el turno "
                    "sin accion operativa concreta. "
                    "Iniciar bundle de sepsis con hemocultivos, antibiotico precoz y "
                    "monitorizacion hemodinamica continua."
                ),
                "section": "Sepsis > Bundle inicial",
                "source": "docs/47_motor_sepsis_urgencias.md",
                "score": 0.8,
            }
        ],
    )

    assert answer is not None
    lowered = answer.lower()
    assert "iniciar bundle de sepsis" in lowered
    assert "ha sido y puede estar" not in lowered


def test_extractive_answer_source_anchor_hides_source_leaf():
    answer = RAGOrchestrator._build_extractive_answer(
        query="Neutropenia febril oncologica",
        matched_domains=["oncology"],
        chunks=[
            {
                "text": (
                    "En neutropenia febril oncologica se debe iniciar antibioterapia empirica "
                    "precoz y hemocultivos."
                ),
                "section": "Oncologia > Neutropenia febril",
                "source": "docs/76_motor_operativo_oncologia_urgencias.md",
                "score": 0.7,
            }
        ],
    )

    assert answer is not None
    assert "Oncologia > Neutropenia febril" in answer
    assert "(76_motor_operativo_oncologia_urgencias.md)" not in answer


def test_context_assembler_adds_title_and_page_metadata():
    chunk = SimpleNamespace(
        id=77,
        chunk_text="En sepsis se debe iniciar bundle inicial y monitorizacion hemodinamica.",
        section_path="Sepsis > Bundle inicial > Pagina 12",
        _rag_score=0.81,
        keywords=["sepsis", "bundle"],
        custom_questions=[],
        specialty="sepsis",
        tokens_count=20,
        document=SimpleNamespace(
            source_file="docs/47_motor_sepsis_urgencias.md",
            title="Motor de Sepsis Urgencias",
        ),
    )

    assembled, trace = RAGContextAssembler.assemble_rag_context([chunk])

    assert trace["rag_assembled_chunks"] == "1"
    assert assembled[0]["source_title"] == "Motor de Sepsis Urgencias"
    assert assembled[0]["source_page"] == "12"


def test_verifier_filters_noise_chunks_with_cross_encoder_proxy(monkeypatch):
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_VERIFIER_ENABLED",
        True,
    )
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_VERIFIER_MIN_SCORE",
        0.50,
    )
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_VERIFIER_MIN_CHUNKS",
        1,
    )
    orchestrator = RAGOrchestrator(db=SimpleNamespace())

    relevant = SimpleNamespace(
        id=901,
        chunk_text=(
            "Sepsis con hipotension y lactato elevado requiere iniciar bundle con "
            "hemocultivos, antibiotico precoz y monitorizacion."
        ),
        section_path="Sepsis > Bundle inicial",
        keywords=["sepsis", "lactato", "bundle"],
        _rag_score=0.62,
        document=SimpleNamespace(title="Motor de Sepsis"),
    )
    noise = SimpleNamespace(
        id=902,
        chunk_text="Cronologia administrativa del servicio y resumen editorial general.",
        section_path="General > Historico",
        keywords=["historico"],
        _rag_score=0.71,
        document=SimpleNamespace(title="Documento General"),
    )

    selected, trace = orchestrator._verify_retrieved_chunks(
        query="Sepsis con lactato alto e hipotension, acciones inmediatas",
        chunks=[noise, relevant],
    )

    assert trace["rag_verifier_passed"] == "1"
    assert trace["rag_verifier_verified"] == "1"
    assert len(selected) == 1
    assert int(getattr(selected[0], "id")) == 901


def test_verifier_enforces_minimum_verified_chunks(monkeypatch):
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_VERIFIER_ENABLED",
        True,
    )
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_VERIFIER_MIN_SCORE",
        0.45,
    )
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_VERIFIER_MIN_CHUNKS",
        2,
    )
    orchestrator = RAGOrchestrator(db=SimpleNamespace())
    one_chunk = SimpleNamespace(
        id=903,
        chunk_text="Iniciar bundle de sepsis y antibioterapia en primera hora.",
        section_path="Sepsis > Bundle inicial",
        keywords=["sepsis", "bundle"],
        _rag_score=0.73,
        document=SimpleNamespace(title="Motor de Sepsis"),
    )

    selected, trace = orchestrator._verify_retrieved_chunks(
        query="Sepsis con hipotension refractaria",
        chunks=[one_chunk],
    )

    assert selected == []
    assert trace["rag_verifier_passed"] == "0"
    assert trace["rag_verifier_reason"] == "below_min_verified_chunks"


def test_ecorag_reflection_reaches_threshold_with_compact_context(monkeypatch):
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_ECORAG_ENABLED",
        True,
    )
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_ECORAG_MIN_EVIDENTIALITY",
        0.35,
    )
    monkeypatch.setattr(
        "app.services.rag_orchestrator.settings.CLINICAL_CHAT_RAG_ECORAG_MIN_CHUNKS",
        1,
    )

    selected, trace = RAGOrchestrator._apply_ecorag_evidential_reflection(
        query="Sepsis con hipotension y lactato elevado",
        chunks=[
            {
                "text": (
                    "Sepsis con hipotension y lactato elevado: iniciar bundle, hemocultivos y "
                    "antibiotico precoz en primera hora."
                ),
                "section": "Sepsis > Bundle inicial",
                "source": "docs/47_motor_sepsis_urgencias.md",
                "score": 0.84,
            },
            {
                "text": "Resumen editorial general sin acciones clinicas concretas para el caso.",
                "section": "General > Introduccion",
                "source": "docs/37_contexto_operaciones_clinicas_urgencias_es.md",
                "score": 0.41,
            },
        ],
    )

    assert selected
    assert len(selected) == 1
    assert trace["rag_ecorag_resolved"] == "1"


def test_extractive_answer_source_anchor_includes_title_section_page():
    answer = RAGOrchestrator._build_extractive_answer(
        query="Sepsis con hipotension refractaria",
        matched_domains=["sepsis"],
        chunks=[
            {
                "text": (
                    "Ante sepsis con hipotension refractaria, iniciar vasopresor, monitorizacion "
                    "continua y reevaluacion hemodinamica."
                ),
                "section": "Sepsis > Escalado hemodinamico",
                "source_title": "Motor de Sepsis Urgencias",
                "source_page": "14",
                "source": "docs/47_motor_sepsis_urgencias.md",
                "score": 0.79,
            }
        ],
    )

    assert answer is not None
    assert "Motor de Sepsis Urgencias > Sepsis > Escalado hemodinamico [p.14]" in answer
