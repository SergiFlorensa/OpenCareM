"""
Database model that stores refresh token sessions.
"""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.core.database import Base


class AuthSession(Base):
    """Represents one refresh-token lifecycle for one user login session."""

    __tablename__ = "auth_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    jti = Column(String(64), nullable=False, unique=True, index=True)
    is_revoked = Column(Boolean, nullable=False, default=False, server_default="0")
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    def __repr__(self):
        return (
            f"AuthSession(id={self.id}, user_id={self.user_id}, "
            f"is_revoked={self.is_revoked}, jti='{self.jti}')"
        )
