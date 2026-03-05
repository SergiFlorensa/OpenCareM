import pytest

from app.core.config import DEFAULT_SECRET_KEY, Settings


def test_allows_default_secret_in_development():
    settings = Settings(
        ENVIRONMENT="development",
        SECRET_KEY=DEFAULT_SECRET_KEY,
        BACKEND_CORS_ORIGINS=["http://localhost:8000"],
    )
    assert settings.ENVIRONMENT == "development"


def test_rejects_default_secret_outside_development():
    with pytest.raises(ValueError, match="SECRET_KEY debe cambiarse"):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY=DEFAULT_SECRET_KEY,
            BACKEND_CORS_ORIGINS=["https://api.example.com"],
        )


def test_rejects_short_secret_outside_development():
    with pytest.raises(ValueError, match="al menos 32 caracteres"):
        Settings(
            ENVIRONMENT="staging",
            SECRET_KEY="short-secret",
            BACKEND_CORS_ORIGINS=["https://api.example.com"],
        )


def test_rejects_wildcard_cors_outside_development():
    with pytest.raises(ValueError, match="no puede contener '\\*'"):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="secure-secret-key-secure-secret-key-123",
            BACKEND_CORS_ORIGINS=["*"],
        )


def test_rejects_invalid_rag_retriever_backend():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_RETRIEVER_BACKEND"):
        Settings(
            CLINICAL_CHAT_RAG_RETRIEVER_BACKEND="unknown",
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_allows_elastic_rag_backend():
    settings = Settings(
        CLINICAL_CHAT_RAG_RETRIEVER_BACKEND="elastic",
        CLINICAL_CHAT_RAG_ELASTIC_URL="http://127.0.0.1:9200",
        CLINICAL_CHAT_RAG_ELASTIC_INDEX="clinical_chunks",
        BACKEND_CORS_ORIGINS=["http://localhost:5173"],
    )
    assert settings.CLINICAL_CHAT_RAG_RETRIEVER_BACKEND == "elastic"


def test_allows_llama_cpp_provider():
    settings = Settings(
        CLINICAL_CHAT_LLM_PROVIDER="llama_cpp",
        CLINICAL_CHAT_LLM_BASE_URL="http://127.0.0.1:8080",
        BACKEND_CORS_ORIGINS=["http://localhost:5173"],
    )
    assert settings.CLINICAL_CHAT_LLM_PROVIDER == "llama_cpp"


def test_rejects_empty_guardrails_config_path():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_GUARDRAILS_CONFIG_PATH"):
        Settings(
            CLINICAL_CHAT_GUARDRAILS_CONFIG_PATH="   ",
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_chroma_candidate_pool():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_CHROMA_CANDIDATE_POOL"):
        Settings(
            CLINICAL_CHAT_RAG_CHROMA_CANDIDATE_POOL=5,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_elastic_candidate_pool():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_ELASTIC_CANDIDATE_POOL"):
        Settings(
            CLINICAL_CHAT_RAG_ELASTIC_CANDIDATE_POOL=10,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_context_min_ratio():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_CONTEXT_MIN_RATIO"):
        Settings(
            CLINICAL_CHAT_RAG_CONTEXT_MIN_RATIO=1.5,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_early_goal_min_score():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_EARLY_GOAL_MIN_SCORE"):
        Settings(
            CLINICAL_CHAT_RAG_EARLY_GOAL_MIN_SCORE=1.2,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_query_cache_ttl_seconds():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_QUERY_CACHE_TTL_SECONDS"):
        Settings(
            CLINICAL_CHAT_RAG_QUERY_CACHE_TTL_SECONDS=5,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_query_cache_max_entries():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_QUERY_CACHE_MAX_ENTRIES"):
        Settings(
            CLINICAL_CHAT_RAG_QUERY_CACHE_MAX_ENTRIES=4,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_allows_fact_only_mode():
    settings = Settings(
        CLINICAL_CHAT_RAG_FACT_ONLY_MODE_ENABLED=True,
        CLINICAL_CHAT_RAG_EARLY_GOAL_TEST_ENABLED=True,
        BACKEND_CORS_ORIGINS=["http://localhost:5173"],
    )
    assert settings.CLINICAL_CHAT_RAG_FACT_ONLY_MODE_ENABLED is True


def test_rejects_invalid_discourse_min_score():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_DISCOURSE_MIN_SCORE"):
        Settings(
            CLINICAL_CHAT_RAG_DISCOURSE_MIN_SCORE=1.2,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_discourse_max_satellite_ratio():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_DISCOURSE_MAX_SATELLITE_RATIO"):
        Settings(
            CLINICAL_CHAT_RAG_DISCOURSE_MAX_SATELLITE_RATIO=-0.1,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_discourse_lcd_min_score():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_DISCOURSE_LCD_MIN_SCORE"):
        Settings(
            CLINICAL_CHAT_RAG_DISCOURSE_LCD_MIN_SCORE=1.1,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_allows_discourse_coherence_settings():
    settings = Settings(
        CLINICAL_CHAT_RAG_DISCOURSE_COHERENCE_ENABLED=True,
        CLINICAL_CHAT_RAG_DISCOURSE_MIN_SCORE=0.3,
        CLINICAL_CHAT_RAG_DISCOURSE_MAX_SATELLITE_RATIO=0.5,
        CLINICAL_CHAT_RAG_DISCOURSE_LCD_MIN_SCORE=0.2,
        BACKEND_CORS_ORIGINS=["http://localhost:5173"],
    )
    assert settings.CLINICAL_CHAT_RAG_DISCOURSE_COHERENCE_ENABLED is True


def test_rejects_invalid_pdf_parser_backend():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_PDF_PARSER_BACKEND"):
        Settings(
            CLINICAL_CHAT_PDF_PARSER_BACKEND="unknown",
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_mineru_timeout():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_PDF_MINERU_TIMEOUT_SECONDS"):
        Settings(
            CLINICAL_CHAT_PDF_MINERU_TIMEOUT_SECONDS=5,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_pdf_ocr_mode():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_PDF_OCR_MODE"):
        Settings(
            CLINICAL_CHAT_PDF_OCR_MODE="invalid_mode",
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_pdf_repeated_edge_min_pages():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_PDF_FILTER_REPEATED_EDGE_TEXT_MIN_PAGES"):
        Settings(
            CLINICAL_CHAT_PDF_FILTER_REPEATED_EDGE_TEXT_MIN_PAGES=1,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_adaptive_chunk_bounds():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_MIN_CHUNKS"):
        Settings(
            CLINICAL_CHAT_RAG_MIN_CHUNKS=9,
            CLINICAL_CHAT_RAG_MAX_CHUNKS_HARD=5,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_mmr_lambda():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_MMR_LAMBDA"):
        Settings(
            CLINICAL_CHAT_RAG_MMR_LAMBDA=1.2,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_context_compression_max_chars():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_COMPRESS_MAX_CHARS"):
        Settings(
            CLINICAL_CHAT_RAG_COMPRESS_MAX_CHARS=90,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_llm_context_utilization_ratio():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_LLM_MAX_CONTEXT_UTILIZATION_RATIO"):
        Settings(
            CLINICAL_CHAT_LLM_MAX_CONTEXT_UTILIZATION_RATIO=0.95,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_simple_route_max_chunks_vs_hard_limit():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_SIMPLE_ROUTE_MAX_CHUNKS"):
        Settings(
            CLINICAL_CHAT_RAG_SIMPLE_ROUTE_MAX_CHUNKS=9,
            CLINICAL_CHAT_RAG_MAX_CHUNKS_HARD=6,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_fts_candidate_pool():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_FTS_CANDIDATE_POOL"):
        Settings(
            CLINICAL_CHAT_RAG_FTS_CANDIDATE_POOL=10,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_spell_max_edit_distance():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_SPELL_MAX_EDIT_DISTANCE"):
        Settings(
            CLINICAL_CHAT_RAG_SPELL_MAX_EDIT_DISTANCE=0,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_skip_pointers_min_list():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_SKIP_POINTERS_MIN_LIST"):
        Settings(
            CLINICAL_CHAT_RAG_SKIP_POINTERS_MIN_LIST=8,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_spell_trigger_max_postings():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_SPELL_TRIGGER_MAX_POSTINGS"):
        Settings(
            CLINICAL_CHAT_RAG_SPELL_TRIGGER_MAX_POSTINGS=0,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_wildcard_max_expansions():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_WILDCARD_MAX_EXPANSIONS"):
        Settings(
            CLINICAL_CHAT_RAG_WILDCARD_MAX_EXPANSIONS=4,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_kgram_jaccard_min():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_KGRAM_JACCARD_MIN"):
        Settings(
            CLINICAL_CHAT_RAG_KGRAM_JACCARD_MIN=0.99,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_contextual_spell_max_candidates():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_CONTEXTUAL_SPELL_MAX_CANDIDATES"):
        Settings(
            CLINICAL_CHAT_RAG_CONTEXTUAL_SPELL_MAX_CANDIDATES=4,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_vocab_cache_max_terms():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_VOCAB_CACHE_MAX_TERMS"):
        Settings(
            CLINICAL_CHAT_RAG_VOCAB_CACHE_MAX_TERMS=500,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_vocab_cache_ttl_seconds():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_VOCAB_CACHE_TTL_SECONDS"):
        Settings(
            CLINICAL_CHAT_RAG_VOCAB_CACHE_TTL_SECONDS=10,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_postings_cache_max_entries():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_POSTINGS_CACHE_MAX_ENTRIES"):
        Settings(
            CLINICAL_CHAT_RAG_POSTINGS_CACHE_MAX_ENTRIES=10,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_postings_cache_ttl_seconds():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_POSTINGS_CACHE_TTL_SECONDS"):
        Settings(
            CLINICAL_CHAT_RAG_POSTINGS_CACHE_TTL_SECONDS=10,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_postings_cache_encoding():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_POSTINGS_CACHE_ENCODING"):
        Settings(
            CLINICAL_CHAT_RAG_POSTINGS_CACHE_ENCODING="delta",
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_tfidf_max_query_terms():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_TFIDF_MAX_QUERY_TERMS"):
        Settings(
            CLINICAL_CHAT_RAG_TFIDF_MAX_QUERY_TERMS=2,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_tfidf_pivot_slope():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_TFIDF_PIVOT_SLOPE"):
        Settings(
            CLINICAL_CHAT_RAG_TFIDF_PIVOT_SLOPE=1.5,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_tfidf_zone_blend():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_TFIDF_ZONE_BLEND"):
        Settings(
            CLINICAL_CHAT_RAG_TFIDF_ZONE_BLEND=-0.1,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_negative_zone_weight():
    with pytest.raises(ValueError, match="Pesos de zona RAG no pueden ser negativos"):
        Settings(
            CLINICAL_CHAT_RAG_ZONE_WEIGHT_TITLE=-0.01,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_idf_min_threshold():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_IDF_MIN_THRESHOLD"):
        Settings(
            CLINICAL_CHAT_RAG_IDF_MIN_THRESHOLD=0.8,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_idf_min_keep_terms():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_IDF_MIN_KEEP_TERMS"):
        Settings(
            CLINICAL_CHAT_RAG_IDF_MIN_KEEP_TERMS=0,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_proximity_bonus_weight():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_PROXIMITY_BONUS_WEIGHT"):
        Settings(
            CLINICAL_CHAT_RAG_PROXIMITY_BONUS_WEIGHT=1.5,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_static_quality_weight():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_STATIC_QUALITY_WEIGHT"):
        Settings(
            CLINICAL_CHAT_RAG_STATIC_QUALITY_WEIGHT=-0.1,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_tier1_min_static_quality():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_TIER1_MIN_STATIC_QUALITY"):
        Settings(
            CLINICAL_CHAT_RAG_TIER1_MIN_STATIC_QUALITY=1.2,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_empty_global_thesaurus_path():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_GLOBAL_THESAURUS_PATH"):
        Settings(
            CLINICAL_CHAT_RAG_GLOBAL_THESAURUS_PATH=" ",
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_global_thesaurus_ttl():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_GLOBAL_THESAURUS_TTL_SECONDS"):
        Settings(
            CLINICAL_CHAT_RAG_GLOBAL_THESAURUS_TTL_SECONDS=10,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_global_thesaurus_max_expansions():
    with pytest.raises(
        ValueError,
        match="CLINICAL_CHAT_RAG_GLOBAL_THESAURUS_MAX_EXPANSIONS_PER_TERM",
    ):
        Settings(
            CLINICAL_CHAT_RAG_GLOBAL_THESAURUS_MAX_EXPANSIONS_PER_TERM=0,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_prf_topk():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_PRF_TOPK"):
        Settings(
            CLINICAL_CHAT_RAG_PRF_TOPK=0,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_prf_max_terms():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_PRF_MAX_TERMS"):
        Settings(
            CLINICAL_CHAT_RAG_PRF_MAX_TERMS=0,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_prf_min_term_len():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_PRF_MIN_TERM_LEN"):
        Settings(
            CLINICAL_CHAT_RAG_PRF_MIN_TERM_LEN=2,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_prf_beta():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_PRF_BETA"):
        Settings(
            CLINICAL_CHAT_RAG_PRF_BETA=2.5,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_bm25_k1():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_BM25_K1"):
        Settings(
            CLINICAL_CHAT_RAG_BM25_K1=3.5,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_bm25_b():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_BM25_B"):
        Settings(
            CLINICAL_CHAT_RAG_BM25_B=1.5,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_bm25_blend():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_BM25_BLEND"):
        Settings(
            CLINICAL_CHAT_RAG_BM25_BLEND=-0.1,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_bim_binary_bonus_weight():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_BIM_BINARY_BONUS_WEIGHT"):
        Settings(
            CLINICAL_CHAT_RAG_BIM_BINARY_BONUS_WEIGHT=1.2,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_qlm_smoothing():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_QLM_SMOOTHING"):
        Settings(
            CLINICAL_CHAT_RAG_QLM_SMOOTHING="laplace",
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_qlm_dirichlet_mu():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_QLM_DIRICHLET_MU"):
        Settings(
            CLINICAL_CHAT_RAG_QLM_DIRICHLET_MU=50,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_qlm_jm_lambda():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_QLM_JM_LAMBDA"):
        Settings(
            CLINICAL_CHAT_RAG_QLM_JM_LAMBDA=1.5,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_qlm_blend():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_QLM_BLEND"):
        Settings(
            CLINICAL_CHAT_RAG_QLM_BLEND=-0.2,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_lsi_k():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_LSI_K"):
        Settings(
            CLINICAL_CHAT_RAG_LSI_K=1,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_lsi_blend():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_LSI_BLEND"):
        Settings(
            CLINICAL_CHAT_RAG_LSI_BLEND=1.2,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_lsi_max_vocab_terms():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_LSI_MAX_VOCAB_TERMS"):
        Settings(
            CLINICAL_CHAT_RAG_LSI_MAX_VOCAB_TERMS=32,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_lsi_min_docs():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_LSI_MIN_DOCS"):
        Settings(
            CLINICAL_CHAT_RAG_LSI_MIN_DOCS=1,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_nb_model():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_NB_MODEL"):
        Settings(
            CLINICAL_CHAT_NB_MODEL="gaussian",
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_nb_alpha():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_NB_ALPHA"):
        Settings(
            CLINICAL_CHAT_NB_ALPHA=0.0,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_nb_min_confidence():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_NB_MIN_CONFIDENCE"):
        Settings(
            CLINICAL_CHAT_NB_MIN_CONFIDENCE=1.2,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_nb_feature_method():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_NB_FEATURE_METHOD"):
        Settings(
            CLINICAL_CHAT_NB_FEATURE_METHOD="idf",
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_nb_max_features():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_NB_MAX_FEATURES"):
        Settings(
            CLINICAL_CHAT_NB_MAX_FEATURES=8,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_vector_method():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_VECTOR_METHOD"):
        Settings(
            CLINICAL_CHAT_VECTOR_METHOD="svm",
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_vector_k():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_VECTOR_K"):
        Settings(
            CLINICAL_CHAT_VECTOR_K=0,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_vector_min_confidence():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_VECTOR_MIN_CONFIDENCE"):
        Settings(
            CLINICAL_CHAT_VECTOR_MIN_CONFIDENCE=1.2,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_cluster_method():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_CLUSTER_METHOD"):
        Settings(
            CLINICAL_CHAT_CLUSTER_METHOD="dbscan",
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_cluster_k_bounds():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_CLUSTER_K_MIN"):
        Settings(
            CLINICAL_CHAT_CLUSTER_K_MIN=9,
            CLINICAL_CHAT_CLUSTER_K_MAX=4,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_cluster_min_confidence():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_CLUSTER_MIN_CONFIDENCE"):
        Settings(
            CLINICAL_CHAT_CLUSTER_MIN_CONFIDENCE=1.3,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_cluster_f_beta():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_CLUSTER_F_BETA"):
        Settings(
            CLINICAL_CHAT_CLUSTER_F_BETA=0.1,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_hcluster_method():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_HCLUSTER_METHOD"):
        Settings(
            CLINICAL_CHAT_HCLUSTER_METHOD="ward",
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_hcluster_k_bounds():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_HCLUSTER_K_MIN"):
        Settings(
            CLINICAL_CHAT_HCLUSTER_K_MIN=9,
            CLINICAL_CHAT_HCLUSTER_K_MAX=4,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_hcluster_min_confidence():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_HCLUSTER_MIN_CONFIDENCE"):
        Settings(
            CLINICAL_CHAT_HCLUSTER_MIN_CONFIDENCE=1.4,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_hcluster_f_beta():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_HCLUSTER_F_BETA"):
        Settings(
            CLINICAL_CHAT_HCLUSTER_F_BETA=0.1,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_svm_domain_c():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_SVM_DOMAIN_C"):
        Settings(
            CLINICAL_CHAT_SVM_DOMAIN_C=0.0,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_svm_domain_l2():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_SVM_DOMAIN_L2"):
        Settings(
            CLINICAL_CHAT_SVM_DOMAIN_L2=2.0,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_svm_domain_epochs():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_SVM_DOMAIN_EPOCHS"):
        Settings(
            CLINICAL_CHAT_SVM_DOMAIN_EPOCHS=0,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_svm_domain_min_confidence():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_SVM_DOMAIN_MIN_CONFIDENCE"):
        Settings(
            CLINICAL_CHAT_SVM_DOMAIN_MIN_CONFIDENCE=1.5,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_empty_web_link_analysis_path():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_WEB_LINK_ANALYSIS_PATH"):
        Settings(
            CLINICAL_CHAT_WEB_LINK_ANALYSIS_PATH=" ",
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_web_link_analysis_blend():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_WEB_LINK_ANALYSIS_BLEND"):
        Settings(
            CLINICAL_CHAT_WEB_LINK_ANALYSIS_BLEND=1.2,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_web_link_analysis_max_hits_base():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_WEB_LINK_ANALYSIS_MAX_HITS_BASE"):
        Settings(
            CLINICAL_CHAT_WEB_LINK_ANALYSIS_MAX_HITS_BASE=5,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_qa_shortcut_min_score():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_QA_SHORTCUT_MIN_SCORE"):
        Settings(
            CLINICAL_CHAT_RAG_QA_SHORTCUT_MIN_SCORE=1.5,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_qa_shortcut_max_candidates():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_QA_SHORTCUT_MAX_CANDIDATES"):
        Settings(
            CLINICAL_CHAT_RAG_QA_SHORTCUT_MAX_CANDIDATES=5,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_multi_intent_max_segments():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_MULTI_INTENT_MAX_SEGMENTS"):
        Settings(
            CLINICAL_CHAT_RAG_MULTI_INTENT_MAX_SEGMENTS=0,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_action_min_score():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_ACTION_MIN_SCORE"):
        Settings(
            CLINICAL_CHAT_RAG_ACTION_MIN_SCORE=1.5,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_verifier_min_score():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_VERIFIER_MIN_SCORE"):
        Settings(
            CLINICAL_CHAT_RAG_VERIFIER_MIN_SCORE=1.2,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_verifier_min_chunks():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_VERIFIER_MIN_CHUNKS"):
        Settings(
            CLINICAL_CHAT_RAG_VERIFIER_MIN_CHUNKS=0,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_ecorag_min_evidentiality():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_ECORAG_MIN_EVIDENTIALITY"):
        Settings(
            CLINICAL_CHAT_RAG_ECORAG_MIN_EVIDENTIALITY=1.8,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )


def test_rejects_invalid_ecorag_min_chunks():
    with pytest.raises(ValueError, match="CLINICAL_CHAT_RAG_ECORAG_MIN_CHUNKS"):
        Settings(
            CLINICAL_CHAT_RAG_ECORAG_MIN_CHUNKS=0,
            BACKEND_CORS_ORIGINS=["http://localhost:5173"],
        )
