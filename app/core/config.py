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
    CLINICAL_CHAT_REQUIRE_VALIDATED_INTERNAL_SOURCES: bool = True
    CLINICAL_CHAT_LLM_ENABLED: bool = False
    CLINICAL_CHAT_LLM_PROVIDER: str = "ollama"
    CLINICAL_CHAT_LLM_BASE_URL: str = "http://127.0.0.1:11434"
    CLINICAL_CHAT_LLM_MODEL: str = "llama3.1:8b"
    CLINICAL_CHAT_LLM_TIMEOUT_SECONDS: int = 15
    CLINICAL_CHAT_LLM_MAX_OUTPUT_TOKENS: int = 700
    CLINICAL_CHAT_LLM_MAX_INPUT_TOKENS: int = 3200
    CLINICAL_CHAT_LLM_PROMPT_MARGIN_TOKENS: int = 256
    CLINICAL_CHAT_LLM_TEMPERATURE: float = 0.2
    CLINICAL_CHAT_LLM_NUM_CTX: int = 4096
    CLINICAL_CHAT_LLM_TOP_P: float = 0.9
    CLINICAL_CHAT_RAG_ENABLED: bool = False
    CLINICAL_CHAT_RAG_MAX_CHUNKS: int = 5
    CLINICAL_CHAT_RAG_VECTOR_WEIGHT: float = 0.5
    CLINICAL_CHAT_RAG_KEYWORD_WEIGHT: float = 0.5
    CLINICAL_CHAT_RAG_EMBEDDING_MODEL: str = "nomic-embed-text"
    CLINICAL_CHAT_RAG_ENABLE_GATEKEEPER: bool = True

    DATABASE_URL: str = "sqlite:///./task_manager.db"
    DATABASE_ECHO: bool = True

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
        if self.CLINICAL_CHAT_LLM_PROVIDER not in {"ollama"}:
            raise ValueError("CLINICAL_CHAT_LLM_PROVIDER debe ser 'ollama'.")
        if self.CLINICAL_CHAT_LLM_TIMEOUT_SECONDS < 2:
            raise ValueError("CLINICAL_CHAT_LLM_TIMEOUT_SECONDS debe ser >= 2.")
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
        if not (1 <= self.CLINICAL_CHAT_RAG_MAX_CHUNKS <= 20):
            raise ValueError("CLINICAL_CHAT_RAG_MAX_CHUNKS debe estar entre 1 y 20.")
        if self.CLINICAL_CHAT_RAG_VECTOR_WEIGHT < 0 or self.CLINICAL_CHAT_RAG_KEYWORD_WEIGHT < 0:
            raise ValueError("Pesos RAG no pueden ser negativos.")
        if self.CLINICAL_CHAT_RAG_VECTOR_WEIGHT + self.CLINICAL_CHAT_RAG_KEYWORD_WEIGHT <= 0:
            raise ValueError("La suma de pesos RAG debe ser mayor que 0.")
        if not self.CLINICAL_CHAT_RAG_EMBEDDING_MODEL.strip():
            raise ValueError("CLINICAL_CHAT_RAG_EMBEDDING_MODEL no puede estar vacio.")
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
