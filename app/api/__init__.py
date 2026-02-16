"""
Rutas de API - Endpoints HTTP
"""
from app.api.agents import router as agents_router
from app.api.ai import router as ai_router
from app.api.auth import router as auth_router
from app.api.care_tasks import router as care_tasks_router
from app.api.clinical_context import router as clinical_context_router
from app.api.emergency_episodes import router as emergency_episodes_router
from app.api.knowledge_sources import router as knowledge_sources_router
from app.api.tasks import router as tasks_router

__all__ = [
    "tasks_router",
    "care_tasks_router",
    "auth_router",
    "ai_router",
    "agents_router",
    "clinical_context_router",
    "emergency_episodes_router",
    "knowledge_sources_router",
]
