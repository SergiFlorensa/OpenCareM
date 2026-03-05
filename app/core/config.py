"""
Configuracion de ajustes del proyecto.
"""
from typing import List

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_SECRET_KEY = "tu-super-secreto-cambialo-en-produccion-12345"


class Settings(BaseSettings):
    """Configuracion global de la aplicacion."""

    APP_NAME: str = "API Gestor de Tareas"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"

    API_V1_PREFIX: str = "/api/v1"

    SECRET_KEY: str = DEFAULT_SECRET_KEY
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    LOGIN_MAX_ATTEMPTS: int = 5
    LOGIN_WINDOW_MINUTES: int = 5
    LOGIN_BLOCK_MINUTES: int = 10
    AI_TRIAGE_MODE: str = "rules"
    CLINICAL_CHAT_WEB_ENABLED: bool = True
    CLINICAL_CHAT_WEB_TIMEOUT_SECONDS: int = 6
    CLINICAL_CHAT_WEB_STRICT_WHITELIST: bool = True
    CLINICAL_CHAT_WEB_ALLOWED_DOMAINS: str = (
        "who.int,cdc.gov,nih.gov,pubmed.ncbi.nlm.nih.gov,scielo.org,"
        "nejm.org,thelancet.com,bmj.com,jamanetwork.com,seimc.org,"
        "semicyuc.org,semes.org,guiasalud.es,openevidence.com"
    )
    CLINICAL_CHAT_WEB_LINK_ANALYSIS_ENABLED: bool = True
    CLINICAL_CHAT_WEB_LINK_ANALYSIS_PATH: str = "docs/web_raw/link_analysis_snapshot.json"
    CLINICAL_CHAT_WEB_LINK_ANALYSIS_BLEND: float = 0.35
    CLINICAL_CHAT_WEB_LINK_ANALYSIS_MAX_HITS_BASE: int = 120
    CLINICAL_CHAT_PDF_PARSER_BACKEND: str = "pypdf"
    CLINICAL_CHAT_PDF_MINERU_BASE_URL: str = "http://127.0.0.1:8091"
    CLINICAL_CHAT_PDF_MINERU_TIMEOUT_SECONDS: int = 90
    CLINICAL_CHAT_PDF_MINERU_FAIL_OPEN: bool = True
    CLINICAL_CHAT_PDF_OCR_MODE: str = "region_selective"
    CLINICAL_CHAT_PDF_LAYOUT_READING_ORDER_ENABLED: bool = True
    CLINICAL_CHAT_PDF_FILTER_REPEATED_EDGE_TEXT_ENABLED: bool = True
    CLINICAL_CHAT_PDF_FILTER_REPEATED_EDGE_TEXT_MIN_PAGES: int = 2
    CLINICAL_CHAT_PDF_TELEMETRY_ENABLED: bool = True
    CLINICAL_CHAT_REQUIRE_VALIDATED_INTERNAL_SOURCES: bool = True
    CLINICAL_CHAT_LLM_ENABLED: bool = False
    CLINICAL_CHAT_LLM_PROVIDER: str = "ollama"
    CLINICAL_CHAT_LLM_BASE_URL: str = "http://127.0.0.1:11434"
    CLINICAL_CHAT_LLM_API_KEY: str = ""
    CLINICAL_CHAT_LLM_MODEL: str = "llama3.2:3b"
    CLINICAL_CHAT_LLM_TIMEOUT_SECONDS: int = 9
    CLINICAL_CHAT_LLM_MAX_OUTPUT_TOKENS: int = 80
    CLINICAL_CHAT_LLM_MAX_INPUT_TOKENS: int = 320
    CLINICAL_CHAT_LLM_PROMPT_MARGIN_TOKENS: int = 80
    CLINICAL_CHAT_LLM_TEMPERATURE: float = 0.1
    CLINICAL_CHAT_LLM_NUM_CTX: int = 896
    CLINICAL_CHAT_LLM_TOP_P: float = 0.9
    CLINICAL_CHAT_LLM_MAX_DIALOGUE_TURNS: int = 3
    CLINICAL_CHAT_LLM_MAX_CONTEXT_UTILIZATION_RATIO: float = 0.40
    CLINICAL_CHAT_LLM_NATIVE_STYLE_ENABLED: bool = True
    CLINICAL_CHAT_LLM_REWRITE_ENABLED: bool = True
    CLINICAL_CHAT_LLM_QUALITY_GATES_ENABLED: bool = True
    CLINICAL_CHAT_LLM_CIRCUIT_BREAKER_ENABLED: bool = True
    CLINICAL_CHAT_LLM_CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 2
    CLINICAL_CHAT_LLM_CIRCUIT_BREAKER_OPEN_SECONDS: int = 90
    CLINICAL_CHAT_NB_ENABLED: bool = True
    CLINICAL_CHAT_NB_MODEL: str = "multinomial"
    CLINICAL_CHAT_NB_ALPHA: float = 1.0
    CLINICAL_CHAT_NB_MIN_CONFIDENCE: float = 0.25
    CLINICAL_CHAT_NB_FEATURE_METHOD: str = "chi2"
    CLINICAL_CHAT_NB_MAX_FEATURES: int = 256
    CLINICAL_CHAT_NB_RERANK_WHEN_MATH_UNCERTAIN_ONLY: bool = True
    CLINICAL_CHAT_VECTOR_ENABLED: bool = True
    CLINICAL_CHAT_VECTOR_METHOD: str = "rocchio"
    CLINICAL_CHAT_VECTOR_K: int = 5
    CLINICAL_CHAT_VECTOR_MIN_CONFIDENCE: float = 0.05
    CLINICAL_CHAT_VECTOR_RERANK_WHEN_MATH_UNCERTAIN_ONLY: bool = True
    CLINICAL_CHAT_CLUSTER_ENABLED: bool = True
    CLINICAL_CHAT_CLUSTER_METHOD: str = "kmeans_em"
    CLINICAL_CHAT_CLUSTER_K_MIN: int = 3
    CLINICAL_CHAT_CLUSTER_K_MAX: int = 8
    CLINICAL_CHAT_CLUSTER_MAX_ITERATIONS: int = 20
    CLINICAL_CHAT_CLUSTER_EM_ITERATIONS: int = 8
    CLINICAL_CHAT_CLUSTER_MIN_CONFIDENCE: float = 0.08
    CLINICAL_CHAT_CLUSTER_RERANK_WHEN_MATH_UNCERTAIN_ONLY: bool = True
    CLINICAL_CHAT_CLUSTER_F_BETA: float = 1.2
    CLINICAL_CHAT_HCLUSTER_ENABLED: bool = True
    CLINICAL_CHAT_HCLUSTER_METHOD: str = "hac_average"
    CLINICAL_CHAT_HCLUSTER_K_MIN: int = 3
    CLINICAL_CHAT_HCLUSTER_K_MAX: int = 8
    CLINICAL_CHAT_HCLUSTER_MIN_CONFIDENCE: float = 0.08
    CLINICAL_CHAT_HCLUSTER_RERANK_WHEN_MATH_UNCERTAIN_ONLY: bool = True
    CLINICAL_CHAT_HCLUSTER_F_BETA: float = 1.2
    CLINICAL_CHAT_HCLUSTER_BUCKSHOT_SAMPLE_SCALE: float = 1.0
    CLINICAL_CHAT_HCLUSTER_MAX_CANDIDATE_DOMAINS: int = 6
    CLINICAL_CHAT_SVM_DOMAIN_ENABLED: bool = True
    CLINICAL_CHAT_SVM_DOMAIN_C: float = 1.0
    CLINICAL_CHAT_SVM_DOMAIN_L2: float = 0.05
    CLINICAL_CHAT_SVM_DOMAIN_EPOCHS: int = 12
    CLINICAL_CHAT_SVM_DOMAIN_MIN_CONFIDENCE: float = 0.10
    CLINICAL_CHAT_SVM_DOMAIN_RERANK_WHEN_MATH_UNCERTAIN_ONLY: bool = True
    CLINICAL_CHAT_RAG_ENABLED: bool = False
    CLINICAL_CHAT_RAG_MAX_CHUNKS: int = 2
    CLINICAL_CHAT_RAG_VECTOR_WEIGHT: float = 0.5
    CLINICAL_CHAT_RAG_KEYWORD_WEIGHT: float = 0.5
    CLINICAL_CHAT_RAG_EMBEDDING_MODEL: str = "nomic-embed-text"
    CLINICAL_CHAT_RAG_ENABLE_GATEKEEPER: bool = True
    CLINICAL_CHAT_RAG_EXTRACTIVE_FALLBACK_ENABLED: bool = True
    CLINICAL_CHAT_RAG_EXTRACTIVE_FALLBACK_MAX_ITEMS: int = 5
    CLINICAL_CHAT_RAG_FORCE_EXTRACTIVE_ONLY: bool = False
    CLINICAL_CHAT_RAG_FACT_ONLY_MODE_ENABLED: bool = False
    CLINICAL_CHAT_RAG_EARLY_GOAL_TEST_ENABLED: bool = True
    CLINICAL_CHAT_RAG_EARLY_GOAL_MIN_SCORE: float = 0.62
    CLINICAL_CHAT_RAG_EARLY_GOAL_MIN_ACTIONABILITY: float = 0.55
    CLINICAL_CHAT_RAG_EARLY_GOAL_MIN_RETRIEVAL_SCORE: float = 0.20
    CLINICAL_CHAT_RAG_QUERY_CACHE_ENABLED: bool = True
    CLINICAL_CHAT_RAG_QUERY_CACHE_TTL_SECONDS: int = 300
    CLINICAL_CHAT_RAG_QUERY_CACHE_MAX_ENTRIES: int = 256
    CLINICAL_CHAT_RAG_DISCOURSE_COHERENCE_ENABLED: bool = True
    CLINICAL_CHAT_RAG_DISCOURSE_MIN_SCORE: float = 0.24
    CLINICAL_CHAT_RAG_DISCOURSE_MAX_SATELLITE_RATIO: float = 0.60
    CLINICAL_CHAT_RAG_DISCOURSE_LCD_MIN_SCORE: float = 0.20
    CLINICAL_CHAT_RAG_QA_SHORTCUT_ENABLED: bool = True
    CLINICAL_CHAT_RAG_QA_SHORTCUT_MIN_SCORE: float = 0.24
    CLINICAL_CHAT_RAG_QA_SHORTCUT_TOP_K: int = 2
    CLINICAL_CHAT_RAG_QA_SHORTCUT_MAX_CANDIDATES: int = 80
    CLINICAL_CHAT_RAG_MULTI_INTENT_ENABLED: bool = True
    CLINICAL_CHAT_RAG_MULTI_INTENT_MAX_SEGMENTS: int = 4
    CLINICAL_CHAT_RAG_MULTI_INTENT_MIN_SEGMENT_CHARS: int = 18
    CLINICAL_CHAT_RAG_MULTI_INTENT_MIN_DOMAIN_PROBABILITY: float = 0.18
    CLINICAL_CHAT_RAG_HYDE_ENABLED: bool = True
    CLINICAL_CHAT_RAG_ACTION_FOCUS_ENABLED: bool = True
    CLINICAL_CHAT_RAG_ACTION_MIN_SCORE: float = 0.26
    CLINICAL_CHAT_RAG_ACTION_MAX_AUX_RATIO: float = 0.60
    CLINICAL_CHAT_RAG_VERIFIER_ENABLED: bool = False
    CLINICAL_CHAT_RAG_VERIFIER_MIN_SCORE: float = 0.50
    CLINICAL_CHAT_RAG_VERIFIER_MIN_CHUNKS: int = 2
    CLINICAL_CHAT_RAG_VERIFIER_BM25_FALLBACK_ENABLED: bool = True
    CLINICAL_CHAT_RAG_ECORAG_ENABLED: bool = False
    CLINICAL_CHAT_RAG_ECORAG_MIN_EVIDENTIALITY: float = 0.52
    CLINICAL_CHAT_RAG_ECORAG_MIN_CHUNKS: int = 2
    CLINICAL_CHAT_RAG_MAX_TOTAL_LATENCY_MS: int = 3000
    CLINICAL_CHAT_RAG_LLM_MIN_REMAINING_BUDGET_MS: int = 700
    CLINICAL_CHAT_RAG_PARALLEL_HYBRID_ENABLED: bool = True
    CLINICAL_CHAT_RAG_FAITHFULNESS_MIN_RATIO: float = 0.20
    CLINICAL_CHAT_RAG_CONTEXT_MIN_RATIO: float = 0.08
    CLINICAL_CHAT_RAG_ADAPTIVE_K_ENABLED: bool = True
    CLINICAL_CHAT_RAG_MIN_CHUNKS: int = 2
    CLINICAL_CHAT_RAG_MAX_CHUNKS_HARD: int = 6
    CLINICAL_CHAT_RAG_MMR_ENABLED: bool = False
    CLINICAL_CHAT_RAG_MMR_LAMBDA: float = 0.70
    CLINICAL_CHAT_RAG_COMPRESS_CONTEXT_ENABLED: bool = True
    CLINICAL_CHAT_RAG_COMPRESS_MAX_CHARS: int = 280
    CLINICAL_CHAT_RAG_FTS_CANDIDATE_ENABLED: bool = True
    CLINICAL_CHAT_RAG_FTS_CANDIDATE_POOL: int = 88
    CLINICAL_CHAT_RAG_SKIP_DOMAIN_SEARCH_TOKENS_OVER: int = 12
    CLINICAL_CHAT_RAG_DETERMINISTIC_ROUTING_ENABLED: bool = True
    CLINICAL_CHAT_RAG_DETERMINISTIC_COMPLEX_MIN_TOKENS: int = 10
    CLINICAL_CHAT_RAG_SIMPLE_ROUTE_MAX_CHUNKS: int = 2
    CLINICAL_CHAT_RAG_COMPLEX_ROUTE_FORCE_SKIP_DOMAIN_SEARCH: bool = True
    CLINICAL_CHAT_RAG_SAFE_WRAPPER_ENABLED: bool = True
    CLINICAL_CHAT_RAG_SAFE_WRAPPER_MIN_CONTEXT_RATIO: float = 0.10
    CLINICAL_CHAT_RAG_SPELL_CORRECTION_ENABLED: bool = True
    CLINICAL_CHAT_RAG_SPELL_MAX_EDIT_DISTANCE: int = 2
    CLINICAL_CHAT_RAG_SPELL_TRIGGER_MAX_POSTINGS: int = 4
    CLINICAL_CHAT_RAG_WILDCARD_ENABLED: bool = True
    CLINICAL_CHAT_RAG_WILDCARD_MAX_EXPANSIONS: int = 16
    CLINICAL_CHAT_RAG_KGRAM_SIZE: int = 3
    CLINICAL_CHAT_RAG_KGRAM_JACCARD_MIN: float = 0.18
    CLINICAL_CHAT_RAG_SOUNDEX_ENABLED: bool = True
    CLINICAL_CHAT_RAG_CONTEXTUAL_SPELL_ENABLED: bool = True
    CLINICAL_CHAT_RAG_CONTEXTUAL_SPELL_MAX_CANDIDATES: int = 10
    CLINICAL_CHAT_RAG_VOCAB_CACHE_ENABLED: bool = True
    CLINICAL_CHAT_RAG_VOCAB_CACHE_MAX_TERMS: int = 120000
    CLINICAL_CHAT_RAG_VOCAB_CACHE_TTL_SECONDS: int = 600
    CLINICAL_CHAT_RAG_POSTINGS_CACHE_ENABLED: bool = True
    CLINICAL_CHAT_RAG_POSTINGS_CACHE_MAX_ENTRIES: int = 4000
    CLINICAL_CHAT_RAG_POSTINGS_CACHE_TTL_SECONDS: int = 600
    CLINICAL_CHAT_RAG_POSTINGS_CACHE_ENCODING: str = "vb"
    CLINICAL_CHAT_RAG_ZONE_WEIGHT_TITLE: float = 0.28
    CLINICAL_CHAT_RAG_ZONE_WEIGHT_SECTION: float = 0.24
    CLINICAL_CHAT_RAG_ZONE_WEIGHT_BODY: float = 0.28
    CLINICAL_CHAT_RAG_ZONE_WEIGHT_KEYWORDS: float = 0.12
    CLINICAL_CHAT_RAG_ZONE_WEIGHT_CUSTOM_QUESTIONS: float = 0.08
    CLINICAL_CHAT_RAG_TFIDF_MAX_QUERY_TERMS: int = 24
    CLINICAL_CHAT_RAG_TFIDF_PIVOT_SLOPE: float = 0.20
    CLINICAL_CHAT_RAG_TFIDF_ZONE_BLEND: float = 0.20
    CLINICAL_CHAT_RAG_IDF_TERM_PRUNING_ENABLED: bool = True
    CLINICAL_CHAT_RAG_IDF_MIN_THRESHOLD: float = 1.15
    CLINICAL_CHAT_RAG_IDF_MIN_KEEP_TERMS: int = 4
    CLINICAL_CHAT_RAG_PROXIMITY_BONUS_ENABLED: bool = True
    CLINICAL_CHAT_RAG_PROXIMITY_BONUS_WEIGHT: float = 0.10
    CLINICAL_CHAT_RAG_STATIC_QUALITY_ENABLED: bool = True
    CLINICAL_CHAT_RAG_STATIC_QUALITY_WEIGHT: float = 0.12
    CLINICAL_CHAT_RAG_TIERED_RANKING_ENABLED: bool = True
    CLINICAL_CHAT_RAG_TIER1_MIN_STATIC_QUALITY: float = 0.55
    CLINICAL_CHAT_RAG_GLOBAL_THESAURUS_ENABLED: bool = True
    CLINICAL_CHAT_RAG_GLOBAL_THESAURUS_PATH: str = "docs/clinical_thesaurus_es_en.json"
    CLINICAL_CHAT_RAG_GLOBAL_THESAURUS_TTL_SECONDS: int = 600
    CLINICAL_CHAT_RAG_GLOBAL_THESAURUS_MAX_EXPANSIONS_PER_TERM: int = 4
    CLINICAL_CHAT_RAG_PRF_ENABLED: bool = False
    CLINICAL_CHAT_RAG_PRF_TOPK: int = 3
    CLINICAL_CHAT_RAG_PRF_MAX_TERMS: int = 6
    CLINICAL_CHAT_RAG_PRF_MIN_TERM_LEN: int = 5
    CLINICAL_CHAT_RAG_PRF_ALPHA: float = 1.0
    CLINICAL_CHAT_RAG_PRF_BETA: float = 0.75
    CLINICAL_CHAT_RAG_PRF_GAMMA: float = 0.0
    CLINICAL_CHAT_RAG_BM25_ENABLED: bool = True
    CLINICAL_CHAT_RAG_BM25_K1: float = 1.5
    CLINICAL_CHAT_RAG_BM25_B: float = 0.75
    CLINICAL_CHAT_RAG_BM25_BLEND: float = 0.65
    CLINICAL_CHAT_RAG_BIM_BINARY_BONUS_ENABLED: bool = True
    CLINICAL_CHAT_RAG_BIM_BINARY_BONUS_WEIGHT: float = 0.10
    CLINICAL_CHAT_RAG_QLM_ENABLED: bool = True
    CLINICAL_CHAT_RAG_QLM_SMOOTHING: str = "dirichlet"
    CLINICAL_CHAT_RAG_QLM_DIRICHLET_MU: float = 1200.0
    CLINICAL_CHAT_RAG_QLM_JM_LAMBDA: float = 0.2
    CLINICAL_CHAT_RAG_QLM_BLEND: float = 0.30
    CLINICAL_CHAT_RAG_LSI_ENABLED: bool = False
    CLINICAL_CHAT_RAG_LSI_K: int = 64
    CLINICAL_CHAT_RAG_LSI_BLEND: float = 0.20
    CLINICAL_CHAT_RAG_LSI_MAX_VOCAB_TERMS: int = 600
    CLINICAL_CHAT_RAG_LSI_MIN_DOCS: int = 4
    CLINICAL_CHAT_RAG_SKIP_POINTERS_ENABLED: bool = True
    CLINICAL_CHAT_RAG_SKIP_POINTERS_MIN_LIST: int = 96
    CLINICAL_CHAT_RAG_RETRIEVER_BACKEND: str = "legacy"
    CLINICAL_CHAT_RAG_LLAMAINDEX_CANDIDATE_POOL: int = 120
    CLINICAL_CHAT_RAG_CHROMA_CANDIDATE_POOL: int = 200
    CLINICAL_CHAT_RAG_ELASTIC_URL: str = "http://127.0.0.1:9200"
    CLINICAL_CHAT_RAG_ELASTIC_INDEX: str = "clinical_chunks"
    CLINICAL_CHAT_RAG_ELASTIC_TIMEOUT_SECONDS: int = 2
    CLINICAL_CHAT_RAG_ELASTIC_CANDIDATE_POOL: int = 160
    CLINICAL_CHAT_RAG_ELASTIC_TEXT_FIELDS: str = (
        "chunk_text^3,section_path^2,keywords_text^2,custom_questions_text^2,source_file"
    )
    CLINICAL_CHAT_RAG_ELASTIC_SEMANTIC_FIELD: str = "semantic_content"
    CLINICAL_CHAT_RAG_ELASTIC_VERIFY_TLS: bool = True
    CLINICAL_CHAT_RAG_ELASTIC_USERNAME: str = ""
    CLINICAL_CHAT_RAG_ELASTIC_PASSWORD: str = ""
    CLINICAL_CHAT_RAG_ELASTIC_API_KEY: str = ""
    CLINICAL_CHAT_UNCERTAINTY_GATE_ENABLED: bool = True
    CLINICAL_CHAT_UNCERTAINTY_GATE_MAX_VARIANCE: float = 0.24
    CLINICAL_CHAT_UNCERTAINTY_GATE_FAILFAST_ON_RAG: bool = False
    CLINICAL_CHAT_GUARDRAILS_ENABLED: bool = False
    CLINICAL_CHAT_GUARDRAILS_CONFIG_PATH: str = "app/guardrails"
    CLINICAL_CHAT_GUARDRAILS_FAIL_OPEN: bool = True

    DATABASE_URL: str = "sqlite:///./task_manager.db"
    DATABASE_ECHO: bool = False

    REDIS_URL: str = "redis://localhost:6379/0"

    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://localhost:8080",
    ]

    LOG_LEVEL: str = "INFO"

    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="allow",
    )

    @model_validator(mode="after")
    def validate_security_baseline(self):
        if self.AI_TRIAGE_MODE not in {"rules", "hybrid"}:
            raise ValueError("AI_TRIAGE_MODE debe ser 'rules' o 'hybrid'.")
        if self.CLINICAL_CHAT_WEB_TIMEOUT_SECONDS < 1:
            raise ValueError("CLINICAL_CHAT_WEB_TIMEOUT_SECONDS debe ser >= 1.")
        if self.CLINICAL_CHAT_WEB_STRICT_WHITELIST and not self.CLINICAL_CHAT_WEB_ALLOWED_DOMAINS:
            raise ValueError(
                "CLINICAL_CHAT_WEB_ALLOWED_DOMAINS no puede estar vacio con whitelist estricta."
            )
        if not self.CLINICAL_CHAT_WEB_LINK_ANALYSIS_PATH.strip():
            raise ValueError("CLINICAL_CHAT_WEB_LINK_ANALYSIS_PATH no puede estar vacio.")
        if not (0 <= self.CLINICAL_CHAT_WEB_LINK_ANALYSIS_BLEND <= 1):
            raise ValueError("CLINICAL_CHAT_WEB_LINK_ANALYSIS_BLEND debe estar entre 0 y 1.")
        if not (20 <= self.CLINICAL_CHAT_WEB_LINK_ANALYSIS_MAX_HITS_BASE <= 2000):
            raise ValueError(
                "CLINICAL_CHAT_WEB_LINK_ANALYSIS_MAX_HITS_BASE debe estar entre 20 y 2000."
            )
        if self.CLINICAL_CHAT_PDF_PARSER_BACKEND not in {"pypdf", "mineru"}:
            raise ValueError(
                "CLINICAL_CHAT_PDF_PARSER_BACKEND debe ser 'pypdf' o 'mineru'."
            )
        if not self.CLINICAL_CHAT_PDF_MINERU_BASE_URL.strip():
            raise ValueError("CLINICAL_CHAT_PDF_MINERU_BASE_URL no puede estar vacio.")
        if not (10 <= self.CLINICAL_CHAT_PDF_MINERU_TIMEOUT_SECONDS <= 600):
            raise ValueError(
                "CLINICAL_CHAT_PDF_MINERU_TIMEOUT_SECONDS debe estar entre 10 y 600."
            )
        if self.CLINICAL_CHAT_PDF_OCR_MODE not in {"region_selective", "page_full"}:
            raise ValueError(
                "CLINICAL_CHAT_PDF_OCR_MODE debe ser 'region_selective' o 'page_full'."
            )
        if not (2 <= self.CLINICAL_CHAT_PDF_FILTER_REPEATED_EDGE_TEXT_MIN_PAGES <= 20):
            raise ValueError(
                "CLINICAL_CHAT_PDF_FILTER_REPEATED_EDGE_TEXT_MIN_PAGES debe estar entre 2 y 20."
            )
        if self.CLINICAL_CHAT_LLM_PROVIDER not in {"ollama", "llama_cpp"}:
            raise ValueError("CLINICAL_CHAT_LLM_PROVIDER debe ser 'ollama' o 'llama_cpp'.")
        if self.CLINICAL_CHAT_LLM_TIMEOUT_SECONDS < 2:
            raise ValueError("CLINICAL_CHAT_LLM_TIMEOUT_SECONDS debe ser >= 2.")
        if not (0 <= self.CLINICAL_CHAT_LLM_MAX_DIALOGUE_TURNS <= 10):
            raise ValueError("CLINICAL_CHAT_LLM_MAX_DIALOGUE_TURNS debe estar entre 0 y 10.")
        if not (0.20 <= self.CLINICAL_CHAT_LLM_MAX_CONTEXT_UTILIZATION_RATIO <= 0.80):
            raise ValueError(
                "CLINICAL_CHAT_LLM_MAX_CONTEXT_UTILIZATION_RATIO debe estar entre 0.20 y 0.80."
            )
        if self.CLINICAL_CHAT_LLM_CIRCUIT_BREAKER_FAILURE_THRESHOLD < 1:
            raise ValueError(
                "CLINICAL_CHAT_LLM_CIRCUIT_BREAKER_FAILURE_THRESHOLD debe ser >= 1."
            )
        if self.CLINICAL_CHAT_LLM_CIRCUIT_BREAKER_OPEN_SECONDS < 1:
            raise ValueError(
                "CLINICAL_CHAT_LLM_CIRCUIT_BREAKER_OPEN_SECONDS debe ser >= 1."
            )
        if not (0 <= self.CLINICAL_CHAT_LLM_TEMPERATURE <= 1):
            raise ValueError("CLINICAL_CHAT_LLM_TEMPERATURE debe estar entre 0 y 1.")
        if not (0 < self.CLINICAL_CHAT_LLM_TOP_P <= 1):
            raise ValueError("CLINICAL_CHAT_LLM_TOP_P debe estar en rango (0, 1].")
        if self.CLINICAL_CHAT_LLM_MAX_OUTPUT_TOKENS < 64:
            raise ValueError("CLINICAL_CHAT_LLM_MAX_OUTPUT_TOKENS debe ser >= 64.")
        if self.CLINICAL_CHAT_LLM_MAX_INPUT_TOKENS < 256:
            raise ValueError("CLINICAL_CHAT_LLM_MAX_INPUT_TOKENS debe ser >= 256.")
        if self.CLINICAL_CHAT_LLM_PROMPT_MARGIN_TOKENS < 32:
            raise ValueError("CLINICAL_CHAT_LLM_PROMPT_MARGIN_TOKENS debe ser >= 32.")
        if self.CLINICAL_CHAT_LLM_NUM_CTX < 512:
            raise ValueError("CLINICAL_CHAT_LLM_NUM_CTX debe ser >= 512.")
        if self.CLINICAL_CHAT_LLM_NUM_CTX <= (
            self.CLINICAL_CHAT_LLM_MAX_OUTPUT_TOKENS + self.CLINICAL_CHAT_LLM_PROMPT_MARGIN_TOKENS
        ):
            raise ValueError(
                "CLINICAL_CHAT_LLM_NUM_CTX debe superar salida maxima + margen de prompt."
            )
        if self.CLINICAL_CHAT_NB_MODEL not in {"multinomial", "bernoulli"}:
            raise ValueError("CLINICAL_CHAT_NB_MODEL debe ser 'multinomial' o 'bernoulli'.")
        if not (0.01 <= self.CLINICAL_CHAT_NB_ALPHA <= 5):
            raise ValueError("CLINICAL_CHAT_NB_ALPHA debe estar entre 0.01 y 5.")
        if not (0 <= self.CLINICAL_CHAT_NB_MIN_CONFIDENCE <= 1):
            raise ValueError("CLINICAL_CHAT_NB_MIN_CONFIDENCE debe estar entre 0 y 1.")
        if self.CLINICAL_CHAT_NB_FEATURE_METHOD not in {"chi2", "mi", "none"}:
            raise ValueError(
                "CLINICAL_CHAT_NB_FEATURE_METHOD debe ser 'chi2', 'mi' o 'none'."
            )
        if not (32 <= self.CLINICAL_CHAT_NB_MAX_FEATURES <= 2000):
            raise ValueError("CLINICAL_CHAT_NB_MAX_FEATURES debe estar entre 32 y 2000.")
        if self.CLINICAL_CHAT_VECTOR_METHOD not in {"rocchio", "knn", "hybrid"}:
            raise ValueError(
                "CLINICAL_CHAT_VECTOR_METHOD debe ser 'rocchio', 'knn' o 'hybrid'."
            )
        if not (1 <= self.CLINICAL_CHAT_VECTOR_K <= 25):
            raise ValueError("CLINICAL_CHAT_VECTOR_K debe estar entre 1 y 25.")
        if not (0 <= self.CLINICAL_CHAT_VECTOR_MIN_CONFIDENCE <= 1):
            raise ValueError("CLINICAL_CHAT_VECTOR_MIN_CONFIDENCE debe estar entre 0 y 1.")
        if self.CLINICAL_CHAT_CLUSTER_METHOD not in {"kmeans", "kmeans_em"}:
            raise ValueError(
                "CLINICAL_CHAT_CLUSTER_METHOD debe ser 'kmeans' o 'kmeans_em'."
            )
        if not (1 <= self.CLINICAL_CHAT_CLUSTER_K_MIN <= 20):
            raise ValueError("CLINICAL_CHAT_CLUSTER_K_MIN debe estar entre 1 y 20.")
        if not (1 <= self.CLINICAL_CHAT_CLUSTER_K_MAX <= 30):
            raise ValueError("CLINICAL_CHAT_CLUSTER_K_MAX debe estar entre 1 y 30.")
        if self.CLINICAL_CHAT_CLUSTER_K_MIN > self.CLINICAL_CHAT_CLUSTER_K_MAX:
            raise ValueError(
                "CLINICAL_CHAT_CLUSTER_K_MIN no puede ser mayor que CLINICAL_CHAT_CLUSTER_K_MAX."
            )
        if not (5 <= self.CLINICAL_CHAT_CLUSTER_MAX_ITERATIONS <= 100):
            raise ValueError(
                "CLINICAL_CHAT_CLUSTER_MAX_ITERATIONS debe estar entre 5 y 100."
            )
        if not (1 <= self.CLINICAL_CHAT_CLUSTER_EM_ITERATIONS <= 50):
            raise ValueError(
                "CLINICAL_CHAT_CLUSTER_EM_ITERATIONS debe estar entre 1 y 50."
            )
        if not (0 <= self.CLINICAL_CHAT_CLUSTER_MIN_CONFIDENCE <= 1):
            raise ValueError(
                "CLINICAL_CHAT_CLUSTER_MIN_CONFIDENCE debe estar entre 0 y 1."
            )
        if not (0.5 <= self.CLINICAL_CHAT_CLUSTER_F_BETA <= 3.0):
            raise ValueError("CLINICAL_CHAT_CLUSTER_F_BETA debe estar entre 0.5 y 3.0.")
        if self.CLINICAL_CHAT_HCLUSTER_METHOD not in {
            "hac_single",
            "hac_complete",
            "hac_average",
            "divisive",
            "buckshot",
        }:
            raise ValueError(
                "CLINICAL_CHAT_HCLUSTER_METHOD debe ser "
                "'hac_single', 'hac_complete', 'hac_average', 'divisive' o 'buckshot'."
            )
        if not (1 <= self.CLINICAL_CHAT_HCLUSTER_K_MIN <= 20):
            raise ValueError("CLINICAL_CHAT_HCLUSTER_K_MIN debe estar entre 1 y 20.")
        if not (1 <= self.CLINICAL_CHAT_HCLUSTER_K_MAX <= 30):
            raise ValueError("CLINICAL_CHAT_HCLUSTER_K_MAX debe estar entre 1 y 30.")
        if self.CLINICAL_CHAT_HCLUSTER_K_MIN > self.CLINICAL_CHAT_HCLUSTER_K_MAX:
            raise ValueError(
                "CLINICAL_CHAT_HCLUSTER_K_MIN no puede ser mayor que "
                "CLINICAL_CHAT_HCLUSTER_K_MAX."
            )
        if not (0 <= self.CLINICAL_CHAT_HCLUSTER_MIN_CONFIDENCE <= 1):
            raise ValueError(
                "CLINICAL_CHAT_HCLUSTER_MIN_CONFIDENCE debe estar entre 0 y 1."
            )
        if not (0.5 <= self.CLINICAL_CHAT_HCLUSTER_F_BETA <= 3.0):
            raise ValueError("CLINICAL_CHAT_HCLUSTER_F_BETA debe estar entre 0.5 y 3.0.")
        if not (0.5 <= self.CLINICAL_CHAT_HCLUSTER_BUCKSHOT_SAMPLE_SCALE <= 3.0):
            raise ValueError(
                "CLINICAL_CHAT_HCLUSTER_BUCKSHOT_SAMPLE_SCALE debe estar entre 0.5 y 3.0."
            )
        if not (1 <= self.CLINICAL_CHAT_HCLUSTER_MAX_CANDIDATE_DOMAINS <= 12):
            raise ValueError(
                "CLINICAL_CHAT_HCLUSTER_MAX_CANDIDATE_DOMAINS debe estar entre 1 y 12."
            )
        if not (0.05 <= self.CLINICAL_CHAT_SVM_DOMAIN_C <= 20):
            raise ValueError("CLINICAL_CHAT_SVM_DOMAIN_C debe estar entre 0.05 y 20.")
        if not (0.0001 <= self.CLINICAL_CHAT_SVM_DOMAIN_L2 <= 1.0):
            raise ValueError("CLINICAL_CHAT_SVM_DOMAIN_L2 debe estar entre 0.0001 y 1.0.")
        if not (1 <= self.CLINICAL_CHAT_SVM_DOMAIN_EPOCHS <= 100):
            raise ValueError("CLINICAL_CHAT_SVM_DOMAIN_EPOCHS debe estar entre 1 y 100.")
        if not (0 <= self.CLINICAL_CHAT_SVM_DOMAIN_MIN_CONFIDENCE <= 1):
            raise ValueError("CLINICAL_CHAT_SVM_DOMAIN_MIN_CONFIDENCE debe estar entre 0 y 1.")
        if not (1 <= self.CLINICAL_CHAT_RAG_MAX_CHUNKS <= 20):
            raise ValueError("CLINICAL_CHAT_RAG_MAX_CHUNKS debe estar entre 1 y 20.")
        if not (0 <= self.CLINICAL_CHAT_RAG_FAITHFULNESS_MIN_RATIO <= 1):
            raise ValueError("CLINICAL_CHAT_RAG_FAITHFULNESS_MIN_RATIO debe estar entre 0 y 1.")
        if not (0 <= self.CLINICAL_CHAT_RAG_CONTEXT_MIN_RATIO <= 1):
            raise ValueError("CLINICAL_CHAT_RAG_CONTEXT_MIN_RATIO debe estar entre 0 y 1.")
        if self.CLINICAL_CHAT_RAG_EXTRACTIVE_FALLBACK_MAX_ITEMS < 1:
            raise ValueError(
                "CLINICAL_CHAT_RAG_EXTRACTIVE_FALLBACK_MAX_ITEMS debe ser >= 1."
            )
        if not (0 <= self.CLINICAL_CHAT_RAG_EARLY_GOAL_MIN_SCORE <= 1):
            raise ValueError("CLINICAL_CHAT_RAG_EARLY_GOAL_MIN_SCORE debe estar entre 0 y 1.")
        if not (0 <= self.CLINICAL_CHAT_RAG_EARLY_GOAL_MIN_ACTIONABILITY <= 1):
            raise ValueError(
                "CLINICAL_CHAT_RAG_EARLY_GOAL_MIN_ACTIONABILITY debe estar entre 0 y 1."
            )
        if not (0 <= self.CLINICAL_CHAT_RAG_EARLY_GOAL_MIN_RETRIEVAL_SCORE <= 1):
            raise ValueError(
                "CLINICAL_CHAT_RAG_EARLY_GOAL_MIN_RETRIEVAL_SCORE debe estar entre 0 y 1."
            )
        if not (30 <= self.CLINICAL_CHAT_RAG_QUERY_CACHE_TTL_SECONDS <= 86400):
            raise ValueError(
                "CLINICAL_CHAT_RAG_QUERY_CACHE_TTL_SECONDS debe estar entre 30 y 86400."
            )
        if not (16 <= self.CLINICAL_CHAT_RAG_QUERY_CACHE_MAX_ENTRIES <= 10000):
            raise ValueError(
                "CLINICAL_CHAT_RAG_QUERY_CACHE_MAX_ENTRIES debe estar entre 16 y 10000."
            )
        if not (0 <= self.CLINICAL_CHAT_RAG_DISCOURSE_MIN_SCORE <= 1):
            raise ValueError("CLINICAL_CHAT_RAG_DISCOURSE_MIN_SCORE debe estar entre 0 y 1.")
        if not (0 <= self.CLINICAL_CHAT_RAG_DISCOURSE_MAX_SATELLITE_RATIO <= 1):
            raise ValueError(
                "CLINICAL_CHAT_RAG_DISCOURSE_MAX_SATELLITE_RATIO debe estar entre 0 y 1."
            )
        if not (0 <= self.CLINICAL_CHAT_RAG_DISCOURSE_LCD_MIN_SCORE <= 1):
            raise ValueError(
                "CLINICAL_CHAT_RAG_DISCOURSE_LCD_MIN_SCORE debe estar entre 0 y 1."
            )
        if not (0 <= self.CLINICAL_CHAT_RAG_QA_SHORTCUT_MIN_SCORE <= 1):
            raise ValueError(
                "CLINICAL_CHAT_RAG_QA_SHORTCUT_MIN_SCORE debe estar entre 0 y 1."
            )
        if not (1 <= self.CLINICAL_CHAT_RAG_QA_SHORTCUT_TOP_K <= 8):
            raise ValueError(
                "CLINICAL_CHAT_RAG_QA_SHORTCUT_TOP_K debe estar entre 1 y 8."
            )
        if not (20 <= self.CLINICAL_CHAT_RAG_QA_SHORTCUT_MAX_CANDIDATES <= 2000):
            raise ValueError(
                "CLINICAL_CHAT_RAG_QA_SHORTCUT_MAX_CANDIDATES debe estar entre 20 y 2000."
            )
        if not (1 <= self.CLINICAL_CHAT_RAG_MULTI_INTENT_MAX_SEGMENTS <= 8):
            raise ValueError(
                "CLINICAL_CHAT_RAG_MULTI_INTENT_MAX_SEGMENTS debe estar entre 1 y 8."
            )
        if not (8 <= self.CLINICAL_CHAT_RAG_MULTI_INTENT_MIN_SEGMENT_CHARS <= 120):
            raise ValueError(
                "CLINICAL_CHAT_RAG_MULTI_INTENT_MIN_SEGMENT_CHARS debe estar entre 8 y 120."
            )
        if not (0 <= self.CLINICAL_CHAT_RAG_MULTI_INTENT_MIN_DOMAIN_PROBABILITY <= 1):
            raise ValueError(
                "CLINICAL_CHAT_RAG_MULTI_INTENT_MIN_DOMAIN_PROBABILITY debe estar entre 0 y 1."
            )
        if not (0 <= self.CLINICAL_CHAT_RAG_ACTION_MIN_SCORE <= 1):
            raise ValueError("CLINICAL_CHAT_RAG_ACTION_MIN_SCORE debe estar entre 0 y 1.")
        if not (0 <= self.CLINICAL_CHAT_RAG_ACTION_MAX_AUX_RATIO <= 1):
            raise ValueError("CLINICAL_CHAT_RAG_ACTION_MAX_AUX_RATIO debe estar entre 0 y 1.")
        if not (0 <= self.CLINICAL_CHAT_RAG_VERIFIER_MIN_SCORE <= 1):
            raise ValueError("CLINICAL_CHAT_RAG_VERIFIER_MIN_SCORE debe estar entre 0 y 1.")
        if not (1 <= self.CLINICAL_CHAT_RAG_VERIFIER_MIN_CHUNKS <= 12):
            raise ValueError("CLINICAL_CHAT_RAG_VERIFIER_MIN_CHUNKS debe estar entre 1 y 12.")
        if not (0 <= self.CLINICAL_CHAT_RAG_ECORAG_MIN_EVIDENTIALITY <= 1):
            raise ValueError(
                "CLINICAL_CHAT_RAG_ECORAG_MIN_EVIDENTIALITY debe estar entre 0 y 1."
            )
        if not (1 <= self.CLINICAL_CHAT_RAG_ECORAG_MIN_CHUNKS <= 12):
            raise ValueError("CLINICAL_CHAT_RAG_ECORAG_MIN_CHUNKS debe estar entre 1 y 12.")
        if not (1000 <= self.CLINICAL_CHAT_RAG_MAX_TOTAL_LATENCY_MS <= 60000):
            raise ValueError(
                "CLINICAL_CHAT_RAG_MAX_TOTAL_LATENCY_MS debe estar entre 1000 y 60000."
            )
        if not (200 <= self.CLINICAL_CHAT_RAG_LLM_MIN_REMAINING_BUDGET_MS <= 10000):
            raise ValueError(
                "CLINICAL_CHAT_RAG_LLM_MIN_REMAINING_BUDGET_MS debe estar entre 200 y 10000."
            )
        if (
            self.CLINICAL_CHAT_RAG_LLM_MIN_REMAINING_BUDGET_MS
            >= self.CLINICAL_CHAT_RAG_MAX_TOTAL_LATENCY_MS
        ):
            raise ValueError(
                "CLINICAL_CHAT_RAG_LLM_MIN_REMAINING_BUDGET_MS debe ser menor que "
                "CLINICAL_CHAT_RAG_MAX_TOTAL_LATENCY_MS."
            )
        if not (1 <= self.CLINICAL_CHAT_RAG_MIN_CHUNKS <= 20):
            raise ValueError("CLINICAL_CHAT_RAG_MIN_CHUNKS debe estar entre 1 y 20.")
        if not (1 <= self.CLINICAL_CHAT_RAG_MAX_CHUNKS_HARD <= 30):
            raise ValueError("CLINICAL_CHAT_RAG_MAX_CHUNKS_HARD debe estar entre 1 y 30.")
        if self.CLINICAL_CHAT_RAG_MIN_CHUNKS > self.CLINICAL_CHAT_RAG_MAX_CHUNKS_HARD:
            raise ValueError(
                "CLINICAL_CHAT_RAG_MIN_CHUNKS no puede ser mayor que "
                "CLINICAL_CHAT_RAG_MAX_CHUNKS_HARD."
            )
        if self.CLINICAL_CHAT_RAG_VERIFIER_MIN_CHUNKS > self.CLINICAL_CHAT_RAG_MAX_CHUNKS_HARD:
            raise ValueError(
                "CLINICAL_CHAT_RAG_VERIFIER_MIN_CHUNKS no puede superar "
                "CLINICAL_CHAT_RAG_MAX_CHUNKS_HARD."
            )
        if self.CLINICAL_CHAT_RAG_ECORAG_MIN_CHUNKS > self.CLINICAL_CHAT_RAG_MAX_CHUNKS_HARD:
            raise ValueError(
                "CLINICAL_CHAT_RAG_ECORAG_MIN_CHUNKS no puede superar "
                "CLINICAL_CHAT_RAG_MAX_CHUNKS_HARD."
            )
        if not (0.0 <= self.CLINICAL_CHAT_RAG_MMR_LAMBDA <= 1.0):
            raise ValueError("CLINICAL_CHAT_RAG_MMR_LAMBDA debe estar entre 0 y 1.")
        if not (120 <= self.CLINICAL_CHAT_RAG_COMPRESS_MAX_CHARS <= 2000):
            raise ValueError(
                "CLINICAL_CHAT_RAG_COMPRESS_MAX_CHARS debe estar entre 120 y 2000."
            )
        if not (20 <= self.CLINICAL_CHAT_RAG_FTS_CANDIDATE_POOL <= 4000):
            raise ValueError(
                "CLINICAL_CHAT_RAG_FTS_CANDIDATE_POOL debe estar entre 20 y 4000."
            )
        if not (4 <= self.CLINICAL_CHAT_RAG_SKIP_DOMAIN_SEARCH_TOKENS_OVER <= 200):
            raise ValueError(
                "CLINICAL_CHAT_RAG_SKIP_DOMAIN_SEARCH_TOKENS_OVER debe estar entre 4 y 200."
            )
        if not (4 <= self.CLINICAL_CHAT_RAG_DETERMINISTIC_COMPLEX_MIN_TOKENS <= 200):
            raise ValueError(
                "CLINICAL_CHAT_RAG_DETERMINISTIC_COMPLEX_MIN_TOKENS debe estar entre 4 y 200."
            )
        if not (1 <= self.CLINICAL_CHAT_RAG_SIMPLE_ROUTE_MAX_CHUNKS <= 20):
            raise ValueError(
                "CLINICAL_CHAT_RAG_SIMPLE_ROUTE_MAX_CHUNKS debe estar entre 1 y 20."
            )
        if self.CLINICAL_CHAT_RAG_SIMPLE_ROUTE_MAX_CHUNKS > self.CLINICAL_CHAT_RAG_MAX_CHUNKS_HARD:
            raise ValueError(
                "CLINICAL_CHAT_RAG_SIMPLE_ROUTE_MAX_CHUNKS no puede superar "
                "CLINICAL_CHAT_RAG_MAX_CHUNKS_HARD."
            )
        if not (0 <= self.CLINICAL_CHAT_RAG_SAFE_WRAPPER_MIN_CONTEXT_RATIO <= 1):
            raise ValueError(
                "CLINICAL_CHAT_RAG_SAFE_WRAPPER_MIN_CONTEXT_RATIO debe estar entre 0 y 1."
            )
        if not (1 <= self.CLINICAL_CHAT_RAG_SPELL_MAX_EDIT_DISTANCE <= 3):
            raise ValueError(
                "CLINICAL_CHAT_RAG_SPELL_MAX_EDIT_DISTANCE debe estar entre 1 y 3."
            )
        if not (1 <= self.CLINICAL_CHAT_RAG_SPELL_TRIGGER_MAX_POSTINGS <= 50):
            raise ValueError(
                "CLINICAL_CHAT_RAG_SPELL_TRIGGER_MAX_POSTINGS debe estar entre 1 y 50."
            )
        if not (8 <= self.CLINICAL_CHAT_RAG_WILDCARD_MAX_EXPANSIONS <= 256):
            raise ValueError(
                "CLINICAL_CHAT_RAG_WILDCARD_MAX_EXPANSIONS debe estar entre 8 y 256."
            )
        if not (2 <= self.CLINICAL_CHAT_RAG_KGRAM_SIZE <= 4):
            raise ValueError("CLINICAL_CHAT_RAG_KGRAM_SIZE debe estar entre 2 y 4.")
        if not (0.05 <= self.CLINICAL_CHAT_RAG_KGRAM_JACCARD_MIN <= 0.95):
            raise ValueError(
                "CLINICAL_CHAT_RAG_KGRAM_JACCARD_MIN debe estar entre 0.05 y 0.95."
            )
        if not (8 <= self.CLINICAL_CHAT_RAG_CONTEXTUAL_SPELL_MAX_CANDIDATES <= 128):
            raise ValueError(
                "CLINICAL_CHAT_RAG_CONTEXTUAL_SPELL_MAX_CANDIDATES debe estar entre 8 y 128."
            )
        if not (1000 <= self.CLINICAL_CHAT_RAG_VOCAB_CACHE_MAX_TERMS <= 2000000):
            raise ValueError(
                "CLINICAL_CHAT_RAG_VOCAB_CACHE_MAX_TERMS debe estar entre 1000 y 2000000."
            )
        if not (30 <= self.CLINICAL_CHAT_RAG_VOCAB_CACHE_TTL_SECONDS <= 86400):
            raise ValueError(
                "CLINICAL_CHAT_RAG_VOCAB_CACHE_TTL_SECONDS debe estar entre 30 y 86400."
            )
        if not (100 <= self.CLINICAL_CHAT_RAG_POSTINGS_CACHE_MAX_ENTRIES <= 200000):
            raise ValueError(
                "CLINICAL_CHAT_RAG_POSTINGS_CACHE_MAX_ENTRIES debe estar entre 100 y 200000."
            )
        if not (30 <= self.CLINICAL_CHAT_RAG_POSTINGS_CACHE_TTL_SECONDS <= 86400):
            raise ValueError(
                "CLINICAL_CHAT_RAG_POSTINGS_CACHE_TTL_SECONDS debe estar entre 30 y 86400."
            )
        if self.CLINICAL_CHAT_RAG_POSTINGS_CACHE_ENCODING not in {"vb", "gamma"}:
            raise ValueError(
                "CLINICAL_CHAT_RAG_POSTINGS_CACHE_ENCODING debe ser 'vb' o 'gamma'."
            )
        zone_weights = [
            self.CLINICAL_CHAT_RAG_ZONE_WEIGHT_TITLE,
            self.CLINICAL_CHAT_RAG_ZONE_WEIGHT_SECTION,
            self.CLINICAL_CHAT_RAG_ZONE_WEIGHT_BODY,
            self.CLINICAL_CHAT_RAG_ZONE_WEIGHT_KEYWORDS,
            self.CLINICAL_CHAT_RAG_ZONE_WEIGHT_CUSTOM_QUESTIONS,
        ]
        if any(weight < 0 for weight in zone_weights):
            raise ValueError("Pesos de zona RAG no pueden ser negativos.")
        if sum(zone_weights) <= 0:
            raise ValueError("La suma de pesos de zona RAG debe ser mayor que 0.")
        if not (4 <= self.CLINICAL_CHAT_RAG_TFIDF_MAX_QUERY_TERMS <= 64):
            raise ValueError(
                "CLINICAL_CHAT_RAG_TFIDF_MAX_QUERY_TERMS debe estar entre 4 y 64."
            )
        if not (0 <= self.CLINICAL_CHAT_RAG_TFIDF_PIVOT_SLOPE <= 1):
            raise ValueError(
                "CLINICAL_CHAT_RAG_TFIDF_PIVOT_SLOPE debe estar entre 0 y 1."
            )
        if not (0 <= self.CLINICAL_CHAT_RAG_TFIDF_ZONE_BLEND <= 1):
            raise ValueError(
                "CLINICAL_CHAT_RAG_TFIDF_ZONE_BLEND debe estar entre 0 y 1."
            )
        if not (1.0 <= self.CLINICAL_CHAT_RAG_IDF_MIN_THRESHOLD <= 4.0):
            raise ValueError(
                "CLINICAL_CHAT_RAG_IDF_MIN_THRESHOLD debe estar entre 1.0 y 4.0."
            )
        if not (1 <= self.CLINICAL_CHAT_RAG_IDF_MIN_KEEP_TERMS <= 16):
            raise ValueError(
                "CLINICAL_CHAT_RAG_IDF_MIN_KEEP_TERMS debe estar entre 1 y 16."
            )
        if not (0 <= self.CLINICAL_CHAT_RAG_PROXIMITY_BONUS_WEIGHT <= 1):
            raise ValueError(
                "CLINICAL_CHAT_RAG_PROXIMITY_BONUS_WEIGHT debe estar entre 0 y 1."
            )
        if not (0 <= self.CLINICAL_CHAT_RAG_STATIC_QUALITY_WEIGHT <= 1):
            raise ValueError(
                "CLINICAL_CHAT_RAG_STATIC_QUALITY_WEIGHT debe estar entre 0 y 1."
            )
        if not (0 <= self.CLINICAL_CHAT_RAG_TIER1_MIN_STATIC_QUALITY <= 1):
            raise ValueError(
                "CLINICAL_CHAT_RAG_TIER1_MIN_STATIC_QUALITY debe estar entre 0 y 1."
            )
        if not self.CLINICAL_CHAT_RAG_GLOBAL_THESAURUS_PATH.strip():
            raise ValueError("CLINICAL_CHAT_RAG_GLOBAL_THESAURUS_PATH no puede estar vacio.")
        if not (30 <= self.CLINICAL_CHAT_RAG_GLOBAL_THESAURUS_TTL_SECONDS <= 86400):
            raise ValueError(
                "CLINICAL_CHAT_RAG_GLOBAL_THESAURUS_TTL_SECONDS debe estar entre 30 y 86400."
            )
        if not (
            1 <= self.CLINICAL_CHAT_RAG_GLOBAL_THESAURUS_MAX_EXPANSIONS_PER_TERM <= 32
        ):
            raise ValueError(
                "CLINICAL_CHAT_RAG_GLOBAL_THESAURUS_MAX_EXPANSIONS_PER_TERM debe estar "
                "entre 1 y 32."
            )
        if not (1 <= self.CLINICAL_CHAT_RAG_PRF_TOPK <= 12):
            raise ValueError("CLINICAL_CHAT_RAG_PRF_TOPK debe estar entre 1 y 12.")
        if not (1 <= self.CLINICAL_CHAT_RAG_PRF_MAX_TERMS <= 24):
            raise ValueError("CLINICAL_CHAT_RAG_PRF_MAX_TERMS debe estar entre 1 y 24.")
        if not (3 <= self.CLINICAL_CHAT_RAG_PRF_MIN_TERM_LEN <= 12):
            raise ValueError("CLINICAL_CHAT_RAG_PRF_MIN_TERM_LEN debe estar entre 3 y 12.")
        if not (0 <= self.CLINICAL_CHAT_RAG_PRF_ALPHA <= 2):
            raise ValueError("CLINICAL_CHAT_RAG_PRF_ALPHA debe estar entre 0 y 2.")
        if not (0 <= self.CLINICAL_CHAT_RAG_PRF_BETA <= 2):
            raise ValueError("CLINICAL_CHAT_RAG_PRF_BETA debe estar entre 0 y 2.")
        if not (0 <= self.CLINICAL_CHAT_RAG_PRF_GAMMA <= 2):
            raise ValueError("CLINICAL_CHAT_RAG_PRF_GAMMA debe estar entre 0 y 2.")
        if not (0 <= self.CLINICAL_CHAT_RAG_BM25_K1 <= 3):
            raise ValueError("CLINICAL_CHAT_RAG_BM25_K1 debe estar entre 0 y 3.")
        if not (0 <= self.CLINICAL_CHAT_RAG_BM25_B <= 1):
            raise ValueError("CLINICAL_CHAT_RAG_BM25_B debe estar entre 0 y 1.")
        if not (0 <= self.CLINICAL_CHAT_RAG_BM25_BLEND <= 1):
            raise ValueError("CLINICAL_CHAT_RAG_BM25_BLEND debe estar entre 0 y 1.")
        if not (0 <= self.CLINICAL_CHAT_RAG_BIM_BINARY_BONUS_WEIGHT <= 1):
            raise ValueError(
                "CLINICAL_CHAT_RAG_BIM_BINARY_BONUS_WEIGHT debe estar entre 0 y 1."
            )
        if self.CLINICAL_CHAT_RAG_QLM_SMOOTHING not in {"dirichlet", "jm"}:
            raise ValueError(
                "CLINICAL_CHAT_RAG_QLM_SMOOTHING debe ser 'dirichlet' o 'jm'."
            )
        if not (100 <= self.CLINICAL_CHAT_RAG_QLM_DIRICHLET_MU <= 5000):
            raise ValueError(
                "CLINICAL_CHAT_RAG_QLM_DIRICHLET_MU debe estar entre 100 y 5000."
            )
        if not (0 <= self.CLINICAL_CHAT_RAG_QLM_JM_LAMBDA <= 1):
            raise ValueError("CLINICAL_CHAT_RAG_QLM_JM_LAMBDA debe estar entre 0 y 1.")
        if not (0 <= self.CLINICAL_CHAT_RAG_QLM_BLEND <= 1):
            raise ValueError("CLINICAL_CHAT_RAG_QLM_BLEND debe estar entre 0 y 1.")
        if not (2 <= self.CLINICAL_CHAT_RAG_LSI_K <= 512):
            raise ValueError("CLINICAL_CHAT_RAG_LSI_K debe estar entre 2 y 512.")
        if not (0 <= self.CLINICAL_CHAT_RAG_LSI_BLEND <= 1):
            raise ValueError("CLINICAL_CHAT_RAG_LSI_BLEND debe estar entre 0 y 1.")
        if not (64 <= self.CLINICAL_CHAT_RAG_LSI_MAX_VOCAB_TERMS <= 4000):
            raise ValueError(
                "CLINICAL_CHAT_RAG_LSI_MAX_VOCAB_TERMS debe estar entre 64 y 4000."
            )
        if not (2 <= self.CLINICAL_CHAT_RAG_LSI_MIN_DOCS <= 200):
            raise ValueError("CLINICAL_CHAT_RAG_LSI_MIN_DOCS debe estar entre 2 y 200.")
        if not (16 <= self.CLINICAL_CHAT_RAG_SKIP_POINTERS_MIN_LIST <= 4096):
            raise ValueError(
                "CLINICAL_CHAT_RAG_SKIP_POINTERS_MIN_LIST debe estar entre 16 y 4096."
            )
        if self.CLINICAL_CHAT_RAG_RETRIEVER_BACKEND not in {
            "legacy",
            "llamaindex",
            "chroma",
            "elastic",
        }:
            raise ValueError(
                "CLINICAL_CHAT_RAG_RETRIEVER_BACKEND debe ser 'legacy', 'llamaindex', "
                "'chroma' o 'elastic'."
            )
        if not (20 <= self.CLINICAL_CHAT_RAG_LLAMAINDEX_CANDIDATE_POOL <= 1000):
            raise ValueError(
                "CLINICAL_CHAT_RAG_LLAMAINDEX_CANDIDATE_POOL debe estar entre 20 y 1000."
            )
        if not (20 <= self.CLINICAL_CHAT_RAG_CHROMA_CANDIDATE_POOL <= 2000):
            raise ValueError(
                "CLINICAL_CHAT_RAG_CHROMA_CANDIDATE_POOL debe estar entre 20 y 2000."
            )
        if not self.CLINICAL_CHAT_RAG_ELASTIC_URL.strip():
            raise ValueError("CLINICAL_CHAT_RAG_ELASTIC_URL no puede estar vacio.")
        if not self.CLINICAL_CHAT_RAG_ELASTIC_INDEX.strip():
            raise ValueError("CLINICAL_CHAT_RAG_ELASTIC_INDEX no puede estar vacio.")
        if not (1 <= self.CLINICAL_CHAT_RAG_ELASTIC_TIMEOUT_SECONDS <= 30):
            raise ValueError(
                "CLINICAL_CHAT_RAG_ELASTIC_TIMEOUT_SECONDS debe estar entre 1 y 30."
            )
        if not (20 <= self.CLINICAL_CHAT_RAG_ELASTIC_CANDIDATE_POOL <= 2000):
            raise ValueError(
                "CLINICAL_CHAT_RAG_ELASTIC_CANDIDATE_POOL debe estar entre 20 y 2000."
            )
        if not self.CLINICAL_CHAT_RAG_ELASTIC_TEXT_FIELDS.strip():
            raise ValueError("CLINICAL_CHAT_RAG_ELASTIC_TEXT_FIELDS no puede estar vacio.")
        if not self.CLINICAL_CHAT_RAG_ELASTIC_SEMANTIC_FIELD.strip():
            raise ValueError("CLINICAL_CHAT_RAG_ELASTIC_SEMANTIC_FIELD no puede estar vacio.")
        if not (0.05 <= self.CLINICAL_CHAT_UNCERTAINTY_GATE_MAX_VARIANCE <= 0.30):
            raise ValueError(
                "CLINICAL_CHAT_UNCERTAINTY_GATE_MAX_VARIANCE debe estar entre 0.05 y 0.30."
            )
        if self.CLINICAL_CHAT_RAG_VECTOR_WEIGHT < 0 or self.CLINICAL_CHAT_RAG_KEYWORD_WEIGHT < 0:
            raise ValueError("Pesos RAG no pueden ser negativos.")
        if self.CLINICAL_CHAT_RAG_VECTOR_WEIGHT + self.CLINICAL_CHAT_RAG_KEYWORD_WEIGHT <= 0:
            raise ValueError("La suma de pesos RAG debe ser mayor que 0.")
        if not self.CLINICAL_CHAT_RAG_EMBEDDING_MODEL.strip():
            raise ValueError("CLINICAL_CHAT_RAG_EMBEDDING_MODEL no puede estar vacio.")
        if not self.CLINICAL_CHAT_GUARDRAILS_CONFIG_PATH.strip():
            raise ValueError("CLINICAL_CHAT_GUARDRAILS_CONFIG_PATH no puede estar vacio.")
        if self.ENVIRONMENT != "development":
            if self.SECRET_KEY == DEFAULT_SECRET_KEY:
                raise ValueError("SECRET_KEY debe cambiarse fuera del entorno de desarrollo.")
            if len(self.SECRET_KEY) < 32:
                raise ValueError(
                    "SECRET_KEY debe tener al menos 32 caracteres fuera de desarrollo."
                )
            if "*" in self.BACKEND_CORS_ORIGINS:
                raise ValueError("BACKEND_CORS_ORIGINS no puede contener '*' fuera de desarrollo.")
        return self


settings = Settings()

