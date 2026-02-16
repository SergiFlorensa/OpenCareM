"""
Schemas para exponer contexto clinico-operativo de urgencias.

Estos contratos no dan diagnostico medico: solo describen recursos,
roles y circuitos de operacion para que agentes y humanos trabajen
con un mismo lenguaje.
"""
from typing import Literal

from pydantic import BaseModel, Field


class AreaUrgenciasResponse(BaseModel):
    """Recurso fisico/operativo disponible en urgencias."""

    codigo: str
    nombre: str
    tipo: Literal["consultas", "camas", "observacion", "sillones", "seguridad"]
    capacidad_total: int = Field(..., ge=0)
    capacidad_aislamiento: int = Field(default=0, ge=0)
    monitorizada: bool = False
    estancia_objetivo_horas_max: int | None = Field(default=None, gt=0)
    zona_seguridad: Literal["roja", "verde", "mixta"]
    descripcion: str


class CircuitoTriageResponse(BaseModel):
    """Regla operativa de circuito de entrada en urgencias."""

    codigo: str
    nombre: str
    criterio_entrada: str
    acciones_tempranas: list[str]
    destino_recomendado: str


class RolOperativoResponse(BaseModel):
    """Perfil operativo con responsabilidades diferenciadas."""

    nombre: str
    descripcion: str
    responsabilidades: list[str]
    permisos_aplicacion: list[str]


class ProcedimientoChecklistResponse(BaseModel):
    """Checklist operativo de procedimiento para AgentSteps guiados."""

    clave: str
    nombre: str
    pasos: list[str]
    objetivo_operativo: str
    advertencia_seguridad: str


class EstandarOperativoResponse(BaseModel):
    """Metrica o estandar usado para seguimiento operacional."""

    codigo: str
    nombre: str
    descripcion: str
    valor_objetivo: str
    unidad: str


class ContextoClinicoResumenResponse(BaseModel):
    """Resumen agregado del contexto cargado en el sistema."""

    version_contexto: str
    total_areas: int
    total_circuitos: int
    total_roles: int
    total_procedimientos: int
    total_estandares: int
    advertencia_uso: str


class TriageLevelResponse(BaseModel):
    """
    Nivel de triaje basado en el estandar Manchester.

    Incluye prioridad operacional y tiempo objetivo maximo de atencion.
    """

    sistema: Literal["manchester"]
    nivel: int = Field(..., ge=1, le=5)
    color: Literal["rojo", "naranja", "amarillo", "verde", "azul"]
    etiqueta: str
    descripcion: str
    sla_objetivo_minutos: int = Field(..., ge=0)
