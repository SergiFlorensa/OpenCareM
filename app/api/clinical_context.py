"""
API de contexto clinico-operativo para urgencias.

Expone catalogos reutilizables por agentes, frontend y runbooks.
"""
from fastapi import APIRouter, HTTPException, status

from app.schemas.clinical_context import (
    AreaUrgenciasResponse,
    CircuitoTriageResponse,
    ContextoClinicoResumenResponse,
    EstandarOperativoResponse,
    ProcedimientoChecklistResponse,
    RolOperativoResponse,
    TriageLevelResponse,
)
from app.services.clinical_context_service import ClinicalContextService

router = APIRouter(prefix="/clinical-context", tags=["clinical-context"])


@router.get("/resumen", response_model=ContextoClinicoResumenResponse)
def get_contexto_resumen():
    """Devuelve resumen de version y cobertura del contexto cargado."""
    return ClinicalContextService.get_resumen()


@router.get("/areas", response_model=list[AreaUrgenciasResponse])
def get_areas_urgencias():
    """Lista areas operativas de urgencias con capacidad y seguridad."""
    return ClinicalContextService.list_areas()


@router.get("/circuitos", response_model=list[CircuitoTriageResponse])
def get_circuitos_triaje():
    """Lista circuitos operativos de entrada y destino recomendado."""
    return ClinicalContextService.list_circuitos()


@router.get("/roles", response_model=list[RolOperativoResponse])
def get_roles_operativos():
    """Lista roles operativos con responsabilidades y permisos sugeridos."""
    return ClinicalContextService.list_roles()


@router.get("/procedimientos", response_model=list[ProcedimientoChecklistResponse])
def get_procedimientos_checklist():
    """Lista checklists operativos convertibles en AgentSteps."""
    return ClinicalContextService.list_procedimientos()


@router.get("/procedimientos/{clave}", response_model=ProcedimientoChecklistResponse)
def get_procedimiento_checklist(clave: str):
    """Obtiene un checklist de procedimiento por clave."""
    procedure = ClinicalContextService.get_procedimiento(clave)
    if procedure is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Procedimiento no encontrado en contexto clinico.",
        )
    return procedure


@router.get("/estandares", response_model=list[EstandarOperativoResponse])
def get_estandares_operativos():
    """Lista estandares operativos para auditoria de tiempos y complejidad."""
    return ClinicalContextService.list_estandares()


@router.get("/triage-levels/manchester", response_model=list[TriageLevelResponse])
def get_triage_levels_manchester():
    """Lista los 5 niveles Manchester con color y SLA objetivo de respuesta."""
    return ClinicalContextService.list_triage_levels_manchester()
