"""
Schemas para soporte operativo de diagnostico diferencial en pitiriasis.

No sustituye diagnostico dermatologico definitivo ni biopsia cuando
esta indicada por evolucion atipica.
"""
from typing import Literal

from pydantic import BaseModel, Field


class PityriasisDifferentialRequest(BaseModel):
    """Entrada estructurada para diferenciar pitiriasis frecuentes en urgencias/consulta."""

    age_years: int = Field(ge=0, le=120)
    lesion_distribution: list[
        Literal[
            "tronco",
            "torax",
            "espalda",
            "cara",
            "cuello",
            "extremidades_superiores",
            "generalizada",
            "areas_seborreicas",
        ]
    ] = Field(default_factory=list)
    lesion_pigmentation: Literal[
        "hipocromica", "hipercromica", "eritematosa", "mixta"
    ] = "hipocromica"
    fine_scaling_present: bool = False
    signo_unyada_positive: bool = False
    herald_patch_present: bool = False
    christmas_tree_pattern_present: bool = False
    pruritus_intensity: int = Field(default=0, ge=0, le=10)
    viral_prodrome_present: bool = False
    wood_lamp_result: Literal[
        "amarillo_naranja", "sin_fluorescencia", "no_realizada"
    ] = "no_realizada"
    koh_result: Literal[
        "positivo_spaghetti_albondigas", "negativo", "no_realizado"
    ] = "no_realizado"
    recurrent_course: bool = False
    atopic_background: bool = False
    sensory_loss_in_lesion: bool = False
    deep_erythema_warmth_pain: bool = False
    systemic_signs: bool = False
    immunosuppressed: bool = False
    clinical_context: str | None = Field(default=None, max_length=2000)


class PityriasisDifferentialRecommendation(BaseModel):
    """Salida operativa interpretable para validacion dermatologica humana."""

    most_likely_condition: Literal[
        "pitiriasis_versicolor",
        "pitiriasis_rosada",
        "pitiriasis_alba",
        "indeterminado",
    ]
    differential_diagnoses: list[str]
    supporting_findings: list[str]
    recommended_tests: list[str]
    initial_management: list[str]
    urgent_red_flags: list[str]
    follow_up_recommendations: list[str]
    human_validation_required: bool
    non_diagnostic_warning: str


class CareTaskPityriasisDifferentialResponse(BaseModel):
    """Respuesta trazable del endpoint de diagnostico diferencial de pitiriasis."""

    care_task_id: int
    agent_run_id: int
    workflow_name: str
    recommendation: PityriasisDifferentialRecommendation
