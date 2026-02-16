"""
Schemas para soporte operativo de interpretacion radiografica de torax.

No realiza diagnostico definitivo; organiza hallazgos y alertas para
validacion clinica humana.
"""
from typing import Literal

from pydantic import BaseModel, Field


class ChestXRaySupportRequest(BaseModel):
    """Entrada estructurada de hallazgos radiograficos observados."""

    projection: Literal["pa", "ap", "lateral"] = "pa"
    inspiratory_quality: Literal["adecuada", "suboptima"] = "adecuada"
    pattern: Literal[
        "ninguno",
        "alveolar",
        "intersticial",
        "atelectasia",
        "neumotorax",
        "derrame_pleural",
        "mixto",
    ] = "ninguno"
    signs: list[
        Literal[
            "broncograma_aereo",
            "lineas_kerley_b",
            "desplazamiento_cisuras",
            "linea_pleural_visceral",
            "ausencia_trama_periferica",
            "signo_menisco",
            "desplazamiento_mediastinico",
            "cardiomegalia_aparente_ap",
            "neumoperitoneo_subdiafragmatico",
        ]
    ] = Field(default_factory=list)
    lesion_size_cm: float | None = Field(default=None, ge=0)
    clinical_context: str | None = Field(default=None, max_length=2000)


class ChestXRaySupportRecommendation(BaseModel):
    """Salida operativa de interpretacion orientativa."""

    suspected_patterns: list[str]
    urgent_red_flags: list[str]
    suggested_actions: list[str]
    projection_caveats: list[str]
    human_validation_required: bool
    non_diagnostic_warning: str


class CareTaskChestXRaySupportResponse(BaseModel):
    """Respuesta trazable del endpoint de soporte radiografico."""

    care_task_id: int
    agent_run_id: int
    workflow_name: str
    recommendation: ChestXRaySupportRecommendation
