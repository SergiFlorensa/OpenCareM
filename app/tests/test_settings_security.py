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
