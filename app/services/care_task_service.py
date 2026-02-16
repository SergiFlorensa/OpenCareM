"""
Servicio de CareTask - Logica de negocio para el dominio clinico-operativo.
"""
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.agent_run import AgentRun
from app.models.care_task import CareTask
from app.models.care_task_cardio_risk_audit_log import CareTaskCardioRiskAuditLog
from app.models.care_task_medicolegal_audit_log import CareTaskMedicolegalAuditLog
from app.models.care_task_resuscitation_audit_log import CareTaskResuscitationAuditLog
from app.models.care_task_scasest_audit_log import CareTaskScasestAuditLog
from app.models.care_task_screening_audit_log import CareTaskScreeningAuditLog
from app.models.care_task_triage_audit_log import CareTaskTriageAuditLog
from app.models.care_task_triage_review import CareTaskTriageReview
from app.schemas.care_task import (
    CareTaskCardioRiskAuditRequest,
    CareTaskCreate,
    CareTaskMedicolegalAuditRequest,
    CareTaskResuscitationAuditRequest,
    CareTaskScasestAuditRequest,
    CareTaskScreeningAuditRequest,
    CareTaskTriageApprovalRequest,
    CareTaskTriageAuditRequest,
    CareTaskUpdate,
)

ALLOWED_CLINICAL_PRIORITIES = {"low", "medium", "high", "critical"}


