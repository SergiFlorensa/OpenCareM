"""
Schemas para soporte operativo diferencial de acne y rosacea.

No sustituye diagnostico dermatologico definitivo ni valoracion presencial.
"""
from typing import Literal

from pydantic import BaseModel, Field


class AcneRosaceaDifferentialRequest(BaseModel):
    """Entrada estructurada para clasificar acne vs rosacea y orientar manejo inicial."""

    age_years: int = Field(ge=0, le=120)
    sex: Literal["femenino", "masculino", "otro"] = "otro"
    lesion_distribution: list[
        Literal[
            "mejillas",
            "nariz",
            "frente",
            "menton",
            "torax",
            "espalda",
            "cuello",
            "generalizada",
        ]
    ] = Field(default_factory=list)
    comedones_present: bool = False
    lesion_pattern: Literal[
        "polimorfo",
        "monomorfo",
        "papulo_pustuloso",
        "nodulo_quistico",
    ] = "papulo_pustuloso"
    flushing_present: bool = False
    telangiectasias_present: bool = False
    ocular_symptoms_present: bool = False
    phymatous_changes_present: bool = False
    photosensitivity_triggered: bool = False
    vasodilatory_triggers_present: bool = False
    severe_nodules_abscesses_present: bool = False
    systemic_symptoms_present: bool = False
    elevated_vsg_or_leukocytosis: bool = False
    suspected_hyperandrogenism: bool = False
    pediatric_patient: bool = False
    pregnant_or_pregnancy_possible: bool = False
    isotretinoin_candidate: bool = False
    current_systemic_tetracycline: bool = False
    current_retinoid_oral: bool = False
    clinical_context: str | None = Field(default=None, max_length=2000)


class AcneRosaceaDifferentialRecommendation(BaseModel):
    """Salida operativa interpretable para acne/rosacea con seguridad farmacologica."""

    most_likely_condition: Literal[
        "acne",
        "rosacea",
        "indeterminado",
    ]
    suspected_subtype: str
    severity_level: Literal["low", "medium", "high"]
    differential_diagnoses: list[str]
    supporting_findings: list[str]
    initial_management: list[str]
    pharmacologic_considerations: list[str]
    isotretinoin_monitoring_checklist: list[str]
    urgent_red_flags: list[str]
    follow_up_recommendations: list[str]
    human_validation_required: bool
    non_diagnostic_warning: str


class CareTaskAcneRosaceaDifferentialResponse(BaseModel):
    """Respuesta trazable del endpoint diferencial acne/rosacea."""

    care_task_id: int
    agent_run_id: int
    workflow_name: str
    recommendation: AcneRosaceaDifferentialRecommendation
