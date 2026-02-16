from datetime import timedelta

import pytest
from jose import jwt

from app.core.config import settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)


def test_password_hash_and_verify():
    password = "my-strong-password"
    hashed = get_password_hash(password)

    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong-password", hashed) is False


def test_create_and_decode_access_token():
    token = create_access_token(
        subject="user-123",
        expires_delta=timedelta(minutes=5),
        additional_claims={"role": "admin"},
    )
    payload = decode_access_token(token)

    assert payload["sub"] == "user-123"
    assert payload["role"] == "admin"
    assert "exp" in payload
    assert "iat" in payload


def test_decode_access_token_rejects_invalid_token():
    with pytest.raises(ValueError, match="Token de acceso invalido o caducado"):
        decode_access_token("invalid.token.value")


def test_decode_access_token_rejects_missing_subject_claim():
    token = jwt.encode(
        {"iat": 123, "exp": 9999999999},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    with pytest.raises(ValueError, match="no contiene el claim 'sub'"):
        decode_access_token(token)
