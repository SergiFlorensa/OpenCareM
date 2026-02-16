from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.login_attempt import LoginAttempt


class LoginThrottleService:
    @staticmethod
    def _as_utc(value: datetime | None) -> datetime | None:
        """Normaliza fechas guardadas para comparaciones seguras en zona horaria."""
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    @staticmethod
    def _get_or_create_attempt(db: Session, username: str, ip_address: str) -> LoginAttempt:
        """Carga el registro de intentos para usuario+IP o lo crea si no existe."""
        attempt = (
            db.query(LoginAttempt)
            .filter(LoginAttempt.username == username, LoginAttempt.ip_address == ip_address)
            .first()
        )
        if attempt:
            return attempt
        attempt = LoginAttempt(
            username=username,
            ip_address=ip_address,
            failed_count=0,
        )
        db.add(attempt)
        db.commit()
        db.refresh(attempt)
        return attempt

    @staticmethod
    def check_block_status(db: Session, username: str, ip_address: str) -> datetime | None:
        """Devuelve fecha de desbloqueo si hay bloqueo temporal; si no, `None`."""
        attempt = (
            db.query(LoginAttempt)
            .filter(LoginAttempt.username == username, LoginAttempt.ip_address == ip_address)
            .first()
        )
        if not attempt:
            return None
        blocked_until = LoginThrottleService._as_utc(attempt.blocked_until)
        now = datetime.now(timezone.utc)
        if blocked_until and blocked_until > now:
            return blocked_until
        if blocked_until and blocked_until <= now:
            attempt.blocked_until = None
            attempt.failed_count = 0
            attempt.first_failed_at = None
            db.add(attempt)
            db.commit()
        return None

    @staticmethod
    def register_failed_attempt(db: Session, username: str, ip_address: str) -> None:
        """Incrementa fallos y aplica bloqueo temporal al alcanzar el limite."""
        attempt = LoginThrottleService._get_or_create_attempt(db, username, ip_address)
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(minutes=settings.LOGIN_WINDOW_MINUTES)
        first_failed_at = LoginThrottleService._as_utc(attempt.first_failed_at)

        if first_failed_at is None or first_failed_at < window_start:
            attempt.failed_count = 1
            attempt.first_failed_at = now
            attempt.blocked_until = None
        else:
            attempt.failed_count = (attempt.failed_count or 0) + 1

        if attempt.failed_count >= settings.LOGIN_MAX_ATTEMPTS:
            attempt.blocked_until = now + timedelta(minutes=settings.LOGIN_BLOCK_MINUTES)

        db.add(attempt)
        db.commit()

    @staticmethod
    def reset_attempts(db: Session, username: str, ip_address: str) -> None:
        """Limpia el estado de throttling tras un login correcto."""
        attempt = (
            db.query(LoginAttempt)
            .filter(LoginAttempt.username == username, LoginAttempt.ip_address == ip_address)
            .first()
        )
        if not attempt:
            return
        attempt.failed_count = 0
        attempt.first_failed_at = None
        attempt.blocked_until = None
        db.add(attempt)
        db.commit()
