from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    get_password_hash,
    validate_password_policy,
    verify_password,
)
from app.models.auth_session import AuthSession
from app.models.user import User


class AuthService:
    @staticmethod
    def _normalize_specialty(value: str | None) -> str:
        """Normaliza especialidad para uso consistente en ruteo operativo."""
        normalized = (value or "general").strip().lower()
        return normalized or "general"

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        """Normaliza fechas de BD para evitar fallos de comparacion por zona horaria."""
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> User | None:
        """Valida credenciales contra usuarios almacenados en base de datos."""
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return None
        if not user.hashed_password:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        return user

    @staticmethod
    def issue_access_token(user: User) -> str:
        """Crea un token JWT usando el nombre de usuario como sujeto."""
        if not user.username:
            raise ValueError("Se requiere el nombre de usuario para emitir el token.")
        return create_access_token(subject=user.username)

    @staticmethod
    def issue_token_pair(db: Session, user: User) -> tuple[str, str]:
        """Crea access+refresh tokens y persiste la sesion para futura revocacion."""
        if not user.username:
            raise ValueError("Se requiere el nombre de usuario para emitir tokens.")
        if user.id is None:
            raise ValueError("Se requiere el ID de usuario para emitir tokens.")
        access_token = create_access_token(subject=user.username)
        refresh_token, refresh_expires_at, refresh_jti = create_refresh_token(subject=user.username)
        auth_session = AuthSession(
            user_id=user.id,
            jti=refresh_jti,
            expires_at=refresh_expires_at,
            is_revoked=False,
        )
        db.add(auth_session)
        db.commit()
        return access_token, refresh_token

    @staticmethod
    def list_users_for_admin(db: Session) -> list[User]:
        """Devuelve todos los usuarios para gestion operativa de administracion."""
        return db.query(User).order_by(User.id.asc()).all()

    @staticmethod
    def refresh_token_pair(db: Session, refresh_token: str) -> tuple[str, str]:
        """Rota la sesion refresh: revoca la anterior y devuelve un nuevo par."""
        payload = decode_refresh_token(refresh_token)
        username = payload.get("sub")
        refresh_jti = payload.get("jti")
        if not isinstance(username, str) or not isinstance(refresh_jti, str):
            raise ValueError("El payload del refresh token es invalido.")

        session = db.query(AuthSession).filter(AuthSession.jti == refresh_jti).first()
        if not session:
            raise ValueError("Sesion refresh no encontrada.")
        if session.is_revoked:
            raise ValueError("La sesion refresh ya esta revocada.")
        if session.expires_at is None:
            raise ValueError("La sesion refresh no tiene expiracion.")
        session_expires_at = AuthService._as_utc(session.expires_at)
        if session_expires_at <= datetime.now(timezone.utc):
            raise ValueError("La sesion refresh ha caducado.")

        user = db.query(User).filter(User.username == username).first()
        if not user or not user.is_active:
            raise ValueError("El usuario no esta activo.")
        if user.id is None:
            raise ValueError("Se requiere el ID de usuario para refrescar tokens.")

        session.is_revoked = True
        session.revoked_at = datetime.now(timezone.utc)
        db.add(session)

        access_token = create_access_token(subject=username)
        new_refresh_token, new_refresh_expires_at, new_refresh_jti = create_refresh_token(
            subject=username
        )
        new_session = AuthSession(
            user_id=user.id,
            jti=new_refresh_jti,
            expires_at=new_refresh_expires_at,
            is_revoked=False,
        )
        db.add(new_session)
        db.commit()
        return access_token, new_refresh_token

    @staticmethod
    def revoke_refresh_session(db: Session, refresh_token: str) -> None:
        """Revoca una sesion refresh para bloquear reutilizacion tras logout."""
        payload = decode_refresh_token(refresh_token)
        refresh_jti = payload.get("jti")
        if not isinstance(refresh_jti, str):
            raise ValueError("El payload del refresh token es invalido.")
        session = db.query(AuthSession).filter(AuthSession.jti == refresh_jti).first()
        if not session:
            raise ValueError("Sesion refresh no encontrada.")
        if session.is_revoked:
            return
        session.is_revoked = True
        session.revoked_at = datetime.now(timezone.utc)
        db.add(session)
        db.commit()

    @staticmethod
    def register_user(
        db: Session,
        username: str,
        password: str,
        specialty: str | None = None,
    ) -> User:
        """Crea un usuario nuevo tras validar reglas de nombre y contrasena."""
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            raise ValueError("El nombre de usuario ya existe.")

        is_valid_password, password_error = validate_password_policy(password)
        if not is_valid_password and password_error:
            raise ValueError(password_error)

        new_user = User(
            username=username,
            hashed_password=get_password_hash(password),
            specialty=AuthService._normalize_specialty(specialty),
            is_active=True,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    @staticmethod
    def bootstrap_first_admin(db: Session, username: str, password: str) -> User:
        """
        Crea el primer usuario admin solo cuando la tabla de usuarios esta vacia.

        Esta funcion sirve para el arranque inicial sin exponer endpoints publicos
        de creacion de administradores.
        """
        existing_users_count = db.query(User).count()
        if existing_users_count > 0:
            raise ValueError("Bootstrap bloqueado: ya existen usuarios en la base de datos.")

        is_valid_password, password_error = validate_password_policy(password)
        if not is_valid_password and password_error:
            raise ValueError(password_error)

        admin_user = User(
            username=username,
            hashed_password=get_password_hash(password),
            specialty="general",
            is_active=True,
            is_superuser=True,
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        return admin_user
