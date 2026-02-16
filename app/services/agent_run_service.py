import time
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.agent_run import AgentRun, AgentStep
from app.models.care_task import CareTask
from app.schemas.ai import TaskTriageResponse
from app.services.ai_triage_service import AITriageService


class AgentRunService:
    @staticmethod
    def _execute_triage_workflow(
        db: Session,
        *,
        workflow_name: str,
        run_input: dict[str, Any],
        step_name: str,
    ) -> AgentRun:
        """Ejecuta un triaje generico y persiste corrida/paso con trazabilidad completa."""
        run = AgentRun(
            workflow_name=workflow_name,
            status="running",
            run_input=run_input,
            total_cost_usd=0.0,
            total_latency_ms=0,
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        run_started_at = time.perf_counter()
        try:
            step_started_at = time.perf_counter()
            triage = AITriageService.suggest_task_metadata(
                title=str(run_input.get("title", "")),
                description=run_input.get("description"),
            )
            fallback_used = triage.confidence < 0.65
            decision = "use_model_output"
            if fallback_used:
                triage = TaskTriageResponse(
                    priority="medium",
                    category="general",
                    confidence=triage.confidence,
                    reason=(
                        "Confianza por debajo del umbral (0.65); "
                        "se aplico fallback a valores seguros."
                    ),
                    source="rules_fallback",
                )
                decision = "fallback_safe_defaults"

            step_latency_ms = round((time.perf_counter() - step_started_at) * 1000)
            step_output = triage.model_dump()
            AgentRunService._build_trace_step(
                db,
                run_id=run.id,
                step_order=1,
                step_name=step_name,
                status="completed",
                step_input=run_input,
                step_output=step_output,
                decision=decision,
                fallback_used=fallback_used,
                error_message=None,
                step_cost_usd=0.0,
                step_latency_ms=step_latency_ms,
            )

            run.status = "completed"
            run.run_output = {"triage": step_output}
            run.total_cost_usd = 0.0
            run.total_latency_ms = round((time.perf_counter() - run_started_at) * 1000)
            db.add(run)
            db.commit()
            db.refresh(run)
            return run
        except Exception as exc:
            run.status = "failed"
            run.error_message = str(exc)
            run.total_latency_ms = round((time.perf_counter() - run_started_at) * 1000)
            db.add(run)
            db.commit()
            db.refresh(run)
            raise

    @staticmethod
    def get_ops_summary(db: Session, workflow_name: str | None = None) -> dict[str, float | int]:
        """Construye metricas operativas de alto nivel para ejecuciones de agentes."""
        run_query = db.query(AgentRun)
        if workflow_name is not None:
            run_query = run_query.filter(AgentRun.workflow_name == workflow_name)

        total_runs = run_query.count()
        completed_runs = run_query.filter(AgentRun.status == "completed").count()
        failed_runs = run_query.filter(AgentRun.status == "failed").count()

        step_query = db.query(AgentStep).join(AgentRun, AgentStep.run_id == AgentRun.id)
        if workflow_name is not None:
            step_query = step_query.filter(AgentRun.workflow_name == workflow_name)
        fallback_steps = step_query.filter(AgentStep.fallback_used.is_(True)).count()

        fallback_rate_percent = 0.0
        if total_runs > 0:
            fallback_rate_percent = round((fallback_steps / total_runs) * 100, 2)

        return {
            "total_runs": total_runs,
            "completed_runs": completed_runs,
            "failed_runs": failed_runs,
            "fallback_steps": fallback_steps,
            "fallback_rate_percent": fallback_rate_percent,
        }

    @staticmethod
    def list_recent_runs(
        db: Session,
        limit: int = 20,
        status: str | None = None,
        workflow_name: str | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
    ) -> list[AgentRun]:
        """Devuelve ejecuciones recientes para inspeccion rapida de comportamiento."""
        safe_limit = max(1, min(limit, 100))
        query = db.query(AgentRun)
        if status is not None:
            query = query.filter(AgentRun.status == status)
        if workflow_name is not None:
            query = query.filter(AgentRun.workflow_name == workflow_name)
        if created_from is not None:
            query = query.filter(AgentRun.created_at >= created_from)
        if created_to is not None:
            query = query.filter(AgentRun.created_at <= created_to)
        return (
            query.order_by(AgentRun.created_at.desc(), AgentRun.id.desc()).limit(safe_limit).all()
        )

    @staticmethod
    def get_run_with_steps(db: Session, run_id: int) -> tuple[AgentRun | None, list[AgentStep]]:
        """Devuelve una ejecucion y sus pasos ordenados para depuracion detallada."""
        run = db.query(AgentRun).filter(AgentRun.id == run_id).first()
        if run is None:
            return None, []
        steps = (
            db.query(AgentStep)
            .filter(AgentStep.run_id == run.id)
            .order_by(AgentStep.step_order.asc(), AgentStep.id.asc())
            .all()
        )
        return run, steps

    @staticmethod
    def _build_trace_step(
        db: Session,
        *,
        run_id: int,
        step_order: int,
        step_name: str,
        status: str,
        step_input: dict[str, Any],
        step_output: dict[str, Any] | None,
        decision: str | None,
        fallback_used: bool,
        error_message: str | None,
        step_cost_usd: float,
        step_latency_ms: int,
    ) -> AgentStep:
        """Persiste un paso de ejecucion para reconstruir el comportamiento del agente."""
        step = AgentStep(
            run_id=run_id,
            step_order=step_order,
            step_name=step_name,
            status=status,
            step_input=step_input,
            step_output=step_output,
            decision=decision,
            fallback_used=fallback_used,
            error_message=error_message,
            step_cost_usd=step_cost_usd,
            step_latency_ms=step_latency_ms,
        )
        db.add(step)
        db.commit()
        db.refresh(step)
        return step

    @staticmethod
    def run_task_triage_workflow(db: Session, title: str, description: str | None) -> AgentRun:
        """Ejecuta `task_triage_v1` y persiste trazas de corrida/paso con decisiones de fallback."""
        run_input = {"title": title, "description": description}
        return AgentRunService._execute_triage_workflow(
            db=db,
            workflow_name="task_triage_v1",
            run_input=run_input,
            step_name="triage_task",
        )

    @staticmethod
    def run_care_task_triage_workflow(db: Session, care_task: CareTask) -> AgentRun:
        """Ejecuta triaje sobre un CareTask y guarda contexto clinico-operativo en la traza."""
        run_input = {
            "care_task_id": care_task.id,
            "title": care_task.title,
            "description": care_task.description,
            "clinical_priority": care_task.clinical_priority,
            "specialty": care_task.specialty,
            "sla_target_minutes": care_task.sla_target_minutes,
            "human_review_required": care_task.human_review_required,
        }
        return AgentRunService._execute_triage_workflow(
            db=db,
            workflow_name="care_task_triage_v1",
            run_input=run_input,
            step_name="triage_care_task",
        )

    @staticmethod
    def run_respiratory_protocol_workflow(
        db: Session,
        *,
        care_task: CareTask,
        protocol_input: dict[str, Any],
        protocol_output: dict[str, Any],
    ) -> AgentRun:
        """Persiste una corrida de protocolo respiratorio como traza operacional."""
        run_input = {
            "care_task_id": care_task.id,
            "title": care_task.title,
            "description": care_task.description,
            "specialty": care_task.specialty,
            "clinical_priority": care_task.clinical_priority,
            "protocol_input": protocol_input,
        }
        run = AgentRun(
            workflow_name="respiratory_protocol_v1",
            status="running",
            run_input=run_input,
            total_cost_usd=0.0,
            total_latency_ms=0,
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        started_at = time.perf_counter()
        AgentRunService._build_trace_step(
            db,
            run_id=run.id,
            step_order=1,
            step_name="respiratory_protocol_assessment",
            status="completed",
            step_input=protocol_input,
            step_output=protocol_output,
            decision="rules_protocol_output",
            fallback_used=False,
            error_message=None,
            step_cost_usd=0.0,
            step_latency_ms=0,
        )
        run.status = "completed"
        run.run_output = {"respiratory_protocol": protocol_output}
        run.total_cost_usd = 0.0
        run.total_latency_ms = round((time.perf_counter() - started_at) * 1000)
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def run_pediatric_humanization_workflow(
        db: Session,
        *,
        care_task: CareTask,
        protocol_input: dict[str, Any],
        protocol_output: dict[str, Any],
    ) -> AgentRun:
        """Persiste una corrida de humanizacion pediatrica como traza operacional."""
        run_input = {
            "care_task_id": care_task.id,
            "title": care_task.title,
            "description": care_task.description,
            "specialty": care_task.specialty,
            "clinical_priority": care_task.clinical_priority,
            "protocol_input": protocol_input,
        }
        run = AgentRun(
            workflow_name="pediatric_neuro_onco_support_v1",
            status="running",
            run_input=run_input,
            total_cost_usd=0.0,
            total_latency_ms=0,
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        started_at = time.perf_counter()
        AgentRunService._build_trace_step(
            db,
            run_id=run.id,
            step_order=1,
            step_name="humanization_operational_assessment",
            status="completed",
            step_input=protocol_input,
            step_output=protocol_output,
            decision="rules_humanization_output",
            fallback_used=False,
            error_message=None,
            step_cost_usd=0.0,
            step_latency_ms=0,
        )
        run.status = "completed"
        run.run_output = {"humanization_protocol": protocol_output}
        run.total_cost_usd = 0.0
        run.total_latency_ms = round((time.perf_counter() - started_at) * 1000)
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def run_advanced_screening_workflow(
        db: Session,
        *,
        care_task: CareTask,
        protocol_input: dict[str, Any],
        protocol_output: dict[str, Any],
    ) -> AgentRun:
        """Persiste una corrida de screening operativo avanzado."""
        run_input = {
            "care_task_id": care_task.id,
            "title": care_task.title,
            "description": care_task.description,
            "specialty": care_task.specialty,
            "clinical_priority": care_task.clinical_priority,
            "protocol_input": protocol_input,
        }
        run = AgentRun(
            workflow_name="advanced_screening_support_v1",
            status="running",
            run_input=run_input,
            total_cost_usd=0.0,
            total_latency_ms=0,
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        started_at = time.perf_counter()
        AgentRunService._build_trace_step(
            db,
            run_id=run.id,
            step_order=1,
            step_name="advanced_screening_assessment",
            status="completed",
            step_input=protocol_input,
            step_output=protocol_output,
            decision="rules_advanced_screening_output",
            fallback_used=False,
            error_message=None,
            step_cost_usd=0.0,
            step_latency_ms=0,
        )
        run.status = "completed"
        run.run_output = {"advanced_screening": protocol_output}
        run.total_cost_usd = 0.0
        run.total_latency_ms = round((time.perf_counter() - started_at) * 1000)
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def run_chest_xray_support_workflow(
        db: Session,
        *,
        care_task: CareTask,
        protocol_input: dict[str, Any],
        protocol_output: dict[str, Any],
    ) -> AgentRun:
        """Persiste una corrida de soporte radiografico de torax."""
        run_input = {
            "care_task_id": care_task.id,
            "title": care_task.title,
            "description": care_task.description,
            "specialty": care_task.specialty,
            "clinical_priority": care_task.clinical_priority,
            "protocol_input": protocol_input,
        }
        run = AgentRun(
            workflow_name="chest_xray_support_v1",
            status="running",
            run_input=run_input,
            total_cost_usd=0.0,
            total_latency_ms=0,
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        started_at = time.perf_counter()
        AgentRunService._build_trace_step(
            db,
            run_id=run.id,
            step_order=1,
            step_name="chest_xray_interpretation_assessment",
            status="completed",
            step_input=protocol_input,
            step_output=protocol_output,
            decision="rules_chest_xray_support_output",
            fallback_used=False,
            error_message=None,
            step_cost_usd=0.0,
            step_latency_ms=0,
        )
        run.status = "completed"
        run.run_output = {"chest_xray_support": protocol_output}
        run.total_cost_usd = 0.0
        run.total_latency_ms = round((time.perf_counter() - started_at) * 1000)
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def run_medicolegal_ops_workflow(
        db: Session,
        *,
        care_task: CareTask,
        protocol_input: dict[str, Any],
        protocol_output: dict[str, Any],
    ) -> AgentRun:
        """Persiste una corrida de soporte medico-legal operativo."""
        run_input = {
            "care_task_id": care_task.id,
            "title": care_task.title,
            "description": care_task.description,
            "specialty": care_task.specialty,
            "clinical_priority": care_task.clinical_priority,
            "protocol_input": protocol_input,
        }
        run = AgentRun(
            workflow_name="medicolegal_ops_support_v1",
            status="running",
            run_input=run_input,
            total_cost_usd=0.0,
            total_latency_ms=0,
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        started_at = time.perf_counter()
        AgentRunService._build_trace_step(
            db,
            run_id=run.id,
            step_order=1,
            step_name="medicolegal_operational_assessment",
            status="completed",
            step_input=protocol_input,
            step_output=protocol_output,
            decision="rules_medicolegal_output",
            fallback_used=False,
            error_message=None,
            step_cost_usd=0.0,
            step_latency_ms=0,
        )
        run.status = "completed"
        run.run_output = {"medicolegal_ops": protocol_output}
        run.total_cost_usd = 0.0
        run.total_latency_ms = round((time.perf_counter() - started_at) * 1000)
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def run_sepsis_protocol_workflow(
        db: Session,
        *,
        care_task: CareTask,
        protocol_input: dict[str, Any],
        protocol_output: dict[str, Any],
    ) -> AgentRun:
        """Persiste una corrida de soporte operativo de sepsis."""
        run_input = {
            "care_task_id": care_task.id,
            "title": care_task.title,
            "description": care_task.description,
            "specialty": care_task.specialty,
            "clinical_priority": care_task.clinical_priority,
            "protocol_input": protocol_input,
        }
        run = AgentRun(
            workflow_name="sepsis_protocol_support_v1",
            status="running",
            run_input=run_input,
            total_cost_usd=0.0,
            total_latency_ms=0,
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        started_at = time.perf_counter()
        AgentRunService._build_trace_step(
            db,
            run_id=run.id,
            step_order=1,
            step_name="sepsis_operational_assessment",
            status="completed",
            step_input=protocol_input,
            step_output=protocol_output,
            decision="rules_sepsis_protocol_output",
            fallback_used=False,
            error_message=None,
            step_cost_usd=0.0,
            step_latency_ms=0,
        )
        run.status = "completed"
        run.run_output = {"sepsis_protocol": protocol_output}
        run.total_cost_usd = 0.0
        run.total_latency_ms = round((time.perf_counter() - started_at) * 1000)
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def run_resuscitation_protocol_workflow(
        db: Session,
        *,
        care_task: CareTask,
        protocol_input: dict[str, Any],
        protocol_output: dict[str, Any],
    ) -> AgentRun:
        """Persiste una corrida de soporte operativo de reanimacion."""
        run_input = {
            "care_task_id": care_task.id,
            "title": care_task.title,
            "description": care_task.description,
            "specialty": care_task.specialty,
            "clinical_priority": care_task.clinical_priority,
            "protocol_input": protocol_input,
        }
        run = AgentRun(
            workflow_name="resuscitation_protocol_support_v1",
            status="running",
            run_input=run_input,
            total_cost_usd=0.0,
            total_latency_ms=0,
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        started_at = time.perf_counter()
        AgentRunService._build_trace_step(
            db,
            run_id=run.id,
            step_order=1,
            step_name="resuscitation_operational_assessment",
            status="completed",
            step_input=protocol_input,
            step_output=protocol_output,
            decision="rules_resuscitation_protocol_output",
            fallback_used=False,
            error_message=None,
            step_cost_usd=0.0,
            step_latency_ms=0,
        )
        run.status = "completed"
        run.run_output = {"resuscitation_protocol": protocol_output}
        run.total_cost_usd = 0.0
        run.total_latency_ms = round((time.perf_counter() - started_at) * 1000)
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def run_scasest_protocol_workflow(
        db: Session,
        *,
        care_task: CareTask,
        protocol_input: dict[str, Any],
        protocol_output: dict[str, Any],
    ) -> AgentRun:
        """Persiste una corrida de soporte operativo para SCASEST."""
        run_input = {
            "care_task_id": care_task.id,
            "title": care_task.title,
            "description": care_task.description,
            "specialty": care_task.specialty,
            "clinical_priority": care_task.clinical_priority,
            "protocol_input": protocol_input,
        }
        run = AgentRun(
            workflow_name="scasest_protocol_support_v1",
            status="running",
            run_input=run_input,
            total_cost_usd=0.0,
            total_latency_ms=0,
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        started_at = time.perf_counter()
        AgentRunService._build_trace_step(
            db,
            run_id=run.id,
            step_order=1,
            step_name="scasest_operational_assessment",
            status="completed",
            step_input=protocol_input,
            step_output=protocol_output,
            decision="rules_scasest_protocol_output",
            fallback_used=False,
            error_message=None,
            step_cost_usd=0.0,
            step_latency_ms=0,
        )
        run.status = "completed"
        run.run_output = {"scasest_protocol": protocol_output}
        run.total_cost_usd = 0.0
        run.total_latency_ms = round((time.perf_counter() - started_at) * 1000)
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def run_cardio_risk_support_workflow(
        db: Session,
        *,
        care_task: CareTask,
        protocol_input: dict[str, Any],
        protocol_output: dict[str, Any],
    ) -> AgentRun:
        """Persiste una corrida de soporte operativo de riesgo cardiovascular."""
        run_input = {
            "care_task_id": care_task.id,
            "title": care_task.title,
            "description": care_task.description,
            "specialty": care_task.specialty,
            "clinical_priority": care_task.clinical_priority,
            "protocol_input": protocol_input,
        }
        run = AgentRun(
            workflow_name="cardio_risk_support_v1",
            status="running",
            run_input=run_input,
            total_cost_usd=0.0,
            total_latency_ms=0,
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        started_at = time.perf_counter()
        AgentRunService._build_trace_step(
            db,
            run_id=run.id,
            step_order=1,
            step_name="cardio_risk_operational_assessment",
            status="completed",
            step_input=protocol_input,
            step_output=protocol_output,
            decision="rules_cardio_risk_output",
            fallback_used=False,
            error_message=None,
            step_cost_usd=0.0,
            step_latency_ms=0,
        )
        run.status = "completed"
        run.run_output = {"cardio_risk_support": protocol_output}
        run.total_cost_usd = 0.0
        run.total_latency_ms = round((time.perf_counter() - started_at) * 1000)
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def run_pityriasis_differential_workflow(
        db: Session,
        *,
        care_task: CareTask,
        protocol_input: dict[str, Any],
        protocol_output: dict[str, Any],
    ) -> AgentRun:
        """Persiste una corrida de soporte diferencial para pitiriasis."""
        run_input = {
            "care_task_id": care_task.id,
            "title": care_task.title,
            "description": care_task.description,
            "specialty": care_task.specialty,
            "clinical_priority": care_task.clinical_priority,
            "protocol_input": protocol_input,
        }
        run = AgentRun(
            workflow_name="pityriasis_differential_support_v1",
            status="running",
            run_input=run_input,
            total_cost_usd=0.0,
            total_latency_ms=0,
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        started_at = time.perf_counter()
        AgentRunService._build_trace_step(
            db,
            run_id=run.id,
            step_order=1,
            step_name="pityriasis_differential_assessment",
            status="completed",
            step_input=protocol_input,
            step_output=protocol_output,
            decision="rules_pityriasis_differential_output",
            fallback_used=False,
            error_message=None,
            step_cost_usd=0.0,
            step_latency_ms=0,
        )
        run.status = "completed"
        run.run_output = {"pityriasis_differential": protocol_output}
        run.total_cost_usd = 0.0
        run.total_latency_ms = round((time.perf_counter() - started_at) * 1000)
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def run_acne_rosacea_differential_workflow(
        db: Session,
        *,
        care_task: CareTask,
        protocol_input: dict[str, Any],
        protocol_output: dict[str, Any],
    ) -> AgentRun:
        """Persiste una corrida de soporte diferencial acne/rosacea."""
        run_input = {
            "care_task_id": care_task.id,
            "title": care_task.title,
            "description": care_task.description,
            "specialty": care_task.specialty,
            "clinical_priority": care_task.clinical_priority,
            "protocol_input": protocol_input,
        }
        run = AgentRun(
            workflow_name="acne_rosacea_differential_support_v1",
            status="running",
            run_input=run_input,
            total_cost_usd=0.0,
            total_latency_ms=0,
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        started_at = time.perf_counter()
        AgentRunService._build_trace_step(
            db,
            run_id=run.id,
            step_order=1,
            step_name="acne_rosacea_differential_assessment",
            status="completed",
            step_input=protocol_input,
            step_output=protocol_output,
            decision="rules_acne_rosacea_differential_output",
            fallback_used=False,
            error_message=None,
            step_cost_usd=0.0,
            step_latency_ms=0,
        )
        run.status = "completed"
        run.run_output = {"acne_rosacea_differential": protocol_output}
        run.total_cost_usd = 0.0
        run.total_latency_ms = round((time.perf_counter() - started_at) * 1000)
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def run_trauma_support_workflow(
        db: Session,
        *,
        care_task: CareTask,
        protocol_input: dict[str, Any],
        protocol_output: dict[str, Any],
    ) -> AgentRun:
        """Persiste una corrida de soporte operativo de trauma."""
        run_input = {
            "care_task_id": care_task.id,
            "title": care_task.title,
            "description": care_task.description,
            "specialty": care_task.specialty,
            "clinical_priority": care_task.clinical_priority,
            "protocol_input": protocol_input,
        }
        run = AgentRun(
            workflow_name="trauma_support_v1",
            status="running",
            run_input=run_input,
            total_cost_usd=0.0,
            total_latency_ms=0,
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        started_at = time.perf_counter()
        AgentRunService._build_trace_step(
            db,
            run_id=run.id,
            step_order=1,
            step_name="trauma_operational_assessment",
            status="completed",
            step_input=protocol_input,
            step_output=protocol_output,
            decision="rules_trauma_support_output",
            fallback_used=False,
            error_message=None,
            step_cost_usd=0.0,
            step_latency_ms=0,
        )
        run.status = "completed"
        run.run_output = {"trauma_support": protocol_output}
        run.total_cost_usd = 0.0
        run.total_latency_ms = round((time.perf_counter() - started_at) * 1000)
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def run_critical_ops_workflow(
        db: Session,
        *,
        care_task: CareTask,
        protocol_input: dict[str, Any],
        protocol_output: dict[str, Any],
    ) -> AgentRun:
        """Persiste una corrida de soporte operativo critico transversal."""
        run_input = {
            "care_task_id": care_task.id,
            "title": care_task.title,
            "description": care_task.description,
            "specialty": care_task.specialty,
            "clinical_priority": care_task.clinical_priority,
            "protocol_input": protocol_input,
        }
        run = AgentRun(
            workflow_name="critical_ops_support_v1",
            status="running",
            run_input=run_input,
            total_cost_usd=0.0,
            total_latency_ms=0,
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        started_at = time.perf_counter()
        AgentRunService._build_trace_step(
            db,
            run_id=run.id,
            step_order=1,
            step_name="critical_ops_operational_assessment",
            status="completed",
            step_input=protocol_input,
            step_output=protocol_output,
            decision="rules_critical_ops_output",
            fallback_used=False,
            error_message=None,
            step_cost_usd=0.0,
            step_latency_ms=0,
        )
        run.status = "completed"
        run.run_output = {"critical_ops": protocol_output}
        run.total_cost_usd = 0.0
        run.total_latency_ms = round((time.perf_counter() - started_at) * 1000)
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def run_neurology_support_workflow(
        db: Session,
        *,
        care_task: CareTask,
        protocol_input: dict[str, Any],
        protocol_output: dict[str, Any],
    ) -> AgentRun:
        """Persiste una corrida de soporte operativo neurologico."""
        run_input = {
            "care_task_id": care_task.id,
            "title": care_task.title,
            "description": care_task.description,
            "specialty": care_task.specialty,
            "clinical_priority": care_task.clinical_priority,
            "protocol_input": protocol_input,
        }
        run = AgentRun(
            workflow_name="neurology_support_v1",
            status="running",
            run_input=run_input,
            total_cost_usd=0.0,
            total_latency_ms=0,
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        started_at = time.perf_counter()
        AgentRunService._build_trace_step(
            db,
            run_id=run.id,
            step_order=1,
            step_name="neurology_operational_assessment",
            status="completed",
            step_input=protocol_input,
            step_output=protocol_output,
            decision="rules_neurology_support_output",
            fallback_used=False,
            error_message=None,
            step_cost_usd=0.0,
            step_latency_ms=0,
        )
        run.status = "completed"
        run.run_output = {"neurology_support": protocol_output}
        run.total_cost_usd = 0.0
        run.total_latency_ms = round((time.perf_counter() - started_at) * 1000)
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def run_gastro_hepato_support_workflow(
        db: Session,
        *,
        care_task: CareTask,
        protocol_input: dict[str, Any],
        protocol_output: dict[str, Any],
    ) -> AgentRun:
        """Persiste una corrida de soporte operativo gastro-hepato."""
        run_input = {
            "care_task_id": care_task.id,
            "title": care_task.title,
            "description": care_task.description,
            "specialty": care_task.specialty,
            "clinical_priority": care_task.clinical_priority,
            "protocol_input": protocol_input,
        }
        run = AgentRun(
            workflow_name="gastro_hepato_support_v1",
            status="running",
            run_input=run_input,
            total_cost_usd=0.0,
            total_latency_ms=0,
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        started_at = time.perf_counter()
        AgentRunService._build_trace_step(
            db,
            run_id=run.id,
            step_order=1,
            step_name="gastro_hepato_operational_assessment",
            status="completed",
            step_input=protocol_input,
            step_output=protocol_output,
            decision="rules_gastro_hepato_support_output",
            fallback_used=False,
            error_message=None,
            step_cost_usd=0.0,
            step_latency_ms=0,
        )
        run.status = "completed"
        run.run_output = {"gastro_hepato_support": protocol_output}
        run.total_cost_usd = 0.0
        run.total_latency_ms = round((time.perf_counter() - started_at) * 1000)
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def run_rheum_immuno_support_workflow(
        db: Session,
        *,
        care_task: CareTask,
        protocol_input: dict[str, Any],
        protocol_output: dict[str, Any],
    ) -> AgentRun:
        """Persiste una corrida de soporte operativo reuma-inmuno."""
        run_input = {
            "care_task_id": care_task.id,
            "title": care_task.title,
            "description": care_task.description,
            "specialty": care_task.specialty,
            "clinical_priority": care_task.clinical_priority,
            "protocol_input": protocol_input,
        }
        run = AgentRun(
            workflow_name="rheum_immuno_support_v1",
            status="running",
            run_input=run_input,
            total_cost_usd=0.0,
            total_latency_ms=0,
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        started_at = time.perf_counter()
        AgentRunService._build_trace_step(
            db,
            run_id=run.id,
            step_order=1,
            step_name="rheum_immuno_operational_assessment",
            status="completed",
            step_input=protocol_input,
            step_output=protocol_output,
            decision="rules_rheum_immuno_support_output",
            fallback_used=False,
            error_message=None,
            step_cost_usd=0.0,
            step_latency_ms=0,
        )
        run.status = "completed"
        run.run_output = {"rheum_immuno_support": protocol_output}
        run.total_cost_usd = 0.0
        run.total_latency_ms = round((time.perf_counter() - started_at) * 1000)
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def run_psychiatry_support_workflow(
        db: Session,
        *,
        care_task: CareTask,
        protocol_input: dict[str, Any],
        protocol_output: dict[str, Any],
    ) -> AgentRun:
        """Persiste una corrida de soporte operativo de psiquiatria."""
        run_input = {
            "care_task_id": care_task.id,
            "title": care_task.title,
            "description": care_task.description,
            "specialty": care_task.specialty,
            "clinical_priority": care_task.clinical_priority,
            "protocol_input": protocol_input,
        }
        run = AgentRun(
            workflow_name="psychiatry_support_v1",
            status="running",
            run_input=run_input,
            total_cost_usd=0.0,
            total_latency_ms=0,
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        started_at = time.perf_counter()
        AgentRunService._build_trace_step(
            db,
            run_id=run.id,
            step_order=1,
            step_name="psychiatry_operational_assessment",
            status="completed",
            step_input=protocol_input,
            step_output=protocol_output,
            decision="rules_psychiatry_support_output",
            fallback_used=False,
            error_message=None,
            step_cost_usd=0.0,
            step_latency_ms=0,
        )
        run.status = "completed"
        run.run_output = {"psychiatry_support": protocol_output}
        run.total_cost_usd = 0.0
        run.total_latency_ms = round((time.perf_counter() - started_at) * 1000)
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def run_hematology_support_workflow(
        db: Session,
        *,
        care_task: CareTask,
        protocol_input: dict[str, Any],
        protocol_output: dict[str, Any],
    ) -> AgentRun:
        """Persiste una corrida de soporte operativo de hematologia."""
        run_input = {
            "care_task_id": care_task.id,
            "title": care_task.title,
            "description": care_task.description,
            "specialty": care_task.specialty,
            "clinical_priority": care_task.clinical_priority,
            "protocol_input": protocol_input,
        }
        run = AgentRun(
            workflow_name="hematology_support_v1",
            status="running",
            run_input=run_input,
            total_cost_usd=0.0,
            total_latency_ms=0,
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        started_at = time.perf_counter()
        AgentRunService._build_trace_step(
            db,
            run_id=run.id,
            step_order=1,
            step_name="hematology_operational_assessment",
            status="completed",
            step_input=protocol_input,
            step_output=protocol_output,
            decision="rules_hematology_support_output",
            fallback_used=False,
            error_message=None,
            step_cost_usd=0.0,
            step_latency_ms=0,
        )
        run.status = "completed"
        run.run_output = {"hematology_support": protocol_output}
        run.total_cost_usd = 0.0
        run.total_latency_ms = round((time.perf_counter() - started_at) * 1000)
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def run_endocrinology_support_workflow(
        db: Session,
        *,
        care_task: CareTask,
        protocol_input: dict[str, Any],
        protocol_output: dict[str, Any],
    ) -> AgentRun:
        """Persiste una corrida de soporte operativo de endocrinologia."""
        run_input = {
            "care_task_id": care_task.id,
            "title": care_task.title,
            "description": care_task.description,
            "specialty": care_task.specialty,
            "clinical_priority": care_task.clinical_priority,
            "protocol_input": protocol_input,
        }
        run = AgentRun(
            workflow_name="endocrinology_support_v1",
            status="running",
            run_input=run_input,
            total_cost_usd=0.0,
            total_latency_ms=0,
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        started_at = time.perf_counter()
        AgentRunService._build_trace_step(
            db,
            run_id=run.id,
            step_order=1,
            step_name="endocrinology_operational_assessment",
            status="completed",
            step_input=protocol_input,
            step_output=protocol_output,
            decision="rules_endocrinology_support_output",
            fallback_used=False,
            error_message=None,
            step_cost_usd=0.0,
            step_latency_ms=0,
        )
        run.status = "completed"
        run.run_output = {"endocrinology_support": protocol_output}
        run.total_cost_usd = 0.0
        run.total_latency_ms = round((time.perf_counter() - started_at) * 1000)
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def run_nephrology_support_workflow(
        db: Session,
        *,
        care_task: CareTask,
        protocol_input: dict[str, Any],
        protocol_output: dict[str, Any],
    ) -> AgentRun:
        """Persiste una corrida de soporte operativo de nefrologia."""
        run_input = {
            "care_task_id": care_task.id,
            "title": care_task.title,
            "description": care_task.description,
            "specialty": care_task.specialty,
            "clinical_priority": care_task.clinical_priority,
            "protocol_input": protocol_input,
        }
        run = AgentRun(
            workflow_name="nephrology_support_v1",
            status="running",
            run_input=run_input,
            total_cost_usd=0.0,
            total_latency_ms=0,
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        started_at = time.perf_counter()
        AgentRunService._build_trace_step(
            db,
            run_id=run.id,
            step_order=1,
            step_name="nephrology_operational_assessment",
            status="completed",
            step_input=protocol_input,
            step_output=protocol_output,
            decision="rules_nephrology_support_output",
            fallback_used=False,
            error_message=None,
            step_cost_usd=0.0,
            step_latency_ms=0,
        )
        run.status = "completed"
        run.run_output = {"nephrology_support": protocol_output}
        run.total_cost_usd = 0.0
        run.total_latency_ms = round((time.perf_counter() - started_at) * 1000)
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def run_pneumology_support_workflow(
        db: Session,
        *,
        care_task: CareTask,
        protocol_input: dict[str, Any],
        protocol_output: dict[str, Any],
    ) -> AgentRun:
        """Persiste una corrida de soporte operativo de neumologia."""
        run_input = {
            "care_task_id": care_task.id,
            "title": care_task.title,
            "description": care_task.description,
            "specialty": care_task.specialty,
            "clinical_priority": care_task.clinical_priority,
            "protocol_input": protocol_input,
        }
        run = AgentRun(
            workflow_name="pneumology_support_v1",
            status="running",
            run_input=run_input,
            total_cost_usd=0.0,
            total_latency_ms=0,
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        started_at = time.perf_counter()
        AgentRunService._build_trace_step(
            db,
            run_id=run.id,
            step_order=1,
            step_name="pneumology_operational_assessment",
            status="completed",
            step_input=protocol_input,
            step_output=protocol_output,
            decision="rules_pneumology_support_output",
            fallback_used=False,
            error_message=None,
            step_cost_usd=0.0,
            step_latency_ms=0,
        )
        run.status = "completed"
        run.run_output = {"pneumology_support": protocol_output}
        run.total_cost_usd = 0.0
        run.total_latency_ms = round((time.perf_counter() - started_at) * 1000)
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def run_geriatrics_support_workflow(
        db: Session,
        *,
        care_task: CareTask,
        protocol_input: dict[str, Any],
        protocol_output: dict[str, Any],
    ) -> AgentRun:
        """Persiste una corrida de soporte operativo de geriatria."""
        run_input = {
            "care_task_id": care_task.id,
            "title": care_task.title,
            "description": care_task.description,
            "specialty": care_task.specialty,
            "clinical_priority": care_task.clinical_priority,
            "protocol_input": protocol_input,
        }
        run = AgentRun(
            workflow_name="geriatrics_support_v1",
            status="running",
            run_input=run_input,
            total_cost_usd=0.0,
            total_latency_ms=0,
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        started_at = time.perf_counter()
        AgentRunService._build_trace_step(
            db,
            run_id=run.id,
            step_order=1,
            step_name="geriatrics_operational_assessment",
            status="completed",
            step_input=protocol_input,
            step_output=protocol_output,
            decision="rules_geriatrics_support_output",
            fallback_used=False,
            error_message=None,
            step_cost_usd=0.0,
            step_latency_ms=0,
        )
        run.status = "completed"
        run.run_output = {"geriatrics_support": protocol_output}
        run.total_cost_usd = 0.0
        run.total_latency_ms = round((time.perf_counter() - started_at) * 1000)
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def run_oncology_support_workflow(
        db: Session,
        *,
        care_task: CareTask,
        protocol_input: dict[str, Any],
        protocol_output: dict[str, Any],
    ) -> AgentRun:
        """Persiste una corrida de soporte operativo de oncologia."""
        run_input = {
            "care_task_id": care_task.id,
            "title": care_task.title,
            "description": care_task.description,
            "specialty": care_task.specialty,
            "clinical_priority": care_task.clinical_priority,
            "protocol_input": protocol_input,
        }
        run = AgentRun(
            workflow_name="oncology_support_v1",
            status="running",
            run_input=run_input,
            total_cost_usd=0.0,
            total_latency_ms=0,
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        started_at = time.perf_counter()
        AgentRunService._build_trace_step(
            db,
            run_id=run.id,
            step_order=1,
            step_name="oncology_operational_assessment",
            status="completed",
            step_input=protocol_input,
            step_output=protocol_output,
            decision="rules_oncology_support_output",
            fallback_used=False,
            error_message=None,
            step_cost_usd=0.0,
            step_latency_ms=0,
        )
        run.status = "completed"
        run.run_output = {"oncology_support": protocol_output}
        run.total_cost_usd = 0.0
        run.total_latency_ms = round((time.perf_counter() - started_at) * 1000)
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def run_anesthesiology_support_workflow(
        db: Session,
        *,
        care_task: CareTask,
        protocol_input: dict[str, Any],
        protocol_output: dict[str, Any],
    ) -> AgentRun:
        """Persiste una corrida de soporte operativo de anestesiologia/reanimacion."""
        run_input = {
            "care_task_id": care_task.id,
            "title": care_task.title,
            "description": care_task.description,
            "specialty": care_task.specialty,
            "clinical_priority": care_task.clinical_priority,
            "protocol_input": protocol_input,
        }
        run = AgentRun(
            workflow_name="anesthesiology_support_v1",
            status="running",
            run_input=run_input,
            total_cost_usd=0.0,
            total_latency_ms=0,
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        started_at = time.perf_counter()
        AgentRunService._build_trace_step(
            db,
            run_id=run.id,
            step_order=1,
            step_name="anesthesiology_operational_assessment",
            status="completed",
            step_input=protocol_input,
            step_output=protocol_output,
            decision="rules_anesthesiology_support_output",
            fallback_used=False,
            error_message=None,
            step_cost_usd=0.0,
            step_latency_ms=0,
        )
        run.status = "completed"
        run.run_output = {"anesthesiology_support": protocol_output}
        run.total_cost_usd = 0.0
        run.total_latency_ms = round((time.perf_counter() - started_at) * 1000)
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def run_palliative_support_workflow(
        db: Session,
        *,
        care_task: CareTask,
        protocol_input: dict[str, Any],
        protocol_output: dict[str, Any],
    ) -> AgentRun:
        """Persiste una corrida de soporte operativo de cuidados paliativos."""
        run_input = {
            "care_task_id": care_task.id,
            "title": care_task.title,
            "description": care_task.description,
            "specialty": care_task.specialty,
            "clinical_priority": care_task.clinical_priority,
            "protocol_input": protocol_input,
        }
        run = AgentRun(
            workflow_name="palliative_support_v1",
            status="running",
            run_input=run_input,
            total_cost_usd=0.0,
            total_latency_ms=0,
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        started_at = time.perf_counter()
        AgentRunService._build_trace_step(
            db,
            run_id=run.id,
            step_order=1,
            step_name="palliative_operational_assessment",
            status="completed",
            step_input=protocol_input,
            step_output=protocol_output,
            decision="rules_palliative_support_output",
            fallback_used=False,
            error_message=None,
            step_cost_usd=0.0,
            step_latency_ms=0,
        )
        run.status = "completed"
        run.run_output = {"palliative_support": protocol_output}
        run.total_cost_usd = 0.0
        run.total_latency_ms = round((time.perf_counter() - started_at) * 1000)
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def run_urology_support_workflow(
        db: Session,
        *,
        care_task: CareTask,
        protocol_input: dict[str, Any],
        protocol_output: dict[str, Any],
    ) -> AgentRun:
        """Persiste una corrida de soporte operativo de urologia."""
        run_input = {
            "care_task_id": care_task.id,
            "title": care_task.title,
            "description": care_task.description,
            "specialty": care_task.specialty,
            "clinical_priority": care_task.clinical_priority,
            "protocol_input": protocol_input,
        }
        run = AgentRun(
            workflow_name="urology_support_v1",
            status="running",
            run_input=run_input,
            total_cost_usd=0.0,
            total_latency_ms=0,
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        started_at = time.perf_counter()
        AgentRunService._build_trace_step(
            db,
            run_id=run.id,
            step_order=1,
            step_name="urology_operational_assessment",
            status="completed",
            step_input=protocol_input,
            step_output=protocol_output,
            decision="rules_urology_support_output",
            fallback_used=False,
            error_message=None,
            step_cost_usd=0.0,
            step_latency_ms=0,
        )
        run.status = "completed"
        run.run_output = {"urology_support": protocol_output}
        run.total_cost_usd = 0.0
        run.total_latency_ms = round((time.perf_counter() - started_at) * 1000)
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def run_ophthalmology_support_workflow(
        db: Session,
        *,
        care_task: CareTask,
        protocol_input: dict[str, Any],
        protocol_output: dict[str, Any],
    ) -> AgentRun:
        """Persiste una corrida de soporte operativo de oftalmologia."""
        run_input = {
            "care_task_id": care_task.id,
            "title": care_task.title,
            "description": care_task.description,
            "specialty": care_task.specialty,
            "clinical_priority": care_task.clinical_priority,
            "protocol_input": protocol_input,
        }
        run = AgentRun(
            workflow_name="ophthalmology_support_v1",
            status="running",
            run_input=run_input,
            total_cost_usd=0.0,
            total_latency_ms=0,
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        started_at = time.perf_counter()
        AgentRunService._build_trace_step(
            db,
            run_id=run.id,
            step_order=1,
            step_name="ophthalmology_operational_assessment",
            status="completed",
            step_input=protocol_input,
            step_output=protocol_output,
            decision="rules_ophthalmology_support_output",
            fallback_used=False,
            error_message=None,
            step_cost_usd=0.0,
            step_latency_ms=0,
        )
        run.status = "completed"
        run.run_output = {"ophthalmology_support": protocol_output}
        run.total_cost_usd = 0.0
        run.total_latency_ms = round((time.perf_counter() - started_at) * 1000)
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def run_immunology_support_workflow(
        db: Session,
        *,
        care_task: CareTask,
        protocol_input: dict[str, Any],
        protocol_output: dict[str, Any],
    ) -> AgentRun:
        """Persiste una corrida de soporte operativo de inmunologia."""
        run_input = {
            "care_task_id": care_task.id,
            "title": care_task.title,
            "description": care_task.description,
            "specialty": care_task.specialty,
            "clinical_priority": care_task.clinical_priority,
            "protocol_input": protocol_input,
        }
        run = AgentRun(
            workflow_name="immunology_support_v1",
            status="running",
            run_input=run_input,
            total_cost_usd=0.0,
            total_latency_ms=0,
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        started_at = time.perf_counter()
        AgentRunService._build_trace_step(
            db,
            run_id=run.id,
            step_order=1,
            step_name="immunology_operational_assessment",
            status="completed",
            step_input=protocol_input,
            step_output=protocol_output,
            decision="rules_immunology_support_output",
            fallback_used=False,
            error_message=None,
            step_cost_usd=0.0,
            step_latency_ms=0,
        )
        run.status = "completed"
        run.run_output = {"immunology_support": protocol_output}
        run.total_cost_usd = 0.0
        run.total_latency_ms = round((time.perf_counter() - started_at) * 1000)
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def run_genetic_recurrence_support_workflow(
        db: Session,
        *,
        care_task: CareTask,
        protocol_input: dict[str, Any],
        protocol_output: dict[str, Any],
    ) -> AgentRun:
        """Persiste una corrida de soporte operativo de recurrencia genetica."""
        run_input = {
            "care_task_id": care_task.id,
            "title": care_task.title,
            "description": care_task.description,
            "specialty": care_task.specialty,
            "clinical_priority": care_task.clinical_priority,
            "protocol_input": protocol_input,
        }
        run = AgentRun(
            workflow_name="genetic_recurrence_support_v1",
            status="running",
            run_input=run_input,
            total_cost_usd=0.0,
            total_latency_ms=0,
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        started_at = time.perf_counter()
        AgentRunService._build_trace_step(
            db,
            run_id=run.id,
            step_order=1,
            step_name="genetic_recurrence_operational_assessment",
            status="completed",
            step_input=protocol_input,
            step_output=protocol_output,
            decision="rules_genetic_recurrence_support_output",
            fallback_used=False,
            error_message=None,
            step_cost_usd=0.0,
            step_latency_ms=0,
        )
        run.status = "completed"
        run.run_output = {"genetic_recurrence_support": protocol_output}
        run.total_cost_usd = 0.0
        run.total_latency_ms = round((time.perf_counter() - started_at) * 1000)
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def run_gynecology_obstetrics_support_workflow(
        db: Session,
        *,
        care_task: CareTask,
        protocol_input: dict[str, Any],
        protocol_output: dict[str, Any],
    ) -> AgentRun:
        """Persiste una corrida de soporte operativo de ginecologia/obstetricia."""
        run_input = {
            "care_task_id": care_task.id,
            "title": care_task.title,
            "description": care_task.description,
            "specialty": care_task.specialty,
            "clinical_priority": care_task.clinical_priority,
            "protocol_input": protocol_input,
        }
        run = AgentRun(
            workflow_name="gynecology_obstetrics_support_v1",
            status="running",
            run_input=run_input,
            total_cost_usd=0.0,
            total_latency_ms=0,
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        started_at = time.perf_counter()
        AgentRunService._build_trace_step(
            db,
            run_id=run.id,
            step_order=1,
            step_name="gynecology_obstetrics_operational_assessment",
            status="completed",
            step_input=protocol_input,
            step_output=protocol_output,
            decision="rules_gynecology_obstetrics_support_output",
            fallback_used=False,
            error_message=None,
            step_cost_usd=0.0,
            step_latency_ms=0,
        )
        run.status = "completed"
        run.run_output = {"gynecology_obstetrics_support": protocol_output}
        run.total_cost_usd = 0.0
        run.total_latency_ms = round((time.perf_counter() - started_at) * 1000)
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def run_pediatrics_neonatology_support_workflow(
        db: Session,
        *,
        care_task: CareTask,
        protocol_input: dict[str, Any],
        protocol_output: dict[str, Any],
    ) -> AgentRun:
        """Persiste una corrida de soporte operativo de pediatria/neonatologia."""
        run_input = {
            "care_task_id": care_task.id,
            "title": care_task.title,
            "description": care_task.description,
            "specialty": care_task.specialty,
            "clinical_priority": care_task.clinical_priority,
            "protocol_input": protocol_input,
        }
        run = AgentRun(
            workflow_name="pediatrics_neonatology_support_v1",
            status="running",
            run_input=run_input,
            total_cost_usd=0.0,
            total_latency_ms=0,
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        started_at = time.perf_counter()
        AgentRunService._build_trace_step(
            db,
            run_id=run.id,
            step_order=1,
            step_name="pediatrics_neonatology_operational_assessment",
            status="completed",
            step_input=protocol_input,
            step_output=protocol_output,
            decision="rules_pediatrics_neonatology_support_output",
            fallback_used=False,
            error_message=None,
            step_cost_usd=0.0,
            step_latency_ms=0,
        )
        run.status = "completed"
        run.run_output = {"pediatrics_neonatology_support": protocol_output}
        run.total_cost_usd = 0.0
        run.total_latency_ms = round((time.perf_counter() - started_at) * 1000)
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def run_epidemiology_support_workflow(
        db: Session,
        *,
        care_task: CareTask,
        protocol_input: dict[str, Any],
        protocol_output: dict[str, Any],
    ) -> AgentRun:
        """Persiste una corrida de soporte operativo de epidemiologia clinica."""
        run_input = {
            "care_task_id": care_task.id,
            "title": care_task.title,
            "description": care_task.description,
            "specialty": care_task.specialty,
            "clinical_priority": care_task.clinical_priority,
            "protocol_input": protocol_input,
        }
        run = AgentRun(
            workflow_name="epidemiology_support_v1",
            status="running",
            run_input=run_input,
            total_cost_usd=0.0,
            total_latency_ms=0,
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        started_at = time.perf_counter()
        AgentRunService._build_trace_step(
            db,
            run_id=run.id,
            step_order=1,
            step_name="epidemiology_operational_assessment",
            status="completed",
            step_input=protocol_input,
            step_output=protocol_output,
            decision="rules_epidemiology_support_output",
            fallback_used=False,
            error_message=None,
            step_cost_usd=0.0,
            step_latency_ms=0,
        )
        run.status = "completed"
        run.run_output = {"epidemiology_support": protocol_output}
        run.total_cost_usd = 0.0
        run.total_latency_ms = round((time.perf_counter() - started_at) * 1000)
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def run_anisakis_support_workflow(
        db: Session,
        *,
        care_task: CareTask,
        protocol_input: dict[str, Any],
        protocol_output: dict[str, Any],
    ) -> AgentRun:
        """Persiste una corrida de soporte operativo anisakis."""
        run_input = {
            "care_task_id": care_task.id,
            "title": care_task.title,
            "description": care_task.description,
            "specialty": care_task.specialty,
            "clinical_priority": care_task.clinical_priority,
            "protocol_input": protocol_input,
        }
        run = AgentRun(
            workflow_name="anisakis_support_v1",
            status="running",
            run_input=run_input,
            total_cost_usd=0.0,
            total_latency_ms=0,
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        started_at = time.perf_counter()
        AgentRunService._build_trace_step(
            db,
            run_id=run.id,
            step_order=1,
            step_name="anisakis_operational_assessment",
            status="completed",
            step_input=protocol_input,
            step_output=protocol_output,
            decision="rules_anisakis_support_output",
            fallback_used=False,
            error_message=None,
            step_cost_usd=0.0,
            step_latency_ms=0,
        )
        run.status = "completed"
        run.run_output = {"anisakis_support": protocol_output}
        run.total_cost_usd = 0.0
        run.total_latency_ms = round((time.perf_counter() - started_at) * 1000)
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def run_care_task_clinical_chat_workflow(
        db: Session,
        *,
        care_task: CareTask,
        chat_input: dict[str, Any],
        chat_output: dict[str, Any],
    ) -> AgentRun:
        """Persiste una corrida de chat clinico-operativo para un CareTask."""
        run_input = {
            "care_task_id": care_task.id,
            "title": care_task.title,
            "description": care_task.description,
            "specialty": care_task.specialty,
            "clinical_priority": care_task.clinical_priority,
            "chat_input": chat_input,
        }
        run = AgentRun(
            workflow_name="care_task_clinical_chat_v1",
            status="running",
            run_input=run_input,
            total_cost_usd=0.0,
            total_latency_ms=0,
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        started_at = time.perf_counter()
        AgentRunService._build_trace_step(
            db,
            run_id=run.id,
            step_order=1,
            step_name="clinical_chat_assessment",
            status="completed",
            step_input=chat_input,
            step_output=chat_output,
            decision="rules_chat_memory_output",
            fallback_used=False,
            error_message=None,
            step_cost_usd=0.0,
            step_latency_ms=0,
        )
        run.status = "completed"
        run.run_output = {"clinical_chat": chat_output}
        run.total_cost_usd = 0.0
        run.total_latency_ms = round((time.perf_counter() - started_at) * 1000)
        db.add(run)
        db.commit()
        db.refresh(run)
        return run
