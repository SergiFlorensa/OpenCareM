"""
Schemas de episodio de urgencias para modelar etapas del flujo operativo.
"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

EmergencyEpisodeOrigin = Literal["walk_in", "ambulance_prealert"]
EmergencyEpisodePriority = Literal["time_dependent", "non_critical"]
EmergencyEpisodeDisposition = Literal["discharge", "admission", "transfer", "ap_referral"]
EmergencyEpisodeStage = Literal[
    "admission",
    "prealert_reception",
    "nursing_triage",
    "immediate_care",
    "monitored_waiting_room",
    "medical_evaluation",
    "diagnostics_ordered",
    "treatment_observation",
    "disposition_decision",
    "discharge_report",
    "bed_request_transfer",
    "interhospital_transfer",
    "primary_care_referral",
    "episode_closed",
]


class EmergencyEpisodeCreate(BaseModel):
    """Crea episodio y fija etapa inicial segun origen."""

    care_task_id: int | None = Field(default=None, gt=0)
    origin: EmergencyEpisodeOrigin
    notes: str | None = Field(default=None, max_length=2000)


class EmergencyEpisodeTransitionRequest(BaseModel):
    """Solicita cambio de etapa con validaciones de negocio."""

    next_stage: EmergencyEpisodeStage
    priority_risk: EmergencyEpisodePriority | None = None
    disposition: EmergencyEpisodeDisposition | None = None
    notes: str | None = Field(default=None, max_length=2000)


class EmergencyEpisodeResponse(BaseModel):
    """Respuesta completa del episodio."""

    id: int
    care_task_id: int | None
    origin: EmergencyEpisodeOrigin
    current_stage: EmergencyEpisodeStage
    priority_risk: EmergencyEpisodePriority | None
    disposition: EmergencyEpisodeDisposition | None
    notes: str | None
    arrived_at: datetime
    triaged_at: datetime | None
    medical_evaluation_at: datetime | None
    diagnostics_completed_at: datetime | None
    disposition_decided_at: datetime | None
    closed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EmergencyEpisodeKpiSummaryResponse(BaseModel):
    """KPIs temporales clave del episodio de urgencias."""

    episode_id: int
    minutes_arrival_to_triage: float | None
    minutes_triage_to_medical_evaluation: float | None
    minutes_medical_evaluation_to_disposition: float | None
    minutes_total_episode: float | None
    final_stage: EmergencyEpisodeStage
    disposition: EmergencyEpisodeDisposition | None
