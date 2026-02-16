"""
Modelo de usuario para autenticacion persistente.
"""
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.sql import func

from app.core.database import Base


class User(Base):
    """Tabla de base de datos que almacena credenciales de acceso."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    specialty = Column(String(80), nullable=False, default="general", server_default="general")
    is_active = Column(Boolean, nullable=False, default=True, server_default="1")
    is_superuser = Column(Boolean, nullable=False, default=False, server_default="0")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self):
        return (
            f"User(id={self.id}, username='{self.username}', "
            f"specialty='{self.specialty}', "
            f"is_active={self.is_active}, is_superuser={self.is_superuser})"
        )
