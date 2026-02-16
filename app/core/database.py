"""
Configuracion de conexion y sesion de base de datos.
"""
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

engine_options: dict[str, Any] = {
    "echo": settings.DATABASE_ECHO,
}
if settings.DATABASE_URL.startswith("sqlite"):
    engine_options["connect_args"] = {"check_same_thread": False}


engine = create_engine(settings.DATABASE_URL, **engine_options)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    """Entrega una sesion de base de datos por cada peticion."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Crea todas las tablas conocidas (utilidad de desarrollo)."""
    from app.models.agent_run import AgentRun, AgentStep  # noqa: F401
    from app.models.auth_session import AuthSession  # noqa: F401
    from app.models.care_task_chat_message import CareTaskChatMessage  # noqa: F401
    from app.models.clinical_knowledge_source import ClinicalKnowledgeSource  # noqa: F401
    from app.models.clinical_knowledge_source_validation import (  # noqa: F401
        ClinicalKnowledgeSourceValidation,
    )
    from app.models.emergency_episode import EmergencyEpisode  # noqa: F401
    from app.models.login_attempt import LoginAttempt  # noqa: F401
    from app.models.task import Task  # noqa: F401
    from app.models.user import User  # noqa: F401

    Base.metadata.create_all(bind=engine)
    print("Base de datos inicializada")


def drop_db():
    """Elimina todas las tablas (utilidad de desarrollo/pruebas)."""
    Base.metadata.drop_all(bind=engine)
    print("Todas las tablas han sido eliminadas")
