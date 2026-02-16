"""
Modelo de base de datos para registrar fallos de login y bloqueos temporales.
"""
from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func

from app.core.database import Base


class LoginAttempt(Base):
    """Guarda intentos fallidos agrupados por usuario y IP cliente."""

    __tablename__ = "login_attempts"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), nullable=False, index=True)
    ip_address = Column(String(64), nullable=False, index=True)
    failed_count = Column(Integer, nullable=False, default=0, server_default="0")
    first_failed_at = Column(DateTime(timezone=True), nullable=True)
    blocked_until = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self):
        return (
            f"LoginAttempt(username='{self.username}', ip_address='{self.ip_address}', "
            f"failed_count={self.failed_count})"
        )
