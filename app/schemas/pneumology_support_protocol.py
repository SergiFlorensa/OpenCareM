"""
Schemas para soporte operativo de neumologia en urgencias.

No sustituye protocolos institucionales ni criterio clinico especializado.
"""
from pydantic import BaseModel, Field


class PneumologySupportProtocolRequest(BaseModel):
    """Entrada clinico-operativa para priorizacion neumologica en urgencias."""

    ct_peripheral_subpleural_consolidation: bool = False
    air_bronchogram_present: bool = False
    centrilobular_upper_lobe_nodules: bool = False
    interstitial_pattern_predominant: bool = False
    smoker_active_or_history: bool = False
    obstructive_lesion_signs: bool = False
    significant_volume_loss_signs: bool = False

    po2_low_detected: bool = False
    pco2_high_detected: bool = False
    respiratory_acidosis_present: bool = False
    chronic_hypercapnia_days: int | None = Field(default=None, ge=0, le=60)
    renal_compensation_evidence: bool = False

    hemoptysis_present: bool = False
    known_bronchiectasis: bool = False
    bibasal_velcro_crackles_present: bool = False
    digital_clubbing_present: bool = False
    reduced_breath_sounds_present: bool = False
    wheeze_present: bool = False

    copd_diagnosed: bool = False
    persistent_frequent_exacerbator: bool = False
    frequent_hospitalizations: bool = False
    on_laba_lama: bool = False
    on_laba_ics_without_lama: bool = False
    eosinophils_per_ul: int | None = Field(default=None, ge=0, le=5000)

    severe_asthma: bool = False
    eosinophilic_phenotype: bool = False
    chronic_rhinosinusitis_with_polyposis: bool = False
    allergic_asthma_phenotype: bool = False
    biologic_planned: str | None = Field(default=None, max_length=60)

    bal_performed: bool = False
    bal_pas_positive_lipoproteins: bool = False
    bal_clears_with_serial_lavage: bool = False
    sarcoidosis_suspected: bool = False
    bal_cd4_cd8_high: bool = False
    hypersensitivity_pneumonitis_suspected: bool = False
    bal_lymphocytosis_present: bool = False

    solitary_nodule_malignancy_suspected: bool = False
    pet_positive: bool = False
    vo2max_ml_kg_min: float | None = Field(default=None, ge=0, le=80)
    surgery_planned: bool = False
    biopsy_high_risk: bool = False

    notes: str | None = Field(default=None, max_length=2000)


class PneumologySupportProtocolRecommendation(BaseModel):
    """Salida estructurada del soporte operativo de neumologia."""

    severity_level: str
    critical_alerts: list[str]
    imaging_assessment: list[str]
    ventilatory_control_assessment: list[str]
    diagnostic_actions: list[str]
    therapeutic_actions: list[str]
    biologic_strategy: list[str]
    procedural_safety_alerts: list[str]
    interpretability_trace: list[str]
    human_validation_required: bool
    non_diagnostic_warning: str


class CareTaskPneumologySupportResponse(BaseModel):
    """Respuesta final del endpoint vinculada a run trazable."""

    care_task_id: int
    agent_run_id: int
    workflow_name: str
    recommendation: PneumologySupportProtocolRecommendation
