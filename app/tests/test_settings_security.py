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
