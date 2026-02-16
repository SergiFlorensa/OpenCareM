"""
API Gestor de Tareas - Punto de entrada principal.
"""
import sys
import time
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from prometheus_fastapi_instrumentator import Instrumentator

from app.api import (
    agents_router,
    ai_router,
    auth_router,
    care_tasks_router,
    clinical_context_router,
    emergency_episodes_router,
    knowledge_sources_router,
    tasks_router,
)
from app.core.config import settings
from app.metrics.agent_metrics import register_agent_metrics

logger.remove()
logger_format = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan> - "
    "<level>{message}</level>"
)
logger.add(sys.stdout, colorize=True, format=logger_format, level="INFO")


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Hooks de ciclo de vida de la aplicacion."""
    logger.info(f"Iniciando {settings.APP_NAME}...")
    logger.info("Documentacion disponible en /docs")
    yield
    logger.info(f"Cerrando {settings.APP_NAME}...")


app = FastAPI(
    title=settings.APP_NAME,
    description="API REST profesional para gestion de tareas",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Registra una linea estructurada por peticion y expone request id en cabeceras."""
    request_id = request.headers.get("X-Request-ID", uuid4().hex)
    started_at = time.perf_counter()
    response: Response | None = None
    status_code = 500
    try:
        response = await call_next(request)
        if response is not None:
            status_code = response.status_code
        return response
    finally:
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        logger.bind(
            event="http_request",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=status_code,
            duration_ms=duration_ms,
        ).info("Peticion HTTP procesada")
        if response is not None:
            response.headers["X-Request-ID"] = request_id


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_agent_metrics()
instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
)
instrumentator.instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

app.include_router(tasks_router, prefix=settings.API_V1_PREFIX)
app.include_router(care_tasks_router, prefix=settings.API_V1_PREFIX)
app.include_router(clinical_context_router, prefix=settings.API_V1_PREFIX)
app.include_router(emergency_episodes_router, prefix=settings.API_V1_PREFIX)
app.include_router(knowledge_sources_router, prefix=settings.API_V1_PREFIX)
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(ai_router, prefix=settings.API_V1_PREFIX)
app.include_router(agents_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    """Endpoint raiz para comprobacion de salud basica."""
    return {
        "message": f"{settings.APP_NAME} esta funcionando.",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "api_prefix": settings.API_V1_PREFIX,
    }


@app.get("/health")
async def health_check():
    """Endpoint de comprobacion de salud para monitorizacion."""
    return {"status": "healthy", "service": "api-gestor-tareas"}


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Evita error 404 del favicon."""
    return {"message": "No favicon"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
