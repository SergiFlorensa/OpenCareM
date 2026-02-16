"""
Dependencias reutilizables de API para autenticacion y autorizacion.
"""
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_subject
from app.models.user import User


def get_current_user(
    db: Session = Depends(get_db),
    current_username: str = Depends(get_current_subject),
) -> User:
    """Carga el usuario autenticado desde BD para usar sus datos completos."""
    user = db.query(User).filter(User.username == current_username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El usuario autenticado ya no existe.",
        )
    return user


def require_superuser(current_user: User = Depends(get_current_user)) -> User:
    """Permite solo usuarios admin en endpoints protegidos de administracion."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de administrador.",
        )
    return current_user