class CareTaskService:
    """Servicio CRUD para `CareTask`."""

    @staticmethod
    def create_care_task(db: Session, task_data: CareTaskCreate) -> CareTask:
        """Crea un CareTask nuevo con validaciones de dominio."""
        priority = task_data.clinical_priority.lower()
        if priority not in ALLOWED_CLINICAL_PRIORITIES:
            raise ValueError(
                "Valor de prioridad clinica invalido. Permitidos: low, medium, high, critical"
            )

        db_task = CareTask(
            title=task_data.title,
            description=task_data.description,
            clinical_priority=priority,
            specialty=task_data.specialty,
            patient_reference=task_data.patient_reference,
            sla_target_minutes=task_data.sla_target_minutes,
            human_review_required=task_data.human_review_required,
            completed=task_data.completed,
        )
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        return db_task

    @staticmethod
    def get_care_task_by_id(db: Session, task_id: int) -> Optional[CareTask]:
        """Devuelve un CareTask por ID o `None`."""
        return db.query(CareTask).filter(CareTask.id == task_id).first()

    @staticmethod
    def get_all_care_tasks(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        completed: Optional[bool] = None,
        clinical_priority: Optional[str] = None,
        patient_reference: Optional[str] = None,
    ) -> List[CareTask]:
        """Lista CareTask con filtros de estado y prioridad."""
        query = db.query(CareTask)
        if completed is not None:
            query = query.filter(CareTask.completed == completed)
        if clinical_priority is not None:
            query = query.filter(CareTask.clinical_priority == clinical_priority.lower())
        if patient_reference:
            query = query.filter(CareTask.patient_reference == patient_reference)
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def update_care_task(
        db: Session, task_id: int, task_data: CareTaskUpdate
    ) -> Optional[CareTask]:
        """Actualiza campos enviados y devuelve el recurso actualizado."""
        db_task = db.query(CareTask).filter(CareTask.id == task_id).first()
        if not db_task:
            return None

        update_dict = task_data.model_dump(exclude_unset=True)
        if "clinical_priority" in update_dict and update_dict["clinical_priority"] is not None:
            normalized = update_dict["clinical_priority"].lower()
            if normalized not in ALLOWED_CLINICAL_PRIORITIES:
                raise ValueError(
                    "Valor de prioridad clinica invalido. Permitidos: low, medium, high, critical"
                )
            update_dict["clinical_priority"] = normalized

        for field, value in update_dict.items():
            setattr(db_task, field, value)

        db.commit()
        db.refresh(db_task)
        return db_task

    @staticmethod
    def delete_care_task(db: Session, task_id: int) -> bool:
        """Elimina un CareTask si existe."""
        db_task = db.query(CareTask).filter(CareTask.id == task_id).first()
        if not db_task:
            return False
        db.delete(db_task)
        db.commit()
        return True

    @staticmethod
    def get_care_tasks_count(
        db: Session,
        completed: Optional[bool] = None,
        clinical_priority: Optional[str] = None,
        patient_reference: Optional[str] = None,
    ) -> int:
        """Cuenta CareTask totales o filtrados."""
        query = db.query(CareTask)
        if completed is not None:
            query = query.filter(CareTask.completed == completed)
        if clinical_priority is not None:
            query = query.filter(CareTask.clinical_priority == clinical_priority.lower())
        if patient_reference:
            query = query.filter(CareTask.patient_reference == patient_reference)
        return query.count()

    @staticmethod
    def approve_care_task_triage(
        db: Session, task_id: int, approval: CareTaskTriageApprovalRequest
    ) -> CareTaskTriageReview:
        """Guarda la decision humana sobre una corrida de triaje del CareTask."""
        run = db.query(AgentRun).filter(AgentRun.id == approval.agent_run_id).first()
        if run is None:
            raise ValueError("Ejecucion de agente no encontrada.")
        if run.workflow_name != "care_task_triage_v1":
            raise ValueError("La ejecucion indicada no pertenece a un triaje de CareTask.")

        run_task_id = run.run_input.get("care_task_id") if run.run_input else None
        if run_task_id != task_id:
            raise ValueError("La ejecucion de agente no pertenece al CareTask indicado.")

        review = (
            db.query(CareTaskTriageReview)
            .filter(CareTaskTriageReview.agent_run_id == approval.agent_run_id)
            .first()
        )
        if review is None:
            review = CareTaskTriageReview(
                care_task_id=task_id,
                agent_run_id=approval.agent_run_id,
                approved=approval.approved,
                reviewer_note=approval.reviewer_note,
                reviewed_by=approval.reviewed_by,
            )
            db.add(review)
        else:
            review.approved = approval.approved
            review.reviewer_note = approval.reviewer_note
            review.reviewed_by = approval.reviewed_by
            db.add(review)

        db.commit()
        db.refresh(review)
        return review

    @staticmethod
    def _get_valid_care_task_run(db: Session, task_id: int, agent_run_id: int) -> AgentRun:
        """Valida que la corrida exista y pertenezca al CareTask indicado."""
        run = db.query(AgentRun).filter(AgentRun.id == agent_run_id).first()
        if run is None:
            raise ValueError("Ejecucion de agente no encontrada.")
        if run.workflow_name != "care_task_triage_v1":
            raise ValueError("La ejecucion indicada no pertenece a un triaje de CareTask.")

        run_task_id = run.run_input.get("care_task_id") if run.run_input else None
        if run_task_id != task_id:
            raise ValueError("La ejecucion de agente no pertenece al CareTask indicado.")
        return run

    @staticmethod
    def _infer_ai_triage_level(run: AgentRun) -> int:
        """Infiere nivel Manchester (1..5) desde salida de run de triaje."""
        triage = run.run_output.get("triage", {}) if run.run_output else {}
        level = triage.get("triage_level")
        if isinstance(level, int) and 1 <= level <= 5:
            return level

        priority = str(triage.get("priority", "")).lower()
        priority_map = {
            "critical": 1,
            "high": 2,
            "medium": 3,
            "low": 4,
        }
        return priority_map.get(priority, 3)

    @staticmethod
    def _classify_triage_deviation(ai_level: int, human_level: int) -> str:
        """Clasifica desviacion entre recomendacion IA y validacion humana."""
        if ai_level == human_level:
            return "match"
        if ai_level > human_level:
            return "under_triage"
        return "over_triage"

    @staticmethod
    def create_or_update_triage_audit(
        db: Session, task_id: int, payload: CareTaskTriageAuditRequest
    ) -> CareTaskTriageAuditLog:
        """Registra auditoria de triaje IA vs humano para medir seguridad operacional."""
        run = CareTaskService._get_valid_care_task_run(
            db=db, task_id=task_id, agent_run_id=payload.agent_run_id
        )
        ai_level = CareTaskService._infer_ai_triage_level(run)
        classification = CareTaskService._classify_triage_deviation(
            ai_level=ai_level,
            human_level=payload.human_validated_level,
        )

        audit = (
            db.query(CareTaskTriageAuditLog)
            .filter(CareTaskTriageAuditLog.agent_run_id == payload.agent_run_id)
            .first()
        )
        if audit is None:
            audit = CareTaskTriageAuditLog(
                care_task_id=task_id,
                agent_run_id=payload.agent_run_id,
                ai_recommended_level=ai_level,
                human_validated_level=payload.human_validated_level,
                classification=classification,
                reviewer_note=payload.reviewer_note,
                reviewed_by=payload.reviewed_by,
            )
            db.add(audit)
        else:
            audit.ai_recommended_level = ai_level
            audit.human_validated_level = payload.human_validated_level
            audit.classification = classification
            audit.reviewer_note = payload.reviewer_note
            audit.reviewed_by = payload.reviewed_by
            db.add(audit)

        db.commit()
        db.refresh(audit)
        return audit

    @staticmethod
    def list_triage_audits(
        db: Session,
        task_id: int,
        limit: int = 50,
    ) -> list[CareTaskTriageAuditLog]:
        """Lista auditorias de triaje por CareTask, ordenadas por fecha reciente."""
        safe_limit = max(1, min(limit, 200))
        return (
            db.query(CareTaskTriageAuditLog)
            .filter(CareTaskTriageAuditLog.care_task_id == task_id)
            .order_by(CareTaskTriageAuditLog.created_at.desc(), CareTaskTriageAuditLog.id.desc())
            .limit(safe_limit)
            .all()
        )

    @staticmethod
    def get_triage_audit_summary(db: Session, task_id: int | None = None) -> dict[str, float | int]:
        """Devuelve agregados de calidad de triaje para observabilidad."""
        query = db.query(CareTaskTriageAuditLog)
        if task_id is not None:
            query = query.filter(CareTaskTriageAuditLog.care_task_id == task_id)

        total_audits = query.count()
        matches = query.filter(CareTaskTriageAuditLog.classification == "match").count()
        under_triage = query.filter(CareTaskTriageAuditLog.classification == "under_triage").count()
        over_triage = query.filter(CareTaskTriageAuditLog.classification == "over_triage").count()

        under_rate = 0.0
        over_rate = 0.0
        if total_audits > 0:
            under_rate = round((under_triage / total_audits) * 100, 2)
            over_rate = round((over_triage / total_audits) * 100, 2)

        return {
            "total_audits": total_audits,
            "matches": matches,
            "under_triage": under_triage,
            "over_triage": over_triage,
            "under_triage_rate_percent": under_rate,
            "over_triage_rate_percent": over_rate,
        }

    @staticmethod
    def _get_valid_screening_run(db: Session, task_id: int, agent_run_id: int) -> AgentRun:
        """Valida que la corrida exista y pertenezca al screening del CareTask indicado."""
        run = db.query(AgentRun).filter(AgentRun.id == agent_run_id).first()
        if run is None:
            raise ValueError("Ejecucion de agente no encontrada.")
        if run.workflow_name != "advanced_screening_support_v1":
            raise ValueError("La ejecucion indicada no pertenece a screening avanzado.")

        run_task_id = run.run_input.get("care_task_id") if run.run_input else None
        if run_task_id != task_id:
            raise ValueError("La ejecucion de agente no pertenece al CareTask indicado.")
        return run

    @staticmethod
    def _extract_ai_screening_flags(run: AgentRun) -> dict[str, bool | str]:
        """Extrae nivel de riesgo y señales clave desde salida del workflow de screening."""
        output = run.run_output.get("advanced_screening", {}) if run.run_output else {}
        actions = output.get("screening_actions", [])
        if not isinstance(actions, list):
            actions = []

        action_text = " ".join(str(item).lower() for item in actions)
        return {
            "risk_level": str(output.get("geriatric_risk_level", "medium")).lower(),
            "hiv_screening_suggested": "cribado vih" in action_text,
            "sepsis_route_suggested": "sepsis" in action_text,
            "persistent_covid_suspected": bool(output.get("persistent_covid_suspected", False)),
            "long_acting_candidate": bool(output.get("long_acting_candidate", False)),
        }

    @staticmethod
    def _classify_screening_deviation(ai_level: str, human_level: str) -> str:
        """Clasifica desviacion global de severidad en screening avanzado."""
        level_map = {"low": 1, "medium": 2, "high": 3}
        ai_value = level_map.get(ai_level, 2)
        human_value = level_map.get(human_level, 2)
        if ai_value == human_value:
            return "match"
        if ai_value < human_value:
            return "under_screening"
        return "over_screening"

    @staticmethod
    def create_or_update_screening_audit(
        db: Session, task_id: int, payload: CareTaskScreeningAuditRequest
    ) -> CareTaskScreeningAuditLog:
        """Registra auditoria del screening para medir precision operativa por regla."""
        run = CareTaskService._get_valid_screening_run(
            db=db, task_id=task_id, agent_run_id=payload.agent_run_id
        )
        ai_flags = CareTaskService._extract_ai_screening_flags(run)
        ai_risk_level = str(ai_flags["risk_level"])
        classification = CareTaskService._classify_screening_deviation(
            ai_level=ai_risk_level,
            human_level=payload.human_validated_risk_level.lower(),
        )

        audit = (
            db.query(CareTaskScreeningAuditLog)
            .filter(CareTaskScreeningAuditLog.agent_run_id == payload.agent_run_id)
            .first()
        )
        if audit is None:
            audit = CareTaskScreeningAuditLog(
                care_task_id=task_id,
                agent_run_id=payload.agent_run_id,
                ai_geriatric_risk_level=ai_risk_level,
                human_validated_risk_level=payload.human_validated_risk_level.lower(),
                classification=classification,
                ai_hiv_screening_suggested=bool(ai_flags["hiv_screening_suggested"]),
                human_hiv_screening_suggested=payload.human_hiv_screening_suggested,
                ai_sepsis_route_suggested=bool(ai_flags["sepsis_route_suggested"]),
                human_sepsis_route_suggested=payload.human_sepsis_route_suggested,
                ai_persistent_covid_suspected=bool(ai_flags["persistent_covid_suspected"]),
                human_persistent_covid_suspected=payload.human_persistent_covid_suspected,
                ai_long_acting_candidate=bool(ai_flags["long_acting_candidate"]),
                human_long_acting_candidate=payload.human_long_acting_candidate,
                reviewer_note=payload.reviewer_note,
                reviewed_by=payload.reviewed_by,
            )
            db.add(audit)
        else:
            audit.ai_geriatric_risk_level = ai_risk_level
            audit.human_validated_risk_level = payload.human_validated_risk_level.lower()
            audit.classification = classification
            audit.ai_hiv_screening_suggested = bool(ai_flags["hiv_screening_suggested"])
            audit.human_hiv_screening_suggested = payload.human_hiv_screening_suggested
            audit.ai_sepsis_route_suggested = bool(ai_flags["sepsis_route_suggested"])
            audit.human_sepsis_route_suggested = payload.human_sepsis_route_suggested
            audit.ai_persistent_covid_suspected = bool(ai_flags["persistent_covid_suspected"])
            audit.human_persistent_covid_suspected = payload.human_persistent_covid_suspected
            audit.ai_long_acting_candidate = bool(ai_flags["long_acting_candidate"])
            audit.human_long_acting_candidate = payload.human_long_acting_candidate
            audit.reviewer_note = payload.reviewer_note
            audit.reviewed_by = payload.reviewed_by
            db.add(audit)

        db.commit()
        db.refresh(audit)
        return audit

    @staticmethod
    def list_screening_audits(
        db: Session,
        task_id: int,
        limit: int = 50,
    ) -> list[CareTaskScreeningAuditLog]:
        """Lista auditorias de screening por CareTask, ordenadas por fecha reciente."""
        safe_limit = max(1, min(limit, 200))
        return (
            db.query(CareTaskScreeningAuditLog)
            .filter(CareTaskScreeningAuditLog.care_task_id == task_id)
            .order_by(
                CareTaskScreeningAuditLog.created_at.desc(),
                CareTaskScreeningAuditLog.id.desc(),
            )
            .limit(safe_limit)
            .all()
        )

    @staticmethod
    def get_screening_audit_summary(
        db: Session, task_id: int | None = None
    ) -> dict[str, float | int]:
        """Devuelve agregados de calidad del screening para observabilidad."""
        query = db.query(CareTaskScreeningAuditLog)
        if task_id is not None:
            query = query.filter(CareTaskScreeningAuditLog.care_task_id == task_id)

        total_audits = query.count()
        matches = query.filter(CareTaskScreeningAuditLog.classification == "match").count()
        under_screening = query.filter(
            CareTaskScreeningAuditLog.classification == "under_screening"
        ).count()
        over_screening = query.filter(
            CareTaskScreeningAuditLog.classification == "over_screening"
        ).count()

        def _match_rate(ai_field: str, human_field: str) -> float:
            if total_audits == 0:
                return 0.0
            same = 0
            for item in query.all():
                if getattr(item, ai_field) == getattr(item, human_field):
                    same += 1
            return round((same / total_audits) * 100, 2)

        under_rate = 0.0
        over_rate = 0.0
        if total_audits > 0:
            under_rate = round((under_screening / total_audits) * 100, 2)
            over_rate = round((over_screening / total_audits) * 100, 2)

        return {
            "total_audits": total_audits,
            "matches": matches,
            "under_screening": under_screening,
            "over_screening": over_screening,
            "under_screening_rate_percent": under_rate,
            "over_screening_rate_percent": over_rate,
            "hiv_screening_match_rate_percent": _match_rate(
                "ai_hiv_screening_suggested", "human_hiv_screening_suggested"
            ),
            "sepsis_route_match_rate_percent": _match_rate(
                "ai_sepsis_route_suggested", "human_sepsis_route_suggested"
            ),
            "persistent_covid_match_rate_percent": _match_rate(
                "ai_persistent_covid_suspected", "human_persistent_covid_suspected"
            ),
            "long_acting_match_rate_percent": _match_rate(
                "ai_long_acting_candidate", "human_long_acting_candidate"
            ),
        }

    @staticmethod
    def _get_valid_medicolegal_run(db: Session, task_id: int, agent_run_id: int) -> AgentRun:
        """Valida que la corrida exista y pertenezca al soporte medico-legal del CareTask."""
        run = db.query(AgentRun).filter(AgentRun.id == agent_run_id).first()
        if run is None:
            raise ValueError("Ejecucion de agente no encontrada.")
        if run.workflow_name != "medicolegal_ops_support_v1":
            raise ValueError("La ejecucion indicada no pertenece a soporte medico-legal.")

        run_task_id = run.run_input.get("care_task_id") if run.run_input else None
        if run_task_id != task_id:
            raise ValueError("La ejecucion de agente no pertenece al CareTask indicado.")
        return run

    @staticmethod
    def _extract_ai_medicolegal_flags(run: AgentRun) -> dict[str, bool | str]:
        """Extrae nivel de riesgo y banderas clave desde salida medico-legal."""
        output = run.run_output.get("medicolegal_ops", {}) if run.run_output else {}
        required_documents = output.get("required_documents", [])
        operational_actions = output.get("operational_actions", [])
        critical_legal_alerts = output.get("critical_legal_alerts", [])

        if not isinstance(required_documents, list):
            required_documents = []
        if not isinstance(operational_actions, list):
            operational_actions = []
        if not isinstance(critical_legal_alerts, list):
            critical_legal_alerts = []

        docs_text = " ".join(str(item).lower() for item in required_documents)
        actions_text = " ".join(str(item).lower() for item in operational_actions)
        alerts_text = " ".join(str(item).lower() for item in critical_legal_alerts)
        merged_text = f"{docs_text} {actions_text} {alerts_text}"

        return {
            "legal_risk_level": str(output.get("legal_risk_level", "medium")).lower(),
            "consent_required": "consentimiento informado" in docs_text,
            "judicial_notification_required": any(
                token in merged_text
                for token in [
                    "judicial",
                    "juzgado",
                    "parte judicial",
                    "muerte no natural",
                ]
            ),
            "chain_of_custody_required": "cadena de custodia" in merged_text,
        }

    @staticmethod
    def _classify_medicolegal_deviation(ai_level: str, human_level: str) -> str:
        """Clasifica desviacion global de severidad en soporte medico-legal."""
        level_map = {"low": 1, "medium": 2, "high": 3}
        ai_value = level_map.get(ai_level, 2)
        human_value = level_map.get(human_level, 2)
        if ai_value == human_value:
            return "match"
        if ai_value < human_value:
            return "under_legal_risk"
        return "over_legal_risk"

    @staticmethod
    def create_or_update_medicolegal_audit(
        db: Session, task_id: int, payload: CareTaskMedicolegalAuditRequest
    ) -> CareTaskMedicolegalAuditLog:
        """Registra auditoria del soporte medico-legal para medir precision operativa."""
        run = CareTaskService._get_valid_medicolegal_run(
            db=db, task_id=task_id, agent_run_id=payload.agent_run_id
        )
        ai_flags = CareTaskService._extract_ai_medicolegal_flags(run)
        ai_legal_risk_level = str(ai_flags["legal_risk_level"])
        classification = CareTaskService._classify_medicolegal_deviation(
            ai_level=ai_legal_risk_level,
            human_level=payload.human_validated_legal_risk_level.lower(),
        )

        audit = (
            db.query(CareTaskMedicolegalAuditLog)
            .filter(CareTaskMedicolegalAuditLog.agent_run_id == payload.agent_run_id)
            .first()
        )
        if audit is None:
            audit = CareTaskMedicolegalAuditLog(
                care_task_id=task_id,
                agent_run_id=payload.agent_run_id,
                ai_legal_risk_level=ai_legal_risk_level,
                human_validated_legal_risk_level=payload.human_validated_legal_risk_level.lower(),
                classification=classification,
                ai_consent_required=bool(ai_flags["consent_required"]),
                human_consent_required=payload.human_consent_required,
                ai_judicial_notification_required=bool(ai_flags["judicial_notification_required"]),
                human_judicial_notification_required=(payload.human_judicial_notification_required),
                ai_chain_of_custody_required=bool(ai_flags["chain_of_custody_required"]),
                human_chain_of_custody_required=payload.human_chain_of_custody_required,
                reviewer_note=payload.reviewer_note,
                reviewed_by=payload.reviewed_by,
            )
            db.add(audit)
        else:
            audit.ai_legal_risk_level = ai_legal_risk_level
            audit.human_validated_legal_risk_level = (
                payload.human_validated_legal_risk_level.lower()
            )
            audit.classification = classification
            audit.ai_consent_required = bool(ai_flags["consent_required"])
            audit.human_consent_required = payload.human_consent_required
            audit.ai_judicial_notification_required = bool(
                ai_flags["judicial_notification_required"]
            )
            audit.human_judicial_notification_required = (
                payload.human_judicial_notification_required
            )
            audit.ai_chain_of_custody_required = bool(ai_flags["chain_of_custody_required"])
            audit.human_chain_of_custody_required = payload.human_chain_of_custody_required
            audit.reviewer_note = payload.reviewer_note
            audit.reviewed_by = payload.reviewed_by
            db.add(audit)

        db.commit()
        db.refresh(audit)
        return audit

    @staticmethod
    def list_medicolegal_audits(
        db: Session,
        task_id: int,
        limit: int = 50,
    ) -> list[CareTaskMedicolegalAuditLog]:
        """Lista auditorias medico-legales por CareTask, ordenadas por fecha reciente."""
        safe_limit = max(1, min(limit, 200))
        return (
            db.query(CareTaskMedicolegalAuditLog)
            .filter(CareTaskMedicolegalAuditLog.care_task_id == task_id)
            .order_by(
                CareTaskMedicolegalAuditLog.created_at.desc(),
                CareTaskMedicolegalAuditLog.id.desc(),
            )
            .limit(safe_limit)
            .all()
        )

    @staticmethod
    def get_medicolegal_audit_summary(
        db: Session, task_id: int | None = None
    ) -> dict[str, float | int]:
        """Devuelve agregados de calidad medico-legal para observabilidad."""
        query = db.query(CareTaskMedicolegalAuditLog)
        if task_id is not None:
            query = query.filter(CareTaskMedicolegalAuditLog.care_task_id == task_id)

        total_audits = query.count()
        matches = query.filter(CareTaskMedicolegalAuditLog.classification == "match").count()
        under_legal_risk = query.filter(
            CareTaskMedicolegalAuditLog.classification == "under_legal_risk"
        ).count()
        over_legal_risk = query.filter(
            CareTaskMedicolegalAuditLog.classification == "over_legal_risk"
        ).count()

        def _match_rate(ai_field: str, human_field: str) -> float:
            if total_audits == 0:
                return 0.0
            same = 0
            for item in query.all():
                if getattr(item, ai_field) == getattr(item, human_field):
                    same += 1
            return round((same / total_audits) * 100, 2)

        under_rate = 0.0
        over_rate = 0.0
        if total_audits > 0:
            under_rate = round((under_legal_risk / total_audits) * 100, 2)
            over_rate = round((over_legal_risk / total_audits) * 100, 2)

        return {
            "total_audits": total_audits,
            "matches": matches,
            "under_legal_risk": under_legal_risk,
            "over_legal_risk": over_legal_risk,
            "under_legal_risk_rate_percent": under_rate,
            "over_legal_risk_rate_percent": over_rate,
            "consent_required_match_rate_percent": _match_rate(
                "ai_consent_required", "human_consent_required"
            ),
            "judicial_notification_match_rate_percent": _match_rate(
                "ai_judicial_notification_required",
                "human_judicial_notification_required",
            ),
            "chain_of_custody_match_rate_percent": _match_rate(
                "ai_chain_of_custody_required",
                "human_chain_of_custody_required",
            ),
        }

    @staticmethod
    def _get_valid_scasest_run(db: Session, task_id: int, agent_run_id: int) -> AgentRun:
        """Valida que la corrida exista y pertenezca al soporte SCASEST del CareTask."""
        run = db.query(AgentRun).filter(AgentRun.id == agent_run_id).first()
        if run is None:
            raise ValueError("Ejecucion de agente no encontrada.")
        if run.workflow_name != "scasest_protocol_support_v1":
            raise ValueError("La ejecucion indicada no pertenece a soporte SCASEST.")

        run_task_id = run.run_input.get("care_task_id") if run.run_input else None
        if run_task_id != task_id:
            raise ValueError("La ejecucion de agente no pertenece al CareTask indicado.")
        return run

    @staticmethod
    def _extract_ai_scasest_flags(run: AgentRun) -> dict[str, bool]:
        """Extrae banderas clave desde salida del workflow de SCASEST."""
        output = run.run_output.get("scasest_protocol", {}) if run.run_output else {}
        escalation_actions = output.get("escalation_actions", [])
        initial_treatment_actions = output.get("initial_treatment_actions", [])

        if not isinstance(escalation_actions, list):
            escalation_actions = []
        if not isinstance(initial_treatment_actions, list):
            initial_treatment_actions = []

        escalation_text = " ".join(str(item).lower() for item in escalation_actions)
        treatment_text = " ".join(str(item).lower() for item in initial_treatment_actions)

        return {
            "high_risk_scasest": bool(output.get("high_risk_scasest", False)),
            "escalation_required": any(
                token in escalation_text for token in ["escalar", "uci", "coronaria", "cardiologia"]
            ),
            "immediate_antiischemic_strategy": any(
                token in treatment_text
                for token in ["aas", "antiagregante", "anticoagulacion", "nitratos"]
            ),
        }

    @staticmethod
    def _classify_scasest_deviation(ai_high_risk: bool, human_high_risk: bool) -> str:
        """Clasifica desviacion global de riesgo en soporte SCASEST."""
        if ai_high_risk == human_high_risk:
            return "match"
        if not ai_high_risk and human_high_risk:
            return "under_scasest_risk"
        return "over_scasest_risk"

    @staticmethod
    def create_or_update_scasest_audit(
        db: Session, task_id: int, payload: CareTaskScasestAuditRequest
    ) -> CareTaskScasestAuditLog:
        """Registra auditoria del soporte SCASEST para medir precision operativa."""
        run = CareTaskService._get_valid_scasest_run(
            db=db, task_id=task_id, agent_run_id=payload.agent_run_id
        )
        ai_flags = CareTaskService._extract_ai_scasest_flags(run)
        ai_high_risk = bool(ai_flags["high_risk_scasest"])
        classification = CareTaskService._classify_scasest_deviation(
            ai_high_risk=ai_high_risk,
            human_high_risk=payload.human_validated_high_risk_scasest,
        )

        audit = (
            db.query(CareTaskScasestAuditLog)
            .filter(CareTaskScasestAuditLog.agent_run_id == payload.agent_run_id)
            .first()
        )
        if audit is None:
            audit = CareTaskScasestAuditLog(
                care_task_id=task_id,
                agent_run_id=payload.agent_run_id,
                ai_high_risk_scasest=ai_high_risk,
                human_validated_high_risk_scasest=payload.human_validated_high_risk_scasest,
                classification=classification,
                ai_escalation_required=bool(ai_flags["escalation_required"]),
                human_escalation_required=payload.human_escalation_required,
                ai_immediate_antiischemic_strategy=bool(
                    ai_flags["immediate_antiischemic_strategy"]
                ),
                human_immediate_antiischemic_strategy=(
                    payload.human_immediate_antiischemic_strategy
                ),
                reviewer_note=payload.reviewer_note,
                reviewed_by=payload.reviewed_by,
            )
            db.add(audit)
        else:
            audit.ai_high_risk_scasest = ai_high_risk
            audit.human_validated_high_risk_scasest = payload.human_validated_high_risk_scasest
            audit.classification = classification
            audit.ai_escalation_required = bool(ai_flags["escalation_required"])
            audit.human_escalation_required = payload.human_escalation_required
            audit.ai_immediate_antiischemic_strategy = bool(
                ai_flags["immediate_antiischemic_strategy"]
            )
            audit.human_immediate_antiischemic_strategy = (
                payload.human_immediate_antiischemic_strategy
            )
            audit.reviewer_note = payload.reviewer_note
            audit.reviewed_by = payload.reviewed_by
            db.add(audit)

        db.commit()
        db.refresh(audit)
        return audit

    @staticmethod
    def list_scasest_audits(
        db: Session,
        task_id: int,
        limit: int = 50,
    ) -> list[CareTaskScasestAuditLog]:
        """Lista auditorias SCASEST por CareTask, ordenadas por fecha reciente."""
        safe_limit = max(1, min(limit, 200))
        return (
            db.query(CareTaskScasestAuditLog)
            .filter(CareTaskScasestAuditLog.care_task_id == task_id)
            .order_by(
                CareTaskScasestAuditLog.created_at.desc(),
                CareTaskScasestAuditLog.id.desc(),
            )
            .limit(safe_limit)
            .all()
        )

    @staticmethod
    def get_scasest_audit_summary(
        db: Session, task_id: int | None = None
    ) -> dict[str, float | int]:
        """Devuelve agregados de calidad SCASEST para observabilidad."""
        query = db.query(CareTaskScasestAuditLog)
        if task_id is not None:
            query = query.filter(CareTaskScasestAuditLog.care_task_id == task_id)

        total_audits = query.count()
        matches = query.filter(CareTaskScasestAuditLog.classification == "match").count()
        under_scasest_risk = query.filter(
            CareTaskScasestAuditLog.classification == "under_scasest_risk"
        ).count()
        over_scasest_risk = query.filter(
            CareTaskScasestAuditLog.classification == "over_scasest_risk"
        ).count()

        def _match_rate(ai_field: str, human_field: str) -> float:
            if total_audits == 0:
                return 0.0
            same = 0
            for item in query.all():
                if getattr(item, ai_field) == getattr(item, human_field):
                    same += 1
            return round((same / total_audits) * 100, 2)

        under_rate = 0.0
        over_rate = 0.0
        if total_audits > 0:
            under_rate = round((under_scasest_risk / total_audits) * 100, 2)
            over_rate = round((over_scasest_risk / total_audits) * 100, 2)

        return {
            "total_audits": total_audits,
            "matches": matches,
            "under_scasest_risk": under_scasest_risk,
            "over_scasest_risk": over_scasest_risk,
            "under_scasest_risk_rate_percent": under_rate,
            "over_scasest_risk_rate_percent": over_rate,
            "escalation_required_match_rate_percent": _match_rate(
                "ai_escalation_required", "human_escalation_required"
            ),
            "immediate_antiischemic_strategy_match_rate_percent": _match_rate(
                "ai_immediate_antiischemic_strategy",
                "human_immediate_antiischemic_strategy",
            ),
        }

    @staticmethod
    def _get_valid_cardio_risk_run(db: Session, task_id: int, agent_run_id: int) -> AgentRun:
        """Valida que la corrida exista y pertenezca al soporte cardiovascular del CareTask."""
        run = db.query(AgentRun).filter(AgentRun.id == agent_run_id).first()
        if run is None:
            raise ValueError("Ejecucion de agente no encontrada.")
        if run.workflow_name != "cardio_risk_support_v1":
            raise ValueError("La ejecucion indicada no pertenece a soporte cardiovascular.")

        run_task_id = run.run_input.get("care_task_id") if run.run_input else None
        if run_task_id != task_id:
            raise ValueError("La ejecucion de agente no pertenece al CareTask indicado.")
        return run

    @staticmethod
    def _extract_ai_cardio_risk_flags(run: AgentRun) -> dict[str, bool | str]:
        """Extrae riesgo global y banderas clave desde salida de soporte cardiovascular."""
        output = run.run_output.get("cardio_risk_support", {}) if run.run_output else {}
        return {
            "risk_level": str(output.get("risk_level", "moderate")).lower(),
            "non_hdl_target_required": bool(output.get("non_hdl_target_required", False)),
            "pharmacologic_strategy_suggested": bool(
                output.get("pharmacologic_strategy_suggested", False)
            ),
            "intensive_lifestyle_required": bool(output.get("intensive_lifestyle_required", False)),
        }

    @staticmethod
    def _classify_cardio_risk_deviation(ai_level: str, human_level: str) -> str:
        """Clasifica desviacion global de severidad en soporte cardiovascular."""
        level_map = {"low": 1, "moderate": 2, "high": 3, "very_high": 4}
        ai_value = level_map.get(ai_level, 2)
        human_value = level_map.get(human_level, 2)
        if ai_value == human_value:
            return "match"
        if ai_value < human_value:
            return "under_cardio_risk"
        return "over_cardio_risk"

    @staticmethod
    def create_or_update_cardio_risk_audit(
        db: Session, task_id: int, payload: CareTaskCardioRiskAuditRequest
    ) -> CareTaskCardioRiskAuditLog:
        """Registra auditoria del soporte cardiovascular para medir precision operativa."""
        run = CareTaskService._get_valid_cardio_risk_run(
            db=db, task_id=task_id, agent_run_id=payload.agent_run_id
        )
        ai_flags = CareTaskService._extract_ai_cardio_risk_flags(run)
        ai_risk_level = str(ai_flags["risk_level"])
        classification = CareTaskService._classify_cardio_risk_deviation(
            ai_level=ai_risk_level,
            human_level=payload.human_validated_risk_level.lower(),
        )

        audit = (
            db.query(CareTaskCardioRiskAuditLog)
            .filter(CareTaskCardioRiskAuditLog.agent_run_id == payload.agent_run_id)
            .first()
        )
        if audit is None:
            audit = CareTaskCardioRiskAuditLog(
                care_task_id=task_id,
                agent_run_id=payload.agent_run_id,
                ai_risk_level=ai_risk_level,
                human_validated_risk_level=payload.human_validated_risk_level.lower(),
                classification=classification,
                ai_non_hdl_target_required=bool(ai_flags["non_hdl_target_required"]),
                human_non_hdl_target_required=payload.human_non_hdl_target_required,
                ai_pharmacologic_strategy_suggested=bool(
                    ai_flags["pharmacologic_strategy_suggested"]
                ),
                human_pharmacologic_strategy_suggested=(
                    payload.human_pharmacologic_strategy_suggested
                ),
                ai_intensive_lifestyle_required=bool(ai_flags["intensive_lifestyle_required"]),
                human_intensive_lifestyle_required=payload.human_intensive_lifestyle_required,
                reviewer_note=payload.reviewer_note,
                reviewed_by=payload.reviewed_by,
            )
            db.add(audit)
        else:
            audit.ai_risk_level = ai_risk_level
            audit.human_validated_risk_level = payload.human_validated_risk_level.lower()
            audit.classification = classification
            audit.ai_non_hdl_target_required = bool(ai_flags["non_hdl_target_required"])
            audit.human_non_hdl_target_required = payload.human_non_hdl_target_required
            audit.ai_pharmacologic_strategy_suggested = bool(
                ai_flags["pharmacologic_strategy_suggested"]
            )
            audit.human_pharmacologic_strategy_suggested = (
                payload.human_pharmacologic_strategy_suggested
            )
            audit.ai_intensive_lifestyle_required = bool(ai_flags["intensive_lifestyle_required"])
            audit.human_intensive_lifestyle_required = payload.human_intensive_lifestyle_required
            audit.reviewer_note = payload.reviewer_note
            audit.reviewed_by = payload.reviewed_by
            db.add(audit)

        db.commit()
        db.refresh(audit)
        return audit

    @staticmethod
    def list_cardio_risk_audits(
        db: Session,
        task_id: int,
        limit: int = 50,
    ) -> list[CareTaskCardioRiskAuditLog]:
        """Lista auditorias cardiovasculares por CareTask, ordenadas por fecha reciente."""
        safe_limit = max(1, min(limit, 200))
        return (
            db.query(CareTaskCardioRiskAuditLog)
            .filter(CareTaskCardioRiskAuditLog.care_task_id == task_id)
            .order_by(
                CareTaskCardioRiskAuditLog.created_at.desc(),
                CareTaskCardioRiskAuditLog.id.desc(),
            )
            .limit(safe_limit)
            .all()
        )

    @staticmethod
    def get_cardio_risk_audit_summary(
        db: Session, task_id: int | None = None
    ) -> dict[str, float | int]:
        """Devuelve agregados de calidad cardiovascular para observabilidad."""
        query = db.query(CareTaskCardioRiskAuditLog)
        if task_id is not None:
            query = query.filter(CareTaskCardioRiskAuditLog.care_task_id == task_id)

        total_audits = query.count()
        matches = query.filter(CareTaskCardioRiskAuditLog.classification == "match").count()
        under_cardio_risk = query.filter(
            CareTaskCardioRiskAuditLog.classification == "under_cardio_risk"
        ).count()
        over_cardio_risk = query.filter(
            CareTaskCardioRiskAuditLog.classification == "over_cardio_risk"
        ).count()

        def _match_rate(ai_field: str, human_field: str) -> float:
            if total_audits == 0:
                return 0.0
            same = 0
            for item in query.all():
                if getattr(item, ai_field) == getattr(item, human_field):
                    same += 1
            return round((same / total_audits) * 100, 2)

        under_rate = 0.0
        over_rate = 0.0
        if total_audits > 0:
            under_rate = round((under_cardio_risk / total_audits) * 100, 2)
            over_rate = round((over_cardio_risk / total_audits) * 100, 2)

        return {
            "total_audits": total_audits,
            "matches": matches,
            "under_cardio_risk": under_cardio_risk,
            "over_cardio_risk": over_cardio_risk,
            "under_cardio_risk_rate_percent": under_rate,
            "over_cardio_risk_rate_percent": over_rate,
            "non_hdl_target_required_match_rate_percent": _match_rate(
                "ai_non_hdl_target_required", "human_non_hdl_target_required"
            ),
            "pharmacologic_strategy_match_rate_percent": _match_rate(
                "ai_pharmacologic_strategy_suggested",
                "human_pharmacologic_strategy_suggested",
            ),
            "intensive_lifestyle_match_rate_percent": _match_rate(
                "ai_intensive_lifestyle_required",
                "human_intensive_lifestyle_required",
            ),
        }

    @staticmethod
    def _get_valid_resuscitation_run(db: Session, task_id: int, agent_run_id: int) -> AgentRun:
        """Valida que la corrida exista y pertenezca a soporte de reanimacion del CareTask."""
        run = db.query(AgentRun).filter(AgentRun.id == agent_run_id).first()
        if run is None:
            raise ValueError("Ejecucion de agente no encontrada.")
        if run.workflow_name != "resuscitation_protocol_support_v1":
            raise ValueError("La ejecucion indicada no pertenece a soporte de reanimacion.")

        run_task_id = run.run_input.get("care_task_id") if run.run_input else None
        if run_task_id != task_id:
            raise ValueError("La ejecucion de agente no pertenece al CareTask indicado.")
        return run

    @staticmethod
    def _extract_ai_resuscitation_flags(run: AgentRun) -> dict[str, bool | str]:
        """Extrae severidad global y banderas clave desde soporte de reanimacion."""
        output = run.run_output.get("resuscitation_protocol", {}) if run.run_output else {}
        ventilation_actions = output.get("ventilation_actions", [])
        if not isinstance(ventilation_actions, list):
            ventilation_actions = []
        ventilation_text = " ".join(str(item).lower() for item in ventilation_actions)
        return {
            "severity_level": str(output.get("severity_level", "high")).lower(),
            "shock_recommended": bool(output.get("shock_recommended", False)),
            "reversible_causes_required": bool(output.get("reversible_causes_checklist", [])),
            "airway_plan_adequate": "capnografia" in ventilation_text
            or "via aerea" in ventilation_text,
        }

    @staticmethod
    def _classify_resuscitation_deviation(ai_level: str, human_level: str) -> str:
        """Clasifica desviacion global de severidad en soporte de reanimacion."""
        level_map = {"medium": 1, "high": 2, "critical": 3}
        ai_value = level_map.get(ai_level, 2)
        human_value = level_map.get(human_level, 2)
        if ai_value == human_value:
            return "match"
        if ai_value < human_value:
            return "under_resuscitation_risk"
        return "over_resuscitation_risk"

    @staticmethod
    def create_or_update_resuscitation_audit(
        db: Session, task_id: int, payload: CareTaskResuscitationAuditRequest
    ) -> CareTaskResuscitationAuditLog:
        """Registra auditoria del soporte de reanimacion para medir precision operativa."""
        run = CareTaskService._get_valid_resuscitation_run(
            db=db, task_id=task_id, agent_run_id=payload.agent_run_id
        )
        ai_flags = CareTaskService._extract_ai_resuscitation_flags(run)
        ai_severity_level = str(ai_flags["severity_level"])
        classification = CareTaskService._classify_resuscitation_deviation(
            ai_level=ai_severity_level,
            human_level=payload.human_validated_severity_level.lower(),
        )

        audit = (
            db.query(CareTaskResuscitationAuditLog)
            .filter(CareTaskResuscitationAuditLog.agent_run_id == payload.agent_run_id)
            .first()
        )
        if audit is None:
            audit = CareTaskResuscitationAuditLog(
                care_task_id=task_id,
                agent_run_id=payload.agent_run_id,
                ai_severity_level=ai_severity_level,
                human_validated_severity_level=payload.human_validated_severity_level.lower(),
                classification=classification,
                ai_shock_recommended=bool(ai_flags["shock_recommended"]),
                human_shock_recommended=payload.human_shock_recommended,
                ai_reversible_causes_required=bool(ai_flags["reversible_causes_required"]),
                human_reversible_causes_completed=payload.human_reversible_causes_completed,
                ai_airway_plan_adequate=bool(ai_flags["airway_plan_adequate"]),
                human_airway_plan_adequate=payload.human_airway_plan_adequate,
                reviewer_note=payload.reviewer_note,
                reviewed_by=payload.reviewed_by,
            )
            db.add(audit)
        else:
            audit.ai_severity_level = ai_severity_level
            audit.human_validated_severity_level = payload.human_validated_severity_level.lower()
            audit.classification = classification
            audit.ai_shock_recommended = bool(ai_flags["shock_recommended"])
            audit.human_shock_recommended = payload.human_shock_recommended
            audit.ai_reversible_causes_required = bool(ai_flags["reversible_causes_required"])
            audit.human_reversible_causes_completed = payload.human_reversible_causes_completed
            audit.ai_airway_plan_adequate = bool(ai_flags["airway_plan_adequate"])
            audit.human_airway_plan_adequate = payload.human_airway_plan_adequate
            audit.reviewer_note = payload.reviewer_note
            audit.reviewed_by = payload.reviewed_by
            db.add(audit)

        db.commit()
        db.refresh(audit)
        return audit

    @staticmethod
    def list_resuscitation_audits(
        db: Session,
        task_id: int,
        limit: int = 50,
    ) -> list[CareTaskResuscitationAuditLog]:
        """Lista auditorias de reanimacion por CareTask, ordenadas por fecha reciente."""
        safe_limit = max(1, min(limit, 200))
        return (
            db.query(CareTaskResuscitationAuditLog)
            .filter(CareTaskResuscitationAuditLog.care_task_id == task_id)
            .order_by(
                CareTaskResuscitationAuditLog.created_at.desc(),
                CareTaskResuscitationAuditLog.id.desc(),
            )
            .limit(safe_limit)
            .all()
        )

    @staticmethod
    def get_resuscitation_audit_summary(
        db: Session, task_id: int | None = None
    ) -> dict[str, float | int]:
        """Devuelve agregados de calidad de reanimacion para observabilidad."""
        query = db.query(CareTaskResuscitationAuditLog)
        if task_id is not None:
            query = query.filter(CareTaskResuscitationAuditLog.care_task_id == task_id)

        total_audits = query.count()
        matches = query.filter(CareTaskResuscitationAuditLog.classification == "match").count()
        under_resuscitation_risk = query.filter(
            CareTaskResuscitationAuditLog.classification == "under_resuscitation_risk"
        ).count()
        over_resuscitation_risk = query.filter(
            CareTaskResuscitationAuditLog.classification == "over_resuscitation_risk"
        ).count()

        def _match_rate(ai_field: str, human_field: str) -> float:
            if total_audits == 0:
                return 0.0
            same = 0
            for item in query.all():
                if getattr(item, ai_field) == getattr(item, human_field):
                    same += 1
            return round((same / total_audits) * 100, 2)

        under_rate = 0.0
        over_rate = 0.0
        if total_audits > 0:
            under_rate = round((under_resuscitation_risk / total_audits) * 100, 2)
            over_rate = round((over_resuscitation_risk / total_audits) * 100, 2)

        return {
            "total_audits": total_audits,
            "matches": matches,
            "under_resuscitation_risk": under_resuscitation_risk,
            "over_resuscitation_risk": over_resuscitation_risk,
            "under_resuscitation_risk_rate_percent": under_rate,
            "over_resuscitation_risk_rate_percent": over_rate,
            "shock_recommended_match_rate_percent": _match_rate(
                "ai_shock_recommended", "human_shock_recommended"
            ),
            "reversible_causes_match_rate_percent": _match_rate(
                "ai_reversible_causes_required", "human_reversible_causes_completed"
            ),
            "airway_plan_match_rate_percent": _match_rate(
                "ai_airway_plan_adequate", "human_airway_plan_adequate"
            ),
        }

    @staticmethod
    def _build_quality_domain_summary(
        *,
        summary: dict[str, float | int],
        under_key: str,
        over_key: str,
    ) -> dict[str, float | int]:
        """Normaliza resumen de auditoria para scorecard global entre dominios."""
        total_audits = int(summary.get("total_audits", 0))
        matches = int(summary.get("matches", 0))
        under_events = int(summary.get(under_key, 0))
        over_events = int(summary.get(over_key, 0))

        under_rate_percent = 0.0
        over_rate_percent = 0.0
        match_rate_percent = 0.0
        if total_audits > 0:
            under_rate_percent = round((under_events / total_audits) * 100, 2)
            over_rate_percent = round((over_events / total_audits) * 100, 2)
            match_rate_percent = round((matches / total_audits) * 100, 2)

        return {
            "total_audits": total_audits,
            "matches": matches,
            "under_events": under_events,
            "over_events": over_events,
            "under_rate_percent": under_rate_percent,
            "over_rate_percent": over_rate_percent,
            "match_rate_percent": match_rate_percent,
        }

    @staticmethod
    def _classify_global_quality_status(
        *,
        total_audits: int,
        under_rate_percent: float,
        over_rate_percent: float,
    ) -> str:
        """Clasifica estado global de calidad para lectura operativa rapida."""
        if total_audits == 0:
            return "sin_datos"
        if under_rate_percent > 10 or over_rate_percent > 20:
            return "degradado"
        if under_rate_percent > 0 or over_rate_percent > 0:
            return "atencion"
        return "estable"

    @staticmethod
    def get_quality_scorecard(db: Session) -> dict[str, object]:
        """Devuelve scorecard unificado de calidad IA en dominios clinicos clave."""
        triage_summary = CareTaskService.get_triage_audit_summary(db=db)
        screening_summary = CareTaskService.get_screening_audit_summary(db=db)
        medicolegal_summary = CareTaskService.get_medicolegal_audit_summary(db=db)
        scasest_summary = CareTaskService.get_scasest_audit_summary(db=db)
        cardio_risk_summary = CareTaskService.get_cardio_risk_audit_summary(db=db)
        resuscitation_summary = CareTaskService.get_resuscitation_audit_summary(db=db)

        domains = {
            "triage": CareTaskService._build_quality_domain_summary(
                summary=triage_summary,
                under_key="under_triage",
                over_key="over_triage",
            ),
            "screening": CareTaskService._build_quality_domain_summary(
                summary=screening_summary,
                under_key="under_screening",
                over_key="over_screening",
            ),
            "medicolegal": CareTaskService._build_quality_domain_summary(
                summary=medicolegal_summary,
                under_key="under_legal_risk",
                over_key="over_legal_risk",
            ),
            "scasest": CareTaskService._build_quality_domain_summary(
                summary=scasest_summary,
                under_key="under_scasest_risk",
                over_key="over_scasest_risk",
            ),
            "cardio_risk": CareTaskService._build_quality_domain_summary(
                summary=cardio_risk_summary,
                under_key="under_cardio_risk",
                over_key="over_cardio_risk",
            ),
            "resuscitation": CareTaskService._build_quality_domain_summary(
                summary=resuscitation_summary,
                under_key="under_resuscitation_risk",
                over_key="over_resuscitation_risk",
            ),
        }

        total_audits = sum(int(item["total_audits"]) for item in domains.values())
        matches = sum(int(item["matches"]) for item in domains.values())
        under_events = sum(int(item["under_events"]) for item in domains.values())
        over_events = sum(int(item["over_events"]) for item in domains.values())

        under_rate_percent = 0.0
        over_rate_percent = 0.0
        match_rate_percent = 0.0
        if total_audits > 0:
            under_rate_percent = round((under_events / total_audits) * 100, 2)
            over_rate_percent = round((over_events / total_audits) * 100, 2)
            match_rate_percent = round((matches / total_audits) * 100, 2)

        quality_status = CareTaskService._classify_global_quality_status(
            total_audits=total_audits,
            under_rate_percent=under_rate_percent,
            over_rate_percent=over_rate_percent,
        )

        return {
            "total_audits": total_audits,
            "matches": matches,
            "under_events": under_events,
            "over_events": over_events,
            "under_rate_percent": under_rate_percent,
            "over_rate_percent": over_rate_percent,
            "match_rate_percent": match_rate_percent,
            "quality_status": quality_status,
            "domains": domains,
        }
