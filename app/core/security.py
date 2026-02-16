"""
Utilidades de seguridad para hash de contrasenas y gestion de JWT.
"""
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

password_context = CryptContext(
    schemes=["pbkdf2_sha256", "bcrypt"],
    deprecated="auto",
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")


def get_password_hash(password: str) -> str:
    """Genera hash de una contrasena en texto plano."""
    return password_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica una contrasena en texto plano contra su hash."""
    return password_context.verify(plain_password, hashed_password)


def create_access_token(
    subject: str,
    expires_delta: timedelta | None = None,
    additional_claims: dict[str, Any] | None = None,
) -> str:
    """Crea un token de acceso JWT firmado con expiracion y sujeto."""
    now = datetime.now(timezone.utc)
    expires_at = now + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    if additional_claims:
        payload.update(additional_claims)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(subject: str, jti: str | None = None) -> tuple[str, datetime, str]:
    """Crea un refresh token firmado y devuelve token, expiracion e ID unico."""
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    refresh_jti = jti or uuid4().hex
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
        "jti": refresh_jti,
        "type": "refresh",
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token, expires_at, refresh_jti


def decode_access_token(token: str) -> dict[str, Any]:
    """Decodifica y valida un token JWT de acceso."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError as exc:
        raise ValueError("Token de acceso invalido o caducado.") from exc
    if "sub" not in payload:
        raise ValueError("El payload del token de acceso no contiene el claim 'sub'.")
    return payload


def decode_refresh_token(token: str) -> dict[str, Any]:
    """Decodifica refresh token y valida claims requeridos para rotacion."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError as exc:
        raise ValueError("Refresh token invalido o caducado.") from exc
    if payload.get("type") != "refresh":
        raise ValueError("El token proporcionado no es de tipo refresh.")
    if "sub" not in payload or "jti" not in payload:
        raise ValueError("El payload del refresh token no contiene claims requeridos.")
    return payload


def get_current_subject(token: str = Depends(oauth2_scheme)) -> str:
    """Extrae el sujeto autenticado desde el bearer token."""
    try:
        payload = decode_access_token(token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se pudieron validar las credenciales.",
        ) from exc
    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se pudieron validar las credenciales.",
        )
    return subject


def validate_password_policy(password: str) -> tuple[bool, str | None]:
    """Explica de forma simple si una contrasena cumple la politica minima."""
    if len(password) < 8:
        return False, "La contrasena debe tener al menos 8 caracteres."
    if password.lower() == password or password.upper() == password:
        return False, "La contrasena debe mezclar mayusculas y minusculas."
    if not any(character.isdigit() for character in password):
        return False, "La contrasena debe incluir al menos un numero."
    return True, None
