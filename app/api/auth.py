from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_superuser
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import (
    AdminUserResponse,
    CurrentUserResponse,
    RefreshTokenRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
)
from app.services.auth_service import AuthService
from app.services.login_throttle_service import LoginThrottleService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse, summary="Autenticar y emitir token de acceso")
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Valida credenciales y devuelve token bearer si el login es correcto."""
    client_ip = request.client.host if request.client else "unknown"
    blocked_until = LoginThrottleService.check_block_status(
        db=db,
        username=form_data.username,
        ip_address=client_ip,
    )
    if blocked_until:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos fallidos de inicio de sesion. Intentalo mas tarde.",
        )

    user = AuthService.authenticate_user(
        db=db,
        username=form_data.username,
        password=form_data.password,
    )
    if not user:
        LoginThrottleService.register_failed_attempt(
            db=db,
            username=form_data.username,
            ip_address=client_ip,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nombre de usuario o contrasena incorrectos.",
        )

    LoginThrottleService.reset_attempts(
        db=db,
        username=form_data.username,
        ip_address=client_ip,
    )
    access_token, refresh_token = AuthService.issue_token_pair(db=db, user=user)
    return TokenResponse(
        access_token=access_token, refresh_token=refresh_token, token_type="bearer"
    )


@router.get("/me", response_model=CurrentUserResponse, summary="Obtener usuario autenticado actual")
def get_me(current_user: User = Depends(get_current_user)):
    """Devuelve quien ha iniciado sesion, incluyendo si es admin."""
    if current_user.username is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="El usuario autenticado no tiene nombre de usuario.",
        )
    return CurrentUserResponse(
        username=current_user.username,
        specialty=current_user.specialty or "general",
        is_superuser=bool(current_user.is_superuser),
    )


@router.post(
    "/register",
    response_model=RegisterResponse,
    summary="Registrar una cuenta de usuario",
)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """Crea un usuario si el nombre esta libre y cumple la politica minima."""
    try:
        created_user = AuthService.register_user(
            db=db,
            username=payload.username,
            password=payload.password,
            specialty=payload.specialty,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    if created_user.id is None or created_user.username is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="La creacion de usuario devolvio datos incompletos.",
        )
    return RegisterResponse(
        id=created_user.id,
        username=created_user.username,
        specialty=created_user.specialty or "general",
    )


@router.post("/refresh", response_model=TokenResponse, summary="Rotar tokens usando refresh token")
def refresh_tokens(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Intercambia un refresh token valido por un nuevo par access+refresh."""
    try:
        access_token, refresh_token = AuthService.refresh_token_pair(
            db=db,
            refresh_token=payload.refresh_token,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
    return TokenResponse(
        access_token=access_token, refresh_token=refresh_token, token_type="bearer"
    )


@router.post("/logout", summary="Revocar sesion de refresh token")
def logout(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Revoca el refresh token para que la sesion no pueda reutilizarse."""
    try:
        AuthService.revoke_refresh_session(db=db, refresh_token=payload.refresh_token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
    return {"message": "Sesion revocada"}


@router.get(
    "/admin/users",
    response_model=list[AdminUserResponse],
    summary="Listar todos los usuarios (solo admin)",
)
def list_users_for_admin(
    _: User = Depends(require_superuser),
    db: Session = Depends(get_db),
):
    """Expone todos los usuarios solo para cuentas admin en gestion operativa."""
    users = AuthService.list_users_for_admin(db)
    return [
        AdminUserResponse(
            id=user.id,
            username=user.username,
            specialty=user.specialty or "general",
            is_active=bool(user.is_active),
            is_superuser=bool(user.is_superuser),
        )
        for user in users
        if user.id is not None and user.username is not None
    ]
