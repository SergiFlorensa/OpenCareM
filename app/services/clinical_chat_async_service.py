"""
Servicio asincrono de chat clinico para ejecucion en segundo plano.

Objetivo: evitar bloquear el request HTTP cuando el LLM local tarda mas de lo
esperado en CPU. El endpoint asincrono encola la solicitud y un worker local
la procesa con persistencia normal de mensajes.
"""
from __future__ import annotations

import queue
import threading
from datetime import datetime, timedelta, timezone
from typing import Any, Literal
from uuid import uuid4

from app.core.database import SessionLocal
from app.models.care_task import CareTask
from app.models.user import User
from app.schemas.clinical_chat import CareTaskClinicalChatMessageRequest
from app.services.clinical_chat_service import ClinicalChatService

AsyncJobStatus = Literal["queued", "running", "completed", "failed"]


class ClinicalChatAsyncService:
    """Cola local en memoria para procesamiento asincrono de chat clinico."""

    _jobs: dict[str, dict[str, Any]] = {}
    _jobs_lock = threading.Lock()
    _job_queue: queue.Queue[str] = queue.Queue()
    _worker_thread: threading.Thread | None = None
    _max_jobs: int = 500
    _ttl_minutes: int = 120

    @classmethod
    def enqueue_job(
        cls,
        *,
        care_task_id: int,
        payload: CareTaskClinicalChatMessageRequest,
        authenticated_user: User | None,
    ) -> dict[str, Any]:
        """Registra un trabajo y lo encola para ejecucion en segundo plano."""
        session_id = cls._safe_session_id(payload.session_id)
        job_id = f"chatjob-{uuid4().hex[:20]}"
        now = datetime.now(timezone.utc)
        job_record: dict[str, Any] = {
            "job_id": job_id,
            "care_task_id": care_task_id,
            "session_id": session_id,
            "payload": payload.model_dump(),
            "user_id": authenticated_user.id if authenticated_user is not None else None,
            "status": "queued",
            "created_at": now,
            "updated_at": now,
            "message_id": None,
            "agent_run_id": None,
            "workflow_name": None,
            "response_mode": None,
            "tool_mode": None,
            "quality_status": None,
            "llm_used": None,
            "error": None,
        }
        job_record["payload"]["session_id"] = session_id

        with cls._jobs_lock:
            cls._cleanup_jobs_locked(now=now)
            cls._jobs[job_id] = job_record

        cls._ensure_worker_started()
        cls._job_queue.put(job_id)
        return cls._public_job_view(job_record)

    @classmethod
    def get_job_status(cls, *, job_id: str) -> dict[str, Any] | None:
        """Devuelve estado actual del trabajo o None si no existe."""
        with cls._jobs_lock:
            record = cls._jobs.get(job_id)
            if record is None:
                return None
            return cls._public_job_view(record)

    @classmethod
    def _ensure_worker_started(cls) -> None:
        if cls._worker_thread and cls._worker_thread.is_alive():
            return
        with cls._jobs_lock:
            if cls._worker_thread and cls._worker_thread.is_alive():
                return
            cls._worker_thread = threading.Thread(
                target=cls._worker_loop,
                name="clinical-chat-async-worker",
                daemon=True,
            )
            cls._worker_thread.start()

    @classmethod
    def _worker_loop(cls) -> None:
        while True:
            job_id = cls._job_queue.get()
            try:
                cls._execute_job(job_id=job_id)
            except Exception as exc:  # pragma: no cover - guardia final
                cls._mark_failed(job_id=job_id, error=f"worker_unhandled:{type(exc).__name__}")
            finally:
                cls._job_queue.task_done()

    @classmethod
    def _execute_job(cls, *, job_id: str) -> None:
        with cls._jobs_lock:
            record = cls._jobs.get(job_id)
            if record is None:
                return
            record["status"] = "running"
            record["updated_at"] = datetime.now(timezone.utc)
            payload_data = dict(record.get("payload") or {})
            care_task_id = int(record["care_task_id"])
            user_id = record.get("user_id")

        try:
            payload = CareTaskClinicalChatMessageRequest(**payload_data)
        except Exception as exc:
            cls._mark_failed(job_id=job_id, error=f"invalid_payload:{type(exc).__name__}")
            return

        try:
            db = SessionLocal()
            try:
                care_task = db.query(CareTask).filter(CareTask.id == care_task_id).first()
                if care_task is None:
                    cls._mark_failed(job_id=job_id, error="care_task_not_found")
                    return
                user = None
                if user_id is not None:
                    user = db.query(User).filter(User.id == int(user_id)).first()
                    if user is None:
                        cls._mark_failed(job_id=job_id, error="user_not_found")
                        return
                (
                    message,
                    agent_run_id,
                    workflow_name,
                    interpretability_trace,
                    response_mode,
                    tool_mode,
                    quality_metrics,
                    _tool_policy_decision,
                    _security_findings,
                ) = ClinicalChatService.create_message(
                    db=db,
                    care_task=care_task,
                    payload=payload,
                    authenticated_user=user,
                )
            finally:
                db.close()
        except Exception as exc:
            cls._mark_failed(job_id=job_id, error=f"{type(exc).__name__}:{str(exc)[:200]}")
            return

        llm_used = any(
            str(item).strip() == "llm_used=true"
            for item in (interpretability_trace or [])
        )
        with cls._jobs_lock:
            record = cls._jobs.get(job_id)
            if record is None:
                return
            record["status"] = "completed"
            record["updated_at"] = datetime.now(timezone.utc)
            record["message_id"] = int(message.id)
            record["session_id"] = str(message.session_id)
            record["agent_run_id"] = int(agent_run_id)
            record["workflow_name"] = str(workflow_name)
            record["response_mode"] = str(response_mode)
            record["tool_mode"] = str(tool_mode)
            record["quality_status"] = str(quality_metrics.get("quality_status") or "degraded")
            record["llm_used"] = bool(llm_used)
            record["error"] = None

    @classmethod
    def _mark_failed(cls, *, job_id: str, error: str) -> None:
        with cls._jobs_lock:
            record = cls._jobs.get(job_id)
            if record is None:
                return
            record["status"] = "failed"
            record["updated_at"] = datetime.now(timezone.utc)
            record["error"] = error[:240]

    @classmethod
    def _cleanup_jobs_locked(cls, *, now: datetime) -> None:
        threshold = now - timedelta(minutes=cls._ttl_minutes)
        stale_ids: list[str] = []
        for job_id, record in cls._jobs.items():
            created_at = record.get("created_at")
            if isinstance(created_at, datetime) and created_at < threshold:
                stale_ids.append(job_id)
        for job_id in stale_ids:
            cls._jobs.pop(job_id, None)
        if len(cls._jobs) <= cls._max_jobs:
            return
        # Proteccion por cardinalidad: elimina los mas antiguos.
        ordered = sorted(
            cls._jobs.items(),
            key=lambda item: item[1].get("created_at") or datetime.now(timezone.utc),
        )
        overflow = len(cls._jobs) - cls._max_jobs
        for job_id, _ in ordered[:overflow]:
            cls._jobs.pop(job_id, None)

    @classmethod
    def _public_job_view(cls, record: dict[str, Any]) -> dict[str, Any]:
        return {
            "job_id": str(record["job_id"]),
            "care_task_id": int(record["care_task_id"]),
            "session_id": str(record["session_id"]),
            "status": str(record["status"]),
            "created_at": record["created_at"],
            "updated_at": record["updated_at"],
            "message_id": record.get("message_id"),
            "agent_run_id": record.get("agent_run_id"),
            "workflow_name": record.get("workflow_name"),
            "response_mode": record.get("response_mode"),
            "tool_mode": record.get("tool_mode"),
            "quality_status": record.get("quality_status"),
            "llm_used": record.get("llm_used"),
            "error": record.get("error"),
        }

    @staticmethod
    def _safe_session_id(raw_session_id: str | None) -> str:
        if raw_session_id and raw_session_id.strip():
            return raw_session_id.strip()
        return f"chat-{uuid4().hex[:12]}"
