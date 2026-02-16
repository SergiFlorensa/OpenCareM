"""
Schemas para soporte operativo de riesgo cardiovascular en urgencias.

No sustituye diagnostico ni decision terapeutica final.
"""
from pydantic import BaseModel, Field


class CardioRiskProtocolRequest(BaseModel):
    """Entrada clinico-operativa para estratificacion inicial de riesgo cardiovascular."""

    age_years: int = Field(..., ge=18, le=120)
    sex: str = Field(..., pattern="^(male|female)$")
    smoker: bool = False
    systolic_bp: int = Field(..., ge=70, le=260)
    non_hdl_mg_dl: float = Field(..., ge=30, le=500)
    apob_mg_dl: float | None = Field(default=None, ge=20, le=300)
    hdl_mg_dl: float | None = Field(default=None, ge=10, le=120)
    triglycerides_mg_dl: float | None = Field(default=None, ge=20, le=2000)
    diabetes: bool = False
    chronic_kidney_disease: bool = False
    established_atherosclerotic_cvd: bool = False
    family_history_premature_cvd: bool = False
    chronic_inflammatory_state: bool = False
    on_lipid_lowering_therapy: bool = False
    statin_intolerance: bool = False
    notes: str | None = Field(default=None, max_length=2000)


class CardioRiskProtocolRecommendation(BaseModel):
    """Salida estructurada de soporte operativo cardiovascular."""

    risk_level: str
    estimated_10y_risk_percent: float
    ldl_target_mg_dl: int
    non_hdl_target_mg_dl: int
    non_hdl_target_required: bool
    intensive_lifestyle_required: bool
    pharmacologic_strategy_suggested: bool
    priority_actions: list[str]
    additional_markers_recommended: list[str]
    alerts: list[str]
    human_validation_required: bool
    non_diagnostic_warning: str


class CareTaskCardioRiskProtocolResponse(BaseModel):
    """Respuesta final del endpoint vinculada a run trazable."""

    care_task_id: int
    agent_run_id: int
    workflow_name: str
    recommendation: CardioRiskProtocolRecommendation
