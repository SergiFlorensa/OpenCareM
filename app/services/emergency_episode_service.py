"""
Servicio para gestionar etapas y transiciones de episodios de urgencias.
"""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.emergency_episode import EmergencyEpisode
from app.schemas.emergency_episode import (
    EmergencyEpisodeCreate,
    EmergencyEpisodeKpiSummaryResponse,
    EmergencyEpisodeTransitionRequest,
)

INITIAL_STAGE_BY_ORIGIN = {
    "walk_in": "admission",
    "ambulance_prealert": "prealert_reception",
}

ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "admission": {"nursing_triage"},
    "prealert_reception": {"nursing_triage"},
    "nursing_triage": {"immediate_care", "monitored_waiting_room"},
    "immediate_care": {"medical_evaluation"},
    "monitored_waiting_room": {"medical_evaluation"},
    "medical_evaluation": {"diagnostics_ordered", "treatment_observation"},
    "diagnostics_ordered": {"treatment_observation"},
    "treatment_observation": {"disposition_decision"},
    "disposition_decision": {
        "discharge_report",
        "bed_request_transfer",
        "interhospital_transfer",
        "primary_care_referral",
    },
    "discharge_report": {"episode_closed"},
    "bed_request_transfer": {"episode_closed"},
    "interhospital_transfer": {"episode_closed"},
    "primary_care_referral": {"episode_closed"},
    "episode_closed": set(),
}

DISPOSITION_BY_STAGE = {
    "discharge_report": "discharge",
    "bed_request_transfer": "admission",
    "interhospital_transfer": "transfer",
    "primary_care_referral": "ap_referral",
}


class EmergencyEpisodeService:
    """Orquesta el flujo extremo-a-extremo de un episodio de urgencias."""

    @staticmethod
    def create_episode(db: Session, payload: EmergencyEpisodeCreate) -> EmergencyEpisode:
        """Crea episodio con etapa inicial coherente al origen de llegada."""
        episode = EmergencyEpisode(
            care_task_id=payload.care_task_id,
            origin=payload.origin,
            current_stage=INITIAL_STAGE_BY_ORIGIN[payload.origin],
            notes=payload.notes,
        )
        db.add(episode)
        db.commit()
        db.refresh(episode)
        return episode

    @staticmethod
    def get_episode_by_id(db: Session, episode_id: int) -> EmergencyEpisode | None:
        """Obtiene un episodio por id."""
        return db.query(EmergencyEpisode).filter(EmergencyEpisode.id == episode_id).first()

    @staticmethod
    def list_episodes(db: Session, limit: int = 50) -> list[EmergencyEpisode]:
        """Lista episodios recientes para operacion y auditoria."""
        safe_limit = max(1, min(limit, 200))
        return (
            db.query(EmergencyEpisode)
            .order_by(EmergencyEpisode.created_at.desc(), EmergencyEpisode.id.desc())
            .limit(safe_limit)
            .all()
        )

    @staticmethod
    def transition_episode(
        db: Session,
        episode_id: int,
        payload: EmergencyEpisodeTransitionRequest,
    ) -> EmergencyEpisode:
        """Aplica una transicion valida y actualiza timestamps/KPIs base."""
        episode = EmergencyEpisodeService.get_episode_by_id(db, episode_id)
        if episode is None:
            raise ValueError("Episodio no encontrado.")

        current_stage = episode.current_stage
        if payload.next_stage not in ALLOWED_TRANSITIONS.get(current_stage, set()):
            raise ValueError(
                f"Transicion invalida desde '{current_stage}' hacia '{payload.next_stage}'."
            )

        if payload.next_stage in {"immediate_care", "monitored_waiting_room"}:
            if payload.priority_risk is None:
                raise ValueError("Debe indicar `priority_risk` al salir de triaje.")

        if payload.next_stage == "disposition_decision" and payload.disposition is not None:
            raise ValueError("No indicar `disposition` antes de etapa final de destino.")

        now = datetime.now(timezone.utc)
        episode.current_stage = payload.next_stage

        if payload.priority_risk is not None:
            episode.priority_risk = payload.priority_risk

        if payload.notes is not None:
            episode.notes = payload.notes

        if payload.next_stage == "nursing_triage" and episode.triaged_at is None:
            episode.triaged_at = now
        if payload.next_stage == "medical_evaluation" and episode.medical_evaluation_at is None:
            episode.medical_evaluation_at = now
        if (
            payload.next_stage == "treatment_observation"
            and episode.diagnostics_completed_at is None
        ):
            episode.diagnostics_completed_at = now
        if payload.next_stage == "disposition_decision":
            episode.disposition_decided_at = now
        if payload.next_stage in DISPOSITION_BY_STAGE:
            episode.disposition = DISPOSITION_BY_STAGE[payload.next_stage]
        if payload.next_stage == "episode_closed":
            episode.closed_at = now

        db.add(episode)
        db.commit()
        db.refresh(episode)
        return episode

    @staticmethod
    def build_kpi_summary(episode: EmergencyEpisode) -> EmergencyEpisodeKpiSummaryResponse:
        """Calcula duraciones clave del flujo para medir eficiencia operativa."""

        def _minutes_between(start: datetime | None, end: datetime | None) -> float | None:
            if start is None or end is None:
                return None
            return round((end - start).total_seconds() / 60, 2)

        return EmergencyEpisodeKpiSummaryResponse(
            episode_id=episode.id,
            minutes_arrival_to_triage=_minutes_between(episode.arrived_at, episode.triaged_at),
            minutes_triage_to_medical_evaluation=_minutes_between(
                episode.triaged_at,
                episode.medical_evaluation_at,
            ),
            minutes_medical_evaluation_to_disposition=_minutes_between(
                episode.medical_evaluation_at,
                episode.disposition_decided_at,
            ),
            minutes_total_episode=_minutes_between(episode.arrived_at, episode.closed_at),
            final_stage=episode.current_stage,
            disposition=episode.disposition,
        )
