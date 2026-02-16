"""
Endpoints de CareTask - CRUD en paralelo para el pivot de dominio.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.acne_rosacea_protocol import (
    AcneRosaceaDifferentialRecommendation,
    AcneRosaceaDifferentialRequest,
    CareTaskAcneRosaceaDifferentialResponse,
)
from app.schemas.advanced_screening import (
    AdvancedScreeningRecommendation,
    AdvancedScreeningRequest,
    CareTaskAdvancedScreeningResponse,
)
from app.schemas.ai import TaskTriageResponse
from app.schemas.anesthesiology_support_protocol import (
    AnesthesiologySupportProtocolRecommendation,
    AnesthesiologySupportProtocolRequest,
    CareTaskAnesthesiologySupportResponse,
)
from app.schemas.anisakis_support_protocol import (
    AnisakisSupportProtocolRecommendation,
    AnisakisSupportProtocolRequest,
    CareTaskAnisakisSupportResponse,
)
from app.schemas.cardio_risk_protocol import (
    CardioRiskProtocolRecommendation,
    CardioRiskProtocolRequest,
    CareTaskCardioRiskProtocolResponse,
)
from app.schemas.care_task import (
    CareTaskCardioRiskAuditRequest,
    CareTaskCardioRiskAuditResponse,
    CareTaskCardioRiskAuditSummaryResponse,
    CareTaskCreate,
    CareTaskMedicolegalAuditRequest,
    CareTaskMedicolegalAuditResponse,
    CareTaskMedicolegalAuditSummaryResponse,
    CareTaskQualityScorecardResponse,
    CareTaskResponse,
    CareTaskResuscitationAuditRequest,
    CareTaskResuscitationAuditResponse,
    CareTaskResuscitationAuditSummaryResponse,
    CareTaskScasestAuditRequest,
    CareTaskScasestAuditResponse,
    CareTaskScasestAuditSummaryResponse,
    CareTaskScreeningAuditRequest,
    CareTaskScreeningAuditResponse,
    CareTaskScreeningAuditSummaryResponse,
    CareTaskTriageApprovalRequest,
    CareTaskTriageApprovalResponse,
    CareTaskTriageAuditRequest,
    CareTaskTriageAuditResponse,
    CareTaskTriageAuditSummaryResponse,
    CareTaskTriageResponse,
    CareTaskUpdate,
)
from app.schemas.chest_xray_support import (
    CareTaskChestXRaySupportResponse,
    ChestXRaySupportRecommendation,
    ChestXRaySupportRequest,
)
from app.schemas.clinical_chat import (
    CareTaskClinicalChatHistoryItemResponse,
    CareTaskClinicalChatMemoryResponse,
    CareTaskClinicalChatMessageRequest,
    CareTaskClinicalChatMessageResponse,
)
from app.schemas.critical_ops_protocol import (
    CareTaskCriticalOpsProtocolResponse,
    CriticalOpsProtocolRecommendation,
    CriticalOpsProtocolRequest,
)
from app.schemas.endocrinology_support_protocol import (
    CareTaskEndocrinologySupportResponse,
    EndocrinologySupportProtocolRecommendation,
    EndocrinologySupportProtocolRequest,
)
from app.schemas.epidemiology_support_protocol import (
    CareTaskEpidemiologySupportResponse,
    EpidemiologySupportProtocolRecommendation,
    EpidemiologySupportProtocolRequest,
)
from app.schemas.gastro_hepato_support_protocol import (
    CareTaskGastroHepatoSupportResponse,
    GastroHepatoSupportProtocolRecommendation,
    GastroHepatoSupportProtocolRequest,
)
from app.schemas.genetic_recurrence_support_protocol import (
    CareTaskGeneticRecurrenceSupportResponse,
    GeneticRecurrenceSupportProtocolRecommendation,
    GeneticRecurrenceSupportProtocolRequest,
)
from app.schemas.geriatrics_support_protocol import (
    CareTaskGeriatricsSupportResponse,
    GeriatricsSupportProtocolRecommendation,
    GeriatricsSupportProtocolRequest,
)
from app.schemas.gynecology_obstetrics_support_protocol import (
    CareTaskGynecologyObstetricsSupportResponse,
    GynecologyObstetricsSupportProtocolRecommendation,
    GynecologyObstetricsSupportProtocolRequest,
)
from app.schemas.hematology_support_protocol import (
    CareTaskHematologySupportResponse,
    HematologySupportProtocolRecommendation,
    HematologySupportProtocolRequest,
)
from app.schemas.humanization_protocol import (
    CareTaskHumanizationProtocolResponse,
    HumanizationProtocolRecommendation,
    HumanizationProtocolRequest,
)
from app.schemas.immunology_support_protocol import (
    CareTaskImmunologySupportResponse,
    ImmunologySupportProtocolRecommendation,
    ImmunologySupportProtocolRequest,
)
from app.schemas.medicolegal_ops import (
    CareTaskMedicolegalOpsResponse,
    MedicolegalOpsRecommendation,
    MedicolegalOpsRequest,
)
from app.schemas.nephrology_support_protocol import (
    CareTaskNephrologySupportResponse,
    NephrologySupportProtocolRecommendation,
    NephrologySupportProtocolRequest,
)
from app.schemas.neurology_support_protocol import (
    CareTaskNeurologySupportResponse,
    NeurologySupportProtocolRecommendation,
    NeurologySupportProtocolRequest,
)
from app.schemas.oncology_support_protocol import (
    CareTaskOncologySupportResponse,
    OncologySupportProtocolRecommendation,
    OncologySupportProtocolRequest,
)
from app.schemas.ophthalmology_support_protocol import (
    CareTaskOphthalmologySupportResponse,
    OphthalmologySupportProtocolRecommendation,
    OphthalmologySupportProtocolRequest,
)
from app.schemas.palliative_support_protocol import (
    CareTaskPalliativeSupportResponse,
    PalliativeSupportProtocolRecommendation,
    PalliativeSupportProtocolRequest,
)
from app.schemas.pediatrics_neonatology_support_protocol import (
    CareTaskPediatricsNeonatologySupportResponse,
    PediatricsNeonatologySupportProtocolRecommendation,
    PediatricsNeonatologySupportProtocolRequest,
)
from app.schemas.pityriasis_protocol import (
    CareTaskPityriasisDifferentialResponse,
    PityriasisDifferentialRecommendation,
    PityriasisDifferentialRequest,
)
from app.schemas.pneumology_support_protocol import (
    CareTaskPneumologySupportResponse,
    PneumologySupportProtocolRecommendation,
    PneumologySupportProtocolRequest,
)
from app.schemas.psychiatry_support_protocol import (
    CareTaskPsychiatrySupportResponse,
    PsychiatrySupportProtocolRecommendation,
    PsychiatrySupportProtocolRequest,
)
from app.schemas.respiratory_protocol import (
    CareTaskRespiratoryProtocolResponse,
    RespiratoryProtocolRecommendation,
    RespiratoryProtocolRequest,
)
from app.schemas.resuscitation_protocol import (
    CareTaskResuscitationProtocolResponse,
    ResuscitationProtocolRecommendation,
    ResuscitationProtocolRequest,
)
from app.schemas.rheum_immuno_support_protocol import (
    CareTaskRheumImmunoSupportResponse,
    RheumImmunoSupportProtocolRecommendation,
    RheumImmunoSupportProtocolRequest,
)
from app.schemas.scasest_protocol import (
    CareTaskScasestProtocolResponse,
    ScasestProtocolRecommendation,
    ScasestProtocolRequest,
)
from app.schemas.sepsis_protocol import (
    CareTaskSepsisProtocolResponse,
    SepsisProtocolRecommendation,
    SepsisProtocolRequest,
)
from app.schemas.trauma_support_protocol import (
    CareTaskTraumaSupportResponse,
    TraumaSupportRecommendation,
    TraumaSupportRequest,
)
from app.schemas.urology_support_protocol import (
    CareTaskUrologySupportResponse,
    UrologySupportProtocolRecommendation,
    UrologySupportProtocolRequest,
)
from app.services.acne_rosacea_protocol_service import AcneRosaceaProtocolService
from app.services.advanced_screening_service import AdvancedScreeningService
from app.services.agent_run_service import AgentRunService
from app.services.anesthesiology_support_protocol_service import (
    AnesthesiologySupportProtocolService,
)
from app.services.anisakis_support_protocol_service import AnisakisSupportProtocolService
from app.services.cardio_risk_support_service import CardioRiskSupportService
from app.services.care_task_service import CareTaskService
from app.services.chest_xray_support_service import ChestXRaySupportService
from app.services.clinical_chat_service import ClinicalChatService
from app.services.critical_ops_protocol_service import CriticalOpsProtocolService
from app.services.endocrinology_support_protocol_service import EndocrinologySupportProtocolService
from app.services.epidemiology_support_protocol_service import EpidemiologySupportProtocolService
from app.services.gastro_hepato_support_protocol_service import GastroHepatoSupportProtocolService
from app.services.genetic_recurrence_support_protocol_service import (
    GeneticRecurrenceSupportProtocolService,
)
from app.services.geriatrics_support_protocol_service import GeriatricsSupportProtocolService
from app.services.gynecology_obstetrics_support_protocol_service import (
    GynecologyObstetricsSupportProtocolService,
)
from app.services.hematology_support_protocol_service import HematologySupportProtocolService
from app.services.humanization_protocol_service import HumanizationProtocolService
from app.services.immunology_support_protocol_service import ImmunologySupportProtocolService
from app.services.medicolegal_ops_service import MedicolegalOpsService
from app.services.nephrology_support_protocol_service import NephrologySupportProtocolService
from app.services.neurology_support_protocol_service import NeurologySupportProtocolService
from app.services.oncology_support_protocol_service import OncologySupportProtocolService
from app.services.ophthalmology_support_protocol_service import OphthalmologySupportProtocolService
from app.services.palliative_support_protocol_service import PalliativeSupportProtocolService
from app.services.pediatrics_neonatology_support_protocol_service import (
    PediatricsNeonatologySupportProtocolService,
)
from app.services.pityriasis_protocol_service import PityriasisProtocolService
from app.services.pneumology_support_protocol_service import PneumologySupportProtocolService
from app.services.psychiatry_support_protocol_service import PsychiatrySupportProtocolService
from app.services.respiratory_protocol_service import RespiratoryProtocolService
from app.services.resuscitation_protocol_service import ResuscitationProtocolService
from app.services.rheum_immuno_support_protocol_service import RheumImmunoSupportProtocolService
from app.services.scasest_protocol_service import ScasestProtocolService
from app.services.sepsis_protocol_service import SepsisProtocolService
from app.services.trauma_support_protocol_service import TraumaSupportProtocolService
from app.services.urology_support_protocol_service import UrologySupportProtocolService

router = APIRouter(prefix="/care-tasks", tags=["care-tasks"])


@router.post("/", response_model=CareTaskResponse, status_code=status.HTTP_201_CREATED)
def create_care_task(task: CareTaskCreate, db: Session = Depends(get_db)):
    """Crea un nuevo CareTask con validacion de prioridad clinica."""
    try:
        return CareTaskService.create_care_task(db, task)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/", response_model=List[CareTaskResponse])
def get_care_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    completed: Optional[bool] = Query(None),
    clinical_priority: Optional[str] = Query(None),
    patient_reference: Optional[str] = Query(None, max_length=120),
    db: Session = Depends(get_db),
):
    """Lista CareTask con filtros por estado y prioridad."""
    return CareTaskService.get_all_care_tasks(
        db,
        skip=skip,
        limit=limit,
        completed=completed,
        clinical_priority=clinical_priority,
        patient_reference=patient_reference,
    )


@router.get("/stats/count")
def get_care_tasks_stats(
    completed: Optional[bool] = Query(None),
    clinical_priority: Optional[str] = Query(None),
    patient_reference: Optional[str] = Query(None, max_length=120),
    db: Session = Depends(get_db),
):
    """Devuelve contador total y filtros para monitorizar carga operativa."""
    total = CareTaskService.get_care_tasks_count(
        db,
        completed=completed,
        clinical_priority=None,
        patient_reference=patient_reference,
    )
    filtered = CareTaskService.get_care_tasks_count(
        db,
        completed=completed,
        clinical_priority=clinical_priority,
        patient_reference=patient_reference,
    )
    return {"total": total, "filtered": filtered}


@router.get("/quality/scorecard", response_model=CareTaskQualityScorecardResponse)
def get_care_tasks_quality_scorecard(db: Session = Depends(get_db)):
    """Devuelve scorecard global de calidad IA clinica para observabilidad operativa."""
    summary = CareTaskService.get_quality_scorecard(db=db)
    return CareTaskQualityScorecardResponse(**summary)


@router.get("/{task_id}", response_model=CareTaskResponse)
def get_care_task(task_id: int, db: Session = Depends(get_db)):
    """Devuelve un CareTask por ID."""
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")
    return task


@router.put("/{task_id}", response_model=CareTaskResponse)
def update_care_task(task_id: int, task_data: CareTaskUpdate, db: Session = Depends(get_db)):
    """Actualiza un CareTask existente."""
    try:
        updated_task = CareTaskService.update_care_task(db, task_id, task_data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if not updated_task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")
    return updated_task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_care_task(task_id: int, db: Session = Depends(get_db)):
    """Elimina un CareTask."""
    deleted = CareTaskService.delete_care_task(db, task_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")
    return None


@router.post(
    "/{task_id}/chat/messages",
    response_model=CareTaskClinicalChatMessageResponse,
)
def create_care_task_chat_message(
    task_id: int,
    payload: CareTaskClinicalChatMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Crea un turno de chat clinico-operativo y lo persiste para memoria futura.

    El chat no sustituye criterio clinico: entrega soporte operativo trazable.
    """
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")

    message, agent_run_id, workflow_name, interpretability_trace, response_mode, tool_mode = (
        ClinicalChatService.create_message(
            db=db,
            care_task=task,
            payload=payload,
            authenticated_user=current_user,
        )
    )
    return CareTaskClinicalChatMessageResponse(
        care_task_id=task.id,
        message_id=message.id,
        session_id=message.session_id,
        agent_run_id=agent_run_id,
        workflow_name=workflow_name,
        response_mode=response_mode,
        tool_mode=tool_mode,
        answer=message.assistant_answer,
        matched_domains=list(message.matched_domains or []),
        matched_endpoints=list(message.matched_endpoints or []),
        effective_specialty=message.effective_specialty,
        knowledge_sources=list(message.knowledge_sources or []),
        web_sources=list(message.web_sources or []),
        memory_facts_used=list(message.memory_facts_used or []),
        patient_history_facts_used=list(message.patient_history_facts_used or []),
        extracted_facts=list(message.extracted_facts or []),
        interpretability_trace=interpretability_trace,
        non_diagnostic_warning=(
            "Soporte operativo no diagnostico. Requiere validacion humana y protocolo local."
        ),
    )


@router.get(
    "/{task_id}/chat/messages",
    response_model=List[CareTaskClinicalChatHistoryItemResponse],
)
def list_care_task_chat_messages(
    task_id: int,
    session_id: Optional[str] = Query(default=None, min_length=3, max_length=64),
    limit: int = Query(default=30, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Lista historial de chat clinico por CareTask y sesion opcional."""
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")

    return ClinicalChatService.list_messages(
        db,
        care_task_id=task_id,
        session_id=session_id,
        limit=limit,
    )


@router.get(
    "/{task_id}/chat/memory",
    response_model=CareTaskClinicalChatMemoryResponse,
)
def get_care_task_chat_memory(
    task_id: int,
    session_id: Optional[str] = Query(default=None, min_length=3, max_length=64),
    limit: int = Query(default=200, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Devuelve memoria agregada reutilizable del chat clinico para el CareTask."""
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")

    summary = ClinicalChatService.summarize_memory(
        db,
        care_task_id=task_id,
        session_id=session_id,
        limit=limit,
    )
    return CareTaskClinicalChatMemoryResponse(
        care_task_id=task_id,
        session_id=session_id,
        interactions_count=int(summary["interactions_count"]),
        top_domains=list(summary["top_domains"]),
        top_extracted_facts=list(summary["top_extracted_facts"]),
        patient_reference=summary.get("patient_reference"),
        patient_interactions_count=int(summary.get("patient_interactions_count", 0)),
        patient_top_domains=list(summary.get("patient_top_domains", [])),
        patient_top_extracted_facts=list(summary.get("patient_top_extracted_facts", [])),
    )


@router.post("/{task_id}/triage", response_model=CareTaskTriageResponse)
def triage_care_task(task_id: int, db: Session = Depends(get_db)):
    """
    Ejecuta triaje de agente sobre un CareTask existente.

    Este endpoint no diagnostica: solo prioriza y clasifica trabajo operativo
    para ayudar a ordenar cola y tiempos de respuesta.
    """
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")

    run = AgentRunService.run_care_task_triage_workflow(db=db, care_task=task)
    triage_payload = run.run_output.get("triage") if run.run_output else None
    if triage_payload is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo construir salida de triaje para CareTask.",
        )

    return CareTaskTriageResponse(
        care_task_id=task.id,
        agent_run_id=run.id,
        workflow_name=run.workflow_name,
        triage=TaskTriageResponse(**triage_payload),
    )


@router.post("/{task_id}/triage/approve", response_model=CareTaskTriageApprovalResponse)
def approve_care_task_triage(
    task_id: int,
    approval: CareTaskTriageApprovalRequest,
    db: Session = Depends(get_db),
):
    """
    Guarda la decision humana sobre un triaje de CareTask.

    Sirve para cerrar el circuito humano-en-el-bucle y dejar evidencia
    auditable de aceptacion o rechazo del resultado del agente.
    """
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")

    try:
        review = CareTaskService.approve_care_task_triage(db=db, task_id=task_id, approval=approval)
    except ValueError as exc:
        message = str(exc)
        if "no encontrada" in message:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message) from exc
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message) from exc

    return CareTaskTriageApprovalResponse(
        review_id=review.id,
        care_task_id=review.care_task_id,
        agent_run_id=review.agent_run_id,
        approved=review.approved,
        reviewer_note=review.reviewer_note,
        reviewed_by=review.reviewed_by,
        created_at=review.created_at,
        updated_at=review.updated_at,
    )


@router.post("/{task_id}/triage/audit", response_model=CareTaskTriageAuditResponse)
def create_care_task_triage_audit(
    task_id: int,
    payload: CareTaskTriageAuditRequest,
    db: Session = Depends(get_db),
):
    """
    Registra auditoria de desviacion (under/over/match) entre IA y validacion humana.
    """
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")

    try:
        audit = CareTaskService.create_or_update_triage_audit(
            db=db,
            task_id=task_id,
            payload=payload,
        )
    except ValueError as exc:
        message = str(exc)
        if "no encontrada" in message:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message) from exc
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message) from exc

    return CareTaskTriageAuditResponse(
        audit_id=audit.id,
        care_task_id=audit.care_task_id,
        agent_run_id=audit.agent_run_id,
        ai_recommended_level=audit.ai_recommended_level,
        human_validated_level=audit.human_validated_level,
        classification=audit.classification,
        reviewer_note=audit.reviewer_note,
        reviewed_by=audit.reviewed_by,
        created_at=audit.created_at,
        updated_at=audit.updated_at,
    )


@router.get("/{task_id}/triage/audit", response_model=list[CareTaskTriageAuditResponse])
def list_care_task_triage_audits(
    task_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Lista auditorias de triaje de un CareTask para revision historica."""
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")

    audits = CareTaskService.list_triage_audits(db=db, task_id=task_id, limit=limit)
    return [
        CareTaskTriageAuditResponse(
            audit_id=item.id,
            care_task_id=item.care_task_id,
            agent_run_id=item.agent_run_id,
            ai_recommended_level=item.ai_recommended_level,
            human_validated_level=item.human_validated_level,
            classification=item.classification,
            reviewer_note=item.reviewer_note,
            reviewed_by=item.reviewed_by,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
        for item in audits
    ]


@router.get("/{task_id}/triage/audit/summary", response_model=CareTaskTriageAuditSummaryResponse)
def get_care_task_triage_audit_summary(task_id: int, db: Session = Depends(get_db)):
    """Devuelve resumen agregado de auditoria de triaje para un CareTask."""
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")
    summary = CareTaskService.get_triage_audit_summary(db=db, task_id=task_id)
    return CareTaskTriageAuditSummaryResponse(**summary)


@router.post(
    "/{task_id}/respiratory-protocol/recommendation",
    response_model=CareTaskRespiratoryProtocolResponse,
)
def run_care_task_respiratory_protocol(
    task_id: int,
    payload: RespiratoryProtocolRequest,
    db: Session = Depends(get_db),
):
    """
    Ejecuta recomendacion operativa temprana para infecciones respiratorias viricas.

    No realiza diagnostico; propone acciones de triaje/prueba/tratamiento temprano
    para validar por clinica humana.
    """
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")

    recommendation = RespiratoryProtocolService.build_recommendation(payload)
    run = AgentRunService.run_respiratory_protocol_workflow(
        db=db,
        care_task=task,
        protocol_input=payload.model_dump(),
        protocol_output=recommendation.model_dump(),
    )
    return CareTaskRespiratoryProtocolResponse(
        care_task_id=task.id,
        agent_run_id=run.id,
        workflow_name=run.workflow_name,
        recommendation=RespiratoryProtocolRecommendation(**recommendation.model_dump()),
    )


@router.post(
    "/{task_id}/humanization/recommendation",
    response_model=CareTaskHumanizationProtocolResponse,
)
def run_care_task_humanization_protocol(
    task_id: int,
    payload: HumanizationProtocolRequest,
    db: Session = Depends(get_db),
):
    """
    Ejecuta recomendacion operativa de humanizacion pediatrica en alta complejidad.

    No realiza diagnostico medico; organiza comunicacion, soporte familiar
    y coordinacion multidisciplinar con validacion humana obligatoria.
    """
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")

    recommendation = HumanizationProtocolService.build_recommendation(payload)
    run = AgentRunService.run_pediatric_humanization_workflow(
        db=db,
        care_task=task,
        protocol_input=payload.model_dump(),
        protocol_output=recommendation.model_dump(),
    )
    return CareTaskHumanizationProtocolResponse(
        care_task_id=task.id,
        agent_run_id=run.id,
        workflow_name=run.workflow_name,
        recommendation=HumanizationProtocolRecommendation(**recommendation.model_dump()),
    )


@router.post(
    "/{task_id}/screening/recommendation",
    response_model=CareTaskAdvancedScreeningResponse,
)
def run_care_task_advanced_screening(
    task_id: int,
    payload: AdvancedScreeningRequest,
    db: Session = Depends(get_db),
):
    """
    Ejecuta screening operativo avanzado con reglas interpretables.

    Cubre riesgo geriatrico, sugerencias de cribado temprano, control de
    fatiga de alarmas y criterios operativos de COVID persistente.
    """
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")

    recommendation = AdvancedScreeningService.build_recommendation(payload)
    run = AgentRunService.run_advanced_screening_workflow(
        db=db,
        care_task=task,
        protocol_input=payload.model_dump(),
        protocol_output=recommendation.model_dump(),
    )
    return CareTaskAdvancedScreeningResponse(
        care_task_id=task.id,
        agent_run_id=run.id,
        workflow_name=run.workflow_name,
        recommendation=AdvancedScreeningRecommendation(**recommendation.model_dump()),
    )


@router.post("/{task_id}/screening/audit", response_model=CareTaskScreeningAuditResponse)
def create_care_task_screening_audit(
    task_id: int,
    payload: CareTaskScreeningAuditRequest,
    db: Session = Depends(get_db),
):
    """Registra auditoria de calidad para screening avanzado (IA vs humano)."""
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")

    try:
        audit = CareTaskService.create_or_update_screening_audit(
            db=db,
            task_id=task_id,
            payload=payload,
        )
    except ValueError as exc:
        message = str(exc)
        if "no encontrada" in message:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message) from exc
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message) from exc

    return CareTaskScreeningAuditResponse(
        audit_id=audit.id,
        care_task_id=audit.care_task_id,
        agent_run_id=audit.agent_run_id,
        ai_geriatric_risk_level=audit.ai_geriatric_risk_level,
        human_validated_risk_level=audit.human_validated_risk_level,
        classification=audit.classification,
        ai_hiv_screening_suggested=audit.ai_hiv_screening_suggested,
        human_hiv_screening_suggested=audit.human_hiv_screening_suggested,
        ai_sepsis_route_suggested=audit.ai_sepsis_route_suggested,
        human_sepsis_route_suggested=audit.human_sepsis_route_suggested,
        ai_persistent_covid_suspected=audit.ai_persistent_covid_suspected,
        human_persistent_covid_suspected=audit.human_persistent_covid_suspected,
        ai_long_acting_candidate=audit.ai_long_acting_candidate,
        human_long_acting_candidate=audit.human_long_acting_candidate,
        reviewer_note=audit.reviewer_note,
        reviewed_by=audit.reviewed_by,
        created_at=audit.created_at,
        updated_at=audit.updated_at,
    )


@router.get("/{task_id}/screening/audit", response_model=list[CareTaskScreeningAuditResponse])
def list_care_task_screening_audits(
    task_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Lista auditorias de screening de un CareTask para revision historica."""
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")

    audits = CareTaskService.list_screening_audits(db=db, task_id=task_id, limit=limit)
    return [
        CareTaskScreeningAuditResponse(
            audit_id=item.id,
            care_task_id=item.care_task_id,
            agent_run_id=item.agent_run_id,
            ai_geriatric_risk_level=item.ai_geriatric_risk_level,
            human_validated_risk_level=item.human_validated_risk_level,
            classification=item.classification,
            ai_hiv_screening_suggested=item.ai_hiv_screening_suggested,
            human_hiv_screening_suggested=item.human_hiv_screening_suggested,
            ai_sepsis_route_suggested=item.ai_sepsis_route_suggested,
            human_sepsis_route_suggested=item.human_sepsis_route_suggested,
            ai_persistent_covid_suspected=item.ai_persistent_covid_suspected,
            human_persistent_covid_suspected=item.human_persistent_covid_suspected,
            ai_long_acting_candidate=item.ai_long_acting_candidate,
            human_long_acting_candidate=item.human_long_acting_candidate,
            reviewer_note=item.reviewer_note,
            reviewed_by=item.reviewed_by,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
        for item in audits
    ]


@router.get(
    "/{task_id}/screening/audit/summary",
    response_model=CareTaskScreeningAuditSummaryResponse,
)
def get_care_task_screening_audit_summary(task_id: int, db: Session = Depends(get_db)):
    """Devuelve resumen agregado de calidad de screening para un CareTask."""
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")
    summary = CareTaskService.get_screening_audit_summary(db=db, task_id=task_id)
    return CareTaskScreeningAuditSummaryResponse(**summary)


@router.post(
    "/{task_id}/chest-xray/interpretation-support",
    response_model=CareTaskChestXRaySupportResponse,
)
def run_care_task_chest_xray_support(
    task_id: int,
    payload: ChestXRaySupportRequest,
    db: Session = Depends(get_db),
):
    """
    Ejecuta soporte operativo de interpretacion de RX de torax.

    No emite diagnostico definitivo; prioriza patrones, red flags y acciones
    para validacion clinica humana.
    """
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")

    recommendation = ChestXRaySupportService.build_recommendation(payload)
    run = AgentRunService.run_chest_xray_support_workflow(
        db=db,
        care_task=task,
        protocol_input=payload.model_dump(),
        protocol_output=recommendation.model_dump(),
    )
    return CareTaskChestXRaySupportResponse(
        care_task_id=task.id,
        agent_run_id=run.id,
        workflow_name=run.workflow_name,
        recommendation=ChestXRaySupportRecommendation(**recommendation.model_dump()),
    )


@router.post(
    "/{task_id}/pityriasis-differential/recommendation",
    response_model=CareTaskPityriasisDifferentialResponse,
)
def run_care_task_pityriasis_differential(
    task_id: int,
    payload: PityriasisDifferentialRequest,
    db: Session = Depends(get_db),
):
    """
    Ejecuta soporte operativo de diagnostico diferencial para pitiriasis.

    No emite diagnostico dermatologico definitivo; organiza hipotesis,
    pruebas de confirmacion y red flags para validacion humana.
    """
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")

    recommendation = PityriasisProtocolService.build_recommendation(payload)
    run = AgentRunService.run_pityriasis_differential_workflow(
        db=db,
        care_task=task,
        protocol_input=payload.model_dump(),
        protocol_output=recommendation.model_dump(),
    )
    return CareTaskPityriasisDifferentialResponse(
        care_task_id=task.id,
        agent_run_id=run.id,
        workflow_name=run.workflow_name,
        recommendation=PityriasisDifferentialRecommendation(**recommendation.model_dump()),
    )


@router.post(
    "/{task_id}/acne-rosacea/recommendation",
    response_model=CareTaskAcneRosaceaDifferentialResponse,
)
def run_care_task_acne_rosacea_differential(
    task_id: int,
    payload: AcneRosaceaDifferentialRequest,
    db: Session = Depends(get_db),
):
    """
    Ejecuta soporte operativo diferencial para acne y rosacea.

    No emite diagnostico definitivo; organiza hipotesis, escalado terapeutico
    y controles de seguridad farmacologica para validacion humana.
    """
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")

    recommendation = AcneRosaceaProtocolService.build_recommendation(payload)
    run = AgentRunService.run_acne_rosacea_differential_workflow(
        db=db,
        care_task=task,
        protocol_input=payload.model_dump(),
        protocol_output=recommendation.model_dump(),
    )
    return CareTaskAcneRosaceaDifferentialResponse(
        care_task_id=task.id,
        agent_run_id=run.id,
        workflow_name=run.workflow_name,
        recommendation=AcneRosaceaDifferentialRecommendation(**recommendation.model_dump()),
    )


@router.post(
    "/{task_id}/trauma/recommendation",
    response_model=CareTaskTraumaSupportResponse,
)
def run_care_task_trauma_support(
    task_id: int,
    payload: TraumaSupportRequest,
    db: Session = Depends(get_db),
):
    """
    Ejecuta soporte operativo de trauma para priorizacion y seguridad inicial.

    No emite diagnostico definitivo; organiza riesgos trimodales, via aerea,
    medula, aplastamiento y soporte por perfil para validacion humana.
    """
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")

    recommendation = TraumaSupportProtocolService.build_recommendation(payload)
    run = AgentRunService.run_trauma_support_workflow(
        db=db,
        care_task=task,
        protocol_input=payload.model_dump(),
        protocol_output=recommendation.model_dump(),
    )
    return CareTaskTraumaSupportResponse(
        care_task_id=task.id,
        agent_run_id=run.id,
        workflow_name=run.workflow_name,
        recommendation=TraumaSupportRecommendation(**recommendation.model_dump()),
    )


@router.post(
    "/{task_id}/critical-ops/recommendation",
    response_model=CareTaskCriticalOpsProtocolResponse,
)
def run_care_task_critical_ops_support(
    task_id: int,
    payload: CriticalOpsProtocolRequest,
    db: Session = Depends(get_db),
):
    """
    Ejecuta soporte operativo critico transversal para urgencias.

    No realiza diagnostico definitivo; prioriza SLA clinicos, rutas
    operativas y alertas de seguridad para validacion humana.
    """
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")

    recommendation = CriticalOpsProtocolService.build_recommendation(payload)
    run = AgentRunService.run_critical_ops_workflow(
        db=db,
        care_task=task,
        protocol_input=payload.model_dump(),
        protocol_output=recommendation.model_dump(),
    )
    return CareTaskCriticalOpsProtocolResponse(
        care_task_id=task.id,
        agent_run_id=run.id,
        workflow_name=run.workflow_name,
        recommendation=CriticalOpsProtocolRecommendation(**recommendation.model_dump()),
    )


@router.post(
    "/{task_id}/neurology/recommendation",
    response_model=CareTaskNeurologySupportResponse,
)
def run_care_task_neurology_support(
    task_id: int,
    payload: NeurologySupportProtocolRequest,
    db: Session = Depends(get_db),
):
    """
    Ejecuta soporte operativo neurologico para urgencias.

    No realiza diagnostico definitivo; prioriza rutas de riesgo vascular,
    diferencial critico y seguridad terapeutica para validacion humana.
    """
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")

    recommendation = NeurologySupportProtocolService.build_recommendation(payload)
    run = AgentRunService.run_neurology_support_workflow(
        db=db,
        care_task=task,
        protocol_input=payload.model_dump(),
        protocol_output=recommendation.model_dump(),
    )
    return CareTaskNeurologySupportResponse(
        care_task_id=task.id,
        agent_run_id=run.id,
        workflow_name=run.workflow_name,
        recommendation=NeurologySupportProtocolRecommendation(**recommendation.model_dump()),
    )


@router.post(
    "/{task_id}/gastro-hepato/recommendation",
    response_model=CareTaskGastroHepatoSupportResponse,
)
def run_care_task_gastro_hepato_support(
    task_id: int,
    payload: GastroHepatoSupportProtocolRequest,
    db: Session = Depends(get_db),
):
    """
    Ejecuta soporte operativo gastro-hepato para urgencias.

    No realiza diagnostico definitivo; prioriza rutas hemodinamicas,
    red flags de imagen y decisiones quirurgicas iniciales para validacion humana.
    """
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")

    recommendation = GastroHepatoSupportProtocolService.build_recommendation(payload)
    run = AgentRunService.run_gastro_hepato_support_workflow(
        db=db,
        care_task=task,
        protocol_input=payload.model_dump(),
        protocol_output=recommendation.model_dump(),
    )
    return CareTaskGastroHepatoSupportResponse(
        care_task_id=task.id,
        agent_run_id=run.id,
        workflow_name=run.workflow_name,
        recommendation=GastroHepatoSupportProtocolRecommendation(**recommendation.model_dump()),
    )


@router.post(
    "/{task_id}/rheum-immuno/recommendation",
    response_model=CareTaskRheumImmunoSupportResponse,
)
def run_care_task_rheum_immuno_support(
    task_id: int,
    payload: RheumImmunoSupportProtocolRequest,
    db: Session = Depends(get_db),
):
    """
    Ejecuta soporte operativo reuma-inmuno para urgencias.

    No realiza diagnostico definitivo; prioriza alertas de riesgo vital,
    reglas de seguridad terapeutica y rutas de cribado para validacion humana.
    """
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")

    recommendation = RheumImmunoSupportProtocolService.build_recommendation(payload)
    run = AgentRunService.run_rheum_immuno_support_workflow(
        db=db,
        care_task=task,
        protocol_input=payload.model_dump(),
        protocol_output=recommendation.model_dump(),
    )
    return CareTaskRheumImmunoSupportResponse(
        care_task_id=task.id,
        agent_run_id=run.id,
        workflow_name=run.workflow_name,
        recommendation=RheumImmunoSupportProtocolRecommendation(**recommendation.model_dump()),
    )


@router.post(
    "/{task_id}/psychiatry/recommendation",
    response_model=CareTaskPsychiatrySupportResponse,
)
def run_care_task_psychiatry_support(
    task_id: int,
    payload: PsychiatrySupportProtocolRequest,
    db: Session = Depends(get_db),
):
    """
    Ejecuta soporte operativo de psiquiatria para urgencias.

    No realiza diagnostico definitivo; organiza alertas de riesgo,
    reglas temporales y seguridad farmacologica para validacion humana.
    """
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")

    recommendation = PsychiatrySupportProtocolService.build_recommendation(payload)
    run = AgentRunService.run_psychiatry_support_workflow(
        db=db,
        care_task=task,
        protocol_input=payload.model_dump(),
        protocol_output=recommendation.model_dump(),
    )
    return CareTaskPsychiatrySupportResponse(
        care_task_id=task.id,
        agent_run_id=run.id,
        workflow_name=run.workflow_name,
        recommendation=PsychiatrySupportProtocolRecommendation(**recommendation.model_dump()),
    )


@router.post(
    "/{task_id}/hematology/recommendation",
    response_model=CareTaskHematologySupportResponse,
)
def run_care_task_hematology_support(
    task_id: int,
    payload: HematologySupportProtocolRequest,
    db: Session = Depends(get_db),
):
    """
    Ejecuta soporte operativo de hematologia para urgencias.

    No realiza diagnostico definitivo; organiza alertas de hemolisis, sangrado,
    seguridad postquirurgica y soporte de clasificacion para validacion humana.
    """
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")

    recommendation = HematologySupportProtocolService.build_recommendation(payload)
    run = AgentRunService.run_hematology_support_workflow(
        db=db,
        care_task=task,
        protocol_input=payload.model_dump(),
        protocol_output=recommendation.model_dump(),
    )
    return CareTaskHematologySupportResponse(
        care_task_id=task.id,
        agent_run_id=run.id,
        workflow_name=run.workflow_name,
        recommendation=HematologySupportProtocolRecommendation(**recommendation.model_dump()),
    )


@router.post(
    "/{task_id}/endocrinology/recommendation",
    response_model=CareTaskEndocrinologySupportResponse,
)
def run_care_task_endocrinology_support(
    task_id: int,
    payload: EndocrinologySupportProtocolRequest,
    db: Session = Depends(get_db),
):
    """
    Ejecuta soporte operativo de endocrinologia y metabolismo para urgencias.

    No realiza diagnostico definitivo; organiza alertas bioquimicas, cribado
    endocrino y seguridad farmacologica para validacion humana.
    """
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")

    recommendation = EndocrinologySupportProtocolService.build_recommendation(payload)
    run = AgentRunService.run_endocrinology_support_workflow(
        db=db,
        care_task=task,
        protocol_input=payload.model_dump(),
        protocol_output=recommendation.model_dump(),
    )
    return CareTaskEndocrinologySupportResponse(
        care_task_id=task.id,
        agent_run_id=run.id,
        workflow_name=run.workflow_name,
        recommendation=EndocrinologySupportProtocolRecommendation(**recommendation.model_dump()),
    )


@router.post(
    "/{task_id}/nephrology/recommendation",
    response_model=CareTaskNephrologySupportResponse,
)
def run_care_task_nephrology_support(
    task_id: int,
    payload: NephrologySupportProtocolRequest,
    db: Session = Depends(get_db),
):
    """
    Ejecuta soporte operativo de nefrologia para urgencias.

    No realiza diagnostico definitivo; organiza alertas sindromicas renales,
    equilibrio acido-base, criterios AEIOU y seguridad terapeutica.
    """
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")

    recommendation = NephrologySupportProtocolService.build_recommendation(payload)
    run = AgentRunService.run_nephrology_support_workflow(
        db=db,
        care_task=task,
        protocol_input=payload.model_dump(),
        protocol_output=recommendation.model_dump(),
    )
    return CareTaskNephrologySupportResponse(
        care_task_id=task.id,
        agent_run_id=run.id,
        workflow_name=run.workflow_name,
        recommendation=NephrologySupportProtocolRecommendation(**recommendation.model_dump()),
    )


@router.post(
    "/{task_id}/pneumology/recommendation",
    response_model=CareTaskPneumologySupportResponse,
)
def run_care_task_pneumology_support(
    task_id: int,
    payload: PneumologySupportProtocolRequest,
    db: Session = Depends(get_db),
):
    """
    Ejecuta soporte operativo de neumologia para urgencias.

    No realiza diagnostico definitivo; organiza diferenciales por imagen,
    evaluacion ventilatoria y seguridad de decisiones terapeuticas.
    """
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")

    recommendation = PneumologySupportProtocolService.build_recommendation(payload)
    run = AgentRunService.run_pneumology_support_workflow(
        db=db,
        care_task=task,
        protocol_input=payload.model_dump(),
        protocol_output=recommendation.model_dump(),
    )
    return CareTaskPneumologySupportResponse(
        care_task_id=task.id,
        agent_run_id=run.id,
        workflow_name=run.workflow_name,
        recommendation=PneumologySupportProtocolRecommendation(**recommendation.model_dump()),
    )


@router.post(
    "/{task_id}/geriatrics/recommendation",
    response_model=CareTaskGeriatricsSupportResponse,
)
def run_care_task_geriatrics_support(
    task_id: int,
    payload: GeriatricsSupportProtocolRequest,
    db: Session = Depends(get_db),
):
    """
    Ejecuta soporte operativo de geriatria y fragilidad para urgencias.

    No realiza diagnostico definitivo; organiza acciones sobre inmovilidad,
    delirium y seguridad farmacologica en personas mayores.
    """
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")

    recommendation = GeriatricsSupportProtocolService.build_recommendation(payload)
    run = AgentRunService.run_geriatrics_support_workflow(
        db=db,
        care_task=task,
        protocol_input=payload.model_dump(),
        protocol_output=recommendation.model_dump(),
    )
    return CareTaskGeriatricsSupportResponse(
        care_task_id=task.id,
        agent_run_id=run.id,
        workflow_name=run.workflow_name,
        recommendation=GeriatricsSupportProtocolRecommendation(**recommendation.model_dump()),
    )


@router.post(
    "/{task_id}/oncology/recommendation",
    response_model=CareTaskOncologySupportResponse,
)
def run_care_task_oncology_support(
    task_id: int,
    payload: OncologySupportProtocolRequest,
    db: Session = Depends(get_db),
):
    """
    Ejecuta soporte operativo de oncologia para urgencias.

    No realiza diagnostico definitivo; organiza decisiones sobre inmunoterapia,
    toxicidades, cardio-oncologia y neutropenia febril.
    """
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")

    recommendation = OncologySupportProtocolService.build_recommendation(payload)
    run = AgentRunService.run_oncology_support_workflow(
        db=db,
        care_task=task,
        protocol_input=payload.model_dump(),
        protocol_output=recommendation.model_dump(),
    )
    return CareTaskOncologySupportResponse(
        care_task_id=task.id,
        agent_run_id=run.id,
        workflow_name=run.workflow_name,
        recommendation=OncologySupportProtocolRecommendation(**recommendation.model_dump()),
    )


@router.post(
    "/{task_id}/anesthesiology/recommendation",
    response_model=CareTaskAnesthesiologySupportResponse,
)
def run_care_task_anesthesiology_support(
    task_id: int,
    payload: AnesthesiologySupportProtocolRequest,
    db: Session = Depends(get_db),
):
    """
    Ejecuta soporte operativo de anestesiologia y reanimacion para urgencias.

    No realiza diagnostico definitivo; organiza seguridad de ISR y
    recomendacion anatomica de bloqueos simpaticos para dolor complejo.
    """
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")

    recommendation = AnesthesiologySupportProtocolService.build_recommendation(payload)
    run = AgentRunService.run_anesthesiology_support_workflow(
        db=db,
        care_task=task,
        protocol_input=payload.model_dump(),
        protocol_output=recommendation.model_dump(),
    )
    return CareTaskAnesthesiologySupportResponse(
        care_task_id=task.id,
        agent_run_id=run.id,
        workflow_name=run.workflow_name,
        recommendation=AnesthesiologySupportProtocolRecommendation(
            **recommendation.model_dump()
        ),
    )


@router.post(
    "/{task_id}/palliative/recommendation",
    response_model=CareTaskPalliativeSupportResponse,
)
def run_care_task_palliative_support(
    task_id: int,
    payload: PalliativeSupportProtocolRequest,
    db: Session = Depends(get_db),
):
    """
    Ejecuta soporte operativo de cuidados paliativos para urgencias.

    No realiza diagnostico definitivo; organiza decisiones de adecuacion,
    seguridad opioide, confort en demencia avanzada y delirium.
    """
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")

    recommendation = PalliativeSupportProtocolService.build_recommendation(payload)
    run = AgentRunService.run_palliative_support_workflow(
        db=db,
        care_task=task,
        protocol_input=payload.model_dump(),
        protocol_output=recommendation.model_dump(),
    )
    return CareTaskPalliativeSupportResponse(
        care_task_id=task.id,
        agent_run_id=run.id,
        workflow_name=run.workflow_name,
        recommendation=PalliativeSupportProtocolRecommendation(**recommendation.model_dump()),
    )


@router.post(
    "/{task_id}/urology/recommendation",
    response_model=CareTaskUrologySupportResponse,
)
def run_care_task_urology_support(
    task_id: int,
    payload: UrologySupportProtocolRequest,
    db: Session = Depends(get_db),
):
    """
    Ejecuta soporte operativo de urologia para urgencias.

    No realiza diagnostico definitivo; organiza decisiones en infeccion renal
    critica, obstruccion urinaria, trauma genital y onco-urologia.
    """
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")

    recommendation = UrologySupportProtocolService.build_recommendation(payload)
    run = AgentRunService.run_urology_support_workflow(
        db=db,
        care_task=task,
        protocol_input=payload.model_dump(),
        protocol_output=recommendation.model_dump(),
    )
    return CareTaskUrologySupportResponse(
        care_task_id=task.id,
        agent_run_id=run.id,
        workflow_name=run.workflow_name,
        recommendation=UrologySupportProtocolRecommendation(**recommendation.model_dump()),
    )


@router.post(
    "/{task_id}/ophthalmology/recommendation",
    response_model=CareTaskOphthalmologySupportResponse,
)
def run_care_task_ophthalmology_support(
    task_id: int,
    payload: OphthalmologySupportProtocolRequest,
    db: Session = Depends(get_db),
):
    """
    Ejecuta soporte operativo de oftalmologia para urgencias.

    No realiza diagnostico definitivo; organiza triaje vascular, riesgo pupilar,
    seguridad perioperatoria de catarata e identificacion operativa de DMAE.
    """
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")

    recommendation = OphthalmologySupportProtocolService.build_recommendation(payload)
    run = AgentRunService.run_ophthalmology_support_workflow(
        db=db,
        care_task=task,
        protocol_input=payload.model_dump(),
        protocol_output=recommendation.model_dump(),
    )
    return CareTaskOphthalmologySupportResponse(
        care_task_id=task.id,
        agent_run_id=run.id,
        workflow_name=run.workflow_name,
        recommendation=OphthalmologySupportProtocolRecommendation(
            **recommendation.model_dump()
        ),
    )


@router.post(
    "/{task_id}/immunology/recommendation",
    response_model=CareTaskImmunologySupportResponse,
)
def run_care_task_immunology_support(
    task_id: int,
    payload: ImmunologySupportProtocolRequest,
    db: Session = Depends(get_db),
):
    """
    Ejecuta soporte operativo de inmunologia para urgencias.

    No realiza diagnostico definitivo; organiza alertas de inmunodeficiencia
    humoral, defensa innata pulmonar y diferencial inmunologico.
    """
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")

    recommendation = ImmunologySupportProtocolService.build_recommendation(payload)
    run = AgentRunService.run_immunology_support_workflow(
        db=db,
        care_task=task,
        protocol_input=payload.model_dump(),
        protocol_output=recommendation.model_dump(),
    )
    return CareTaskImmunologySupportResponse(
        care_task_id=task.id,
        agent_run_id=run.id,
        workflow_name=run.workflow_name,
        recommendation=ImmunologySupportProtocolRecommendation(**recommendation.model_dump()),
    )


@router.post(
    "/{task_id}/genetic-recurrence/recommendation",
    response_model=CareTaskGeneticRecurrenceSupportResponse,
)
def run_care_task_genetic_recurrence_support(
    task_id: int,
    payload: GeneticRecurrenceSupportProtocolRequest,
    db: Session = Depends(get_db),
):
    """
    Ejecuta soporte operativo de recurrencia genetica para urgencias.

    No realiza diagnostico definitivo; organiza prioridad de mecanismos de
    recurrencia (mosaicismo germinal vs alternativas) para validacion humana.
    """
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")

    recommendation = GeneticRecurrenceSupportProtocolService.build_recommendation(payload)
    run = AgentRunService.run_genetic_recurrence_support_workflow(
        db=db,
        care_task=task,
        protocol_input=payload.model_dump(),
        protocol_output=recommendation.model_dump(),
    )
    return CareTaskGeneticRecurrenceSupportResponse(
        care_task_id=task.id,
        agent_run_id=run.id,
        workflow_name=run.workflow_name,
        recommendation=GeneticRecurrenceSupportProtocolRecommendation(
            **recommendation.model_dump()
        ),
    )


@router.post(
    "/{task_id}/gynecology-obstetrics/recommendation",
    response_model=CareTaskGynecologyObstetricsSupportResponse,
)
def run_care_task_gynecology_obstetrics_support(
    task_id: int,
    payload: GynecologyObstetricsSupportProtocolRequest,
    db: Session = Depends(get_db),
):
    """
    Ejecuta soporte operativo de ginecologia y obstetricia para urgencias.

    No realiza diagnostico definitivo; organiza riesgo oncogenetico hereditario,
    urgencias del embarazo y bloqueos de seguridad terapeutica.
    """
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")

    recommendation = GynecologyObstetricsSupportProtocolService.build_recommendation(payload)
    run = AgentRunService.run_gynecology_obstetrics_support_workflow(
        db=db,
        care_task=task,
        protocol_input=payload.model_dump(),
        protocol_output=recommendation.model_dump(),
    )
    return CareTaskGynecologyObstetricsSupportResponse(
        care_task_id=task.id,
        agent_run_id=run.id,
        workflow_name=run.workflow_name,
        recommendation=GynecologyObstetricsSupportProtocolRecommendation(
            **recommendation.model_dump()
        ),
    )


@router.post(
    "/{task_id}/pediatrics-neonatology/recommendation",
    response_model=CareTaskPediatricsNeonatologySupportResponse,
)
def run_care_task_pediatrics_neonatology_support(
    task_id: int,
    payload: PediatricsNeonatologySupportProtocolRequest,
    db: Session = Depends(get_db),
):
    """
    Ejecuta soporte operativo de pediatria y neonatologia para urgencias.

    No realiza diagnostico definitivo; organiza riesgo infeccioso exantematico,
    soporte neonatal inicial y alertas de urgencia pediatrica.
    """
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")

    recommendation = PediatricsNeonatologySupportProtocolService.build_recommendation(
        payload
    )
    run = AgentRunService.run_pediatrics_neonatology_support_workflow(
        db=db,
        care_task=task,
        protocol_input=payload.model_dump(),
        protocol_output=recommendation.model_dump(),
    )
    return CareTaskPediatricsNeonatologySupportResponse(
        care_task_id=task.id,
        agent_run_id=run.id,
        workflow_name=run.workflow_name,
        recommendation=PediatricsNeonatologySupportProtocolRecommendation(
            **recommendation.model_dump()
        ),
    )


@router.post(
    "/{task_id}/epidemiology/recommendation",
    response_model=CareTaskEpidemiologySupportResponse,
)
def run_care_task_epidemiology_support(
    task_id: int,
    payload: EpidemiologySupportProtocolRequest,
    db: Session = Depends(get_db),
):
    """
    Ejecuta soporte operativo de epidemiologia clinica aplicada en urgencias.

    No realiza diagnostico ni sustituye analisis metodologico formal;
    organiza metricas de riesgo, NNT, inferencia causal y evaluacion economica.
    """
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")

    recommendation = EpidemiologySupportProtocolService.build_recommendation(payload)
    run = AgentRunService.run_epidemiology_support_workflow(
        db=db,
        care_task=task,
        protocol_input=payload.model_dump(),
        protocol_output=recommendation.model_dump(),
    )
    return CareTaskEpidemiologySupportResponse(
        care_task_id=task.id,
        agent_run_id=run.id,
        workflow_name=run.workflow_name,
        recommendation=EpidemiologySupportProtocolRecommendation(
            **recommendation.model_dump()
        ),
    )


@router.post(
    "/{task_id}/anisakis/recommendation",
    response_model=CareTaskAnisakisSupportResponse,
)
def run_care_task_anisakis_support(
    task_id: int,
    payload: AnisakisSupportProtocolRequest,
    db: Session = Depends(get_db),
):
    """
    Ejecuta soporte operativo para sospecha de reaccion por Anisakis.

    No realiza diagnostico definitivo; prioriza deteccion de fenotipo alergico
    y medidas preventivas estructuradas al alta.
    """
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")

    recommendation = AnisakisSupportProtocolService.build_recommendation(payload)
    run = AgentRunService.run_anisakis_support_workflow(
        db=db,
        care_task=task,
        protocol_input=payload.model_dump(),
        protocol_output=recommendation.model_dump(),
    )
    return CareTaskAnisakisSupportResponse(
        care_task_id=task.id,
        agent_run_id=run.id,
        workflow_name=run.workflow_name,
        recommendation=AnisakisSupportProtocolRecommendation(**recommendation.model_dump()),
    )


@router.post(
    "/{task_id}/medicolegal/recommendation",
    response_model=CareTaskMedicolegalOpsResponse,
)
def run_care_task_medicolegal_ops(
    task_id: int,
    payload: MedicolegalOpsRequest,
    db: Session = Depends(get_db),
):
    """
    Ejecuta soporte operativo medico-legal para urgencias.

    No sustituye asesoria juridica formal; ordena alertas, checklist y
    documentos obligatorios para validacion humana.
    """
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")

    recommendation = MedicolegalOpsService.build_recommendation(payload)
    run = AgentRunService.run_medicolegal_ops_workflow(
        db=db,
        care_task=task,
        protocol_input=payload.model_dump(),
        protocol_output=recommendation.model_dump(),
    )
    return CareTaskMedicolegalOpsResponse(
        care_task_id=task.id,
        agent_run_id=run.id,
        workflow_name=run.workflow_name,
        recommendation=MedicolegalOpsRecommendation(**recommendation.model_dump()),
    )


@router.post("/{task_id}/medicolegal/audit", response_model=CareTaskMedicolegalAuditResponse)
def create_care_task_medicolegal_audit(
    task_id: int,
    payload: CareTaskMedicolegalAuditRequest,
    db: Session = Depends(get_db),
):
    """Registra auditoria de calidad para soporte medico-legal (IA vs humano)."""
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")

    try:
        audit = CareTaskService.create_or_update_medicolegal_audit(
            db=db,
            task_id=task_id,
            payload=payload,
        )
    except ValueError as exc:
        message = str(exc)
        if "no encontrada" in message:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message) from exc
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message) from exc

    return CareTaskMedicolegalAuditResponse(
        audit_id=audit.id,
        care_task_id=audit.care_task_id,
        agent_run_id=audit.agent_run_id,
        ai_legal_risk_level=audit.ai_legal_risk_level,
        human_validated_legal_risk_level=audit.human_validated_legal_risk_level,
        classification=audit.classification,
        ai_consent_required=audit.ai_consent_required,
        human_consent_required=audit.human_consent_required,
        ai_judicial_notification_required=audit.ai_judicial_notification_required,
        human_judicial_notification_required=audit.human_judicial_notification_required,
        ai_chain_of_custody_required=audit.ai_chain_of_custody_required,
        human_chain_of_custody_required=audit.human_chain_of_custody_required,
        reviewer_note=audit.reviewer_note,
        reviewed_by=audit.reviewed_by,
        created_at=audit.created_at,
        updated_at=audit.updated_at,
    )


@router.get("/{task_id}/medicolegal/audit", response_model=list[CareTaskMedicolegalAuditResponse])
def list_care_task_medicolegal_audits(
    task_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Lista auditorias medico-legales de un CareTask para revision historica."""
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")

    audits = CareTaskService.list_medicolegal_audits(db=db, task_id=task_id, limit=limit)
    return [
        CareTaskMedicolegalAuditResponse(
            audit_id=item.id,
            care_task_id=item.care_task_id,
            agent_run_id=item.agent_run_id,
            ai_legal_risk_level=item.ai_legal_risk_level,
            human_validated_legal_risk_level=item.human_validated_legal_risk_level,
            classification=item.classification,
            ai_consent_required=item.ai_consent_required,
            human_consent_required=item.human_consent_required,
            ai_judicial_notification_required=item.ai_judicial_notification_required,
            human_judicial_notification_required=item.human_judicial_notification_required,
            ai_chain_of_custody_required=item.ai_chain_of_custody_required,
            human_chain_of_custody_required=item.human_chain_of_custody_required,
            reviewer_note=item.reviewer_note,
            reviewed_by=item.reviewed_by,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
        for item in audits
    ]


@router.get(
    "/{task_id}/medicolegal/audit/summary",
    response_model=CareTaskMedicolegalAuditSummaryResponse,
)
def get_care_task_medicolegal_audit_summary(task_id: int, db: Session = Depends(get_db)):
    """Devuelve resumen agregado de calidad medico-legal para un CareTask."""
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")
    summary = CareTaskService.get_medicolegal_audit_summary(db=db, task_id=task_id)
    return CareTaskMedicolegalAuditSummaryResponse(**summary)


@router.post(
    "/{task_id}/sepsis/recommendation",
    response_model=CareTaskSepsisProtocolResponse,
)
def run_care_task_sepsis_protocol(
    task_id: int,
    payload: SepsisProtocolRequest,
    db: Session = Depends(get_db),
):
    """
    Ejecuta soporte operativo temprano para sepsis en urgencias.

    No realiza diagnostico definitivo; organiza bundle inicial y escalado
    para validacion clinica humana.
    """
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")

    recommendation = SepsisProtocolService.build_recommendation(payload)
    run = AgentRunService.run_sepsis_protocol_workflow(
        db=db,
        care_task=task,
        protocol_input=payload.model_dump(),
        protocol_output=recommendation.model_dump(),
    )
    return CareTaskSepsisProtocolResponse(
        care_task_id=task.id,
        agent_run_id=run.id,
        workflow_name=run.workflow_name,
        recommendation=SepsisProtocolRecommendation(**recommendation.model_dump()),
    )


@router.post(
    "/{task_id}/resuscitation/recommendation",
    response_model=CareTaskResuscitationProtocolResponse,
)
def run_care_task_resuscitation_support(
    task_id: int,
    payload: ResuscitationProtocolRequest,
    db: Session = Depends(get_db),
):
    """
    Ejecuta soporte operativo de reanimacion y soporte vital.

    No realiza diagnostico definitivo ni sustituye ACLS/BLS institucional;
    organiza acciones operativas para validacion clinica humana inmediata.
    """
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")

    recommendation = ResuscitationProtocolService.build_recommendation(payload)
    run = AgentRunService.run_resuscitation_protocol_workflow(
        db=db,
        care_task=task,
        protocol_input=payload.model_dump(),
        protocol_output=recommendation.model_dump(),
    )
    return CareTaskResuscitationProtocolResponse(
        care_task_id=task.id,
        agent_run_id=run.id,
        workflow_name=run.workflow_name,
        recommendation=ResuscitationProtocolRecommendation(**recommendation.model_dump()),
    )


@router.post("/{task_id}/resuscitation/audit", response_model=CareTaskResuscitationAuditResponse)
def create_care_task_resuscitation_audit(
    task_id: int,
    payload: CareTaskResuscitationAuditRequest,
    db: Session = Depends(get_db),
):
    """Registra auditoria de calidad para soporte de reanimacion (IA vs humano)."""
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")

    try:
        audit = CareTaskService.create_or_update_resuscitation_audit(
            db=db,
            task_id=task_id,
            payload=payload,
        )
    except ValueError as exc:
        message = str(exc)
        if "no encontrada" in message:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message) from exc
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message) from exc

    return CareTaskResuscitationAuditResponse(
        audit_id=audit.id,
        care_task_id=audit.care_task_id,
        agent_run_id=audit.agent_run_id,
        ai_severity_level=audit.ai_severity_level,
        human_validated_severity_level=audit.human_validated_severity_level,
        classification=audit.classification,
        ai_shock_recommended=audit.ai_shock_recommended,
        human_shock_recommended=audit.human_shock_recommended,
        ai_reversible_causes_required=audit.ai_reversible_causes_required,
        human_reversible_causes_completed=audit.human_reversible_causes_completed,
        ai_airway_plan_adequate=audit.ai_airway_plan_adequate,
        human_airway_plan_adequate=audit.human_airway_plan_adequate,
        reviewer_note=audit.reviewer_note,
        reviewed_by=audit.reviewed_by,
        created_at=audit.created_at,
        updated_at=audit.updated_at,
    )


@router.get(
    "/{task_id}/resuscitation/audit",
    response_model=list[CareTaskResuscitationAuditResponse],
)
def list_care_task_resuscitation_audits(
    task_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Lista auditorias de reanimacion por CareTask para revision historica."""
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")

    audits = CareTaskService.list_resuscitation_audits(db=db, task_id=task_id, limit=limit)
    return [
        CareTaskResuscitationAuditResponse(
            audit_id=item.id,
            care_task_id=item.care_task_id,
            agent_run_id=item.agent_run_id,
            ai_severity_level=item.ai_severity_level,
            human_validated_severity_level=item.human_validated_severity_level,
            classification=item.classification,
            ai_shock_recommended=item.ai_shock_recommended,
            human_shock_recommended=item.human_shock_recommended,
            ai_reversible_causes_required=item.ai_reversible_causes_required,
            human_reversible_causes_completed=item.human_reversible_causes_completed,
            ai_airway_plan_adequate=item.ai_airway_plan_adequate,
            human_airway_plan_adequate=item.human_airway_plan_adequate,
            reviewer_note=item.reviewer_note,
            reviewed_by=item.reviewed_by,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
        for item in audits
    ]


@router.get(
    "/{task_id}/resuscitation/audit/summary",
    response_model=CareTaskResuscitationAuditSummaryResponse,
)
def get_care_task_resuscitation_audit_summary(task_id: int, db: Session = Depends(get_db)):
    """Devuelve resumen agregado de calidad de reanimacion para un CareTask."""
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")
    summary = CareTaskService.get_resuscitation_audit_summary(db=db, task_id=task_id)
    return CareTaskResuscitationAuditSummaryResponse(**summary)


@router.post(
    "/{task_id}/scasest/recommendation",
    response_model=CareTaskScasestProtocolResponse,
)
def run_care_task_scasest_protocol(
    task_id: int,
    payload: ScasestProtocolRequest,
    db: Session = Depends(get_db),
):
    """
    Ejecuta soporte operativo inicial para sospecha de SCASEST en urgencias.

    No realiza diagnostico definitivo; organiza pruebas, tratamiento temprano
    y escalado para validacion clinica humana.
    """
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")

    recommendation = ScasestProtocolService.build_recommendation(payload)
    run = AgentRunService.run_scasest_protocol_workflow(
        db=db,
        care_task=task,
        protocol_input=payload.model_dump(),
        protocol_output=recommendation.model_dump(),
    )
    return CareTaskScasestProtocolResponse(
        care_task_id=task.id,
        agent_run_id=run.id,
        workflow_name=run.workflow_name,
        recommendation=ScasestProtocolRecommendation(**recommendation.model_dump()),
    )


@router.post("/{task_id}/scasest/audit", response_model=CareTaskScasestAuditResponse)
def create_care_task_scasest_audit(
    task_id: int,
    payload: CareTaskScasestAuditRequest,
    db: Session = Depends(get_db),
):
    """Registra auditoria de calidad para soporte SCASEST (IA vs humano)."""
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")

    try:
        audit = CareTaskService.create_or_update_scasest_audit(
            db=db,
            task_id=task_id,
            payload=payload,
        )
    except ValueError as exc:
        message = str(exc)
        if "no encontrada" in message:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message) from exc
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message) from exc

    return CareTaskScasestAuditResponse(
        audit_id=audit.id,
        care_task_id=audit.care_task_id,
        agent_run_id=audit.agent_run_id,
        ai_high_risk_scasest=audit.ai_high_risk_scasest,
        human_validated_high_risk_scasest=audit.human_validated_high_risk_scasest,
        classification=audit.classification,
        ai_escalation_required=audit.ai_escalation_required,
        human_escalation_required=audit.human_escalation_required,
        ai_immediate_antiischemic_strategy=audit.ai_immediate_antiischemic_strategy,
        human_immediate_antiischemic_strategy=audit.human_immediate_antiischemic_strategy,
        reviewer_note=audit.reviewer_note,
        reviewed_by=audit.reviewed_by,
        created_at=audit.created_at,
        updated_at=audit.updated_at,
    )


@router.get("/{task_id}/scasest/audit", response_model=list[CareTaskScasestAuditResponse])
def list_care_task_scasest_audits(
    task_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Lista auditorias SCASEST de un CareTask para revision historica."""
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")

    audits = CareTaskService.list_scasest_audits(db=db, task_id=task_id, limit=limit)
    return [
        CareTaskScasestAuditResponse(
            audit_id=item.id,
            care_task_id=item.care_task_id,
            agent_run_id=item.agent_run_id,
            ai_high_risk_scasest=item.ai_high_risk_scasest,
            human_validated_high_risk_scasest=item.human_validated_high_risk_scasest,
            classification=item.classification,
            ai_escalation_required=item.ai_escalation_required,
            human_escalation_required=item.human_escalation_required,
            ai_immediate_antiischemic_strategy=item.ai_immediate_antiischemic_strategy,
            human_immediate_antiischemic_strategy=item.human_immediate_antiischemic_strategy,
            reviewer_note=item.reviewer_note,
            reviewed_by=item.reviewed_by,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
        for item in audits
    ]


@router.get(
    "/{task_id}/scasest/audit/summary",
    response_model=CareTaskScasestAuditSummaryResponse,
)
def get_care_task_scasest_audit_summary(task_id: int, db: Session = Depends(get_db)):
    """Devuelve resumen agregado de calidad SCASEST para un CareTask."""
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")
    summary = CareTaskService.get_scasest_audit_summary(db=db, task_id=task_id)
    return CareTaskScasestAuditSummaryResponse(**summary)


@router.post(
    "/{task_id}/cardio-risk/recommendation",
    response_model=CareTaskCardioRiskProtocolResponse,
)
def run_care_task_cardio_risk_support(
    task_id: int,
    payload: CardioRiskProtocolRequest,
    db: Session = Depends(get_db),
):
    """
    Ejecuta soporte operativo inicial de riesgo cardiovascular.

    No realiza diagnostico definitivo; ordena riesgo, objetivos lipidemicos
    y acciones iniciales para validacion clinica humana.
    """
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")

    recommendation = CardioRiskSupportService.build_recommendation(payload)
    run = AgentRunService.run_cardio_risk_support_workflow(
        db=db,
        care_task=task,
        protocol_input=payload.model_dump(),
        protocol_output=recommendation.model_dump(),
    )
    return CareTaskCardioRiskProtocolResponse(
        care_task_id=task.id,
        agent_run_id=run.id,
        workflow_name=run.workflow_name,
        recommendation=CardioRiskProtocolRecommendation(**recommendation.model_dump()),
    )


@router.post("/{task_id}/cardio-risk/audit", response_model=CareTaskCardioRiskAuditResponse)
def create_care_task_cardio_risk_audit(
    task_id: int,
    payload: CareTaskCardioRiskAuditRequest,
    db: Session = Depends(get_db),
):
    """Registra auditoria de calidad para soporte cardiovascular (IA vs humano)."""
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")

    try:
        audit = CareTaskService.create_or_update_cardio_risk_audit(
            db=db,
            task_id=task_id,
            payload=payload,
        )
    except ValueError as exc:
        message = str(exc)
        if "no encontrada" in message:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message) from exc
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message) from exc

    return CareTaskCardioRiskAuditResponse(
        audit_id=audit.id,
        care_task_id=audit.care_task_id,
        agent_run_id=audit.agent_run_id,
        ai_risk_level=audit.ai_risk_level,
        human_validated_risk_level=audit.human_validated_risk_level,
        classification=audit.classification,
        ai_non_hdl_target_required=audit.ai_non_hdl_target_required,
        human_non_hdl_target_required=audit.human_non_hdl_target_required,
        ai_pharmacologic_strategy_suggested=audit.ai_pharmacologic_strategy_suggested,
        human_pharmacologic_strategy_suggested=audit.human_pharmacologic_strategy_suggested,
        ai_intensive_lifestyle_required=audit.ai_intensive_lifestyle_required,
        human_intensive_lifestyle_required=audit.human_intensive_lifestyle_required,
        reviewer_note=audit.reviewer_note,
        reviewed_by=audit.reviewed_by,
        created_at=audit.created_at,
        updated_at=audit.updated_at,
    )


@router.get("/{task_id}/cardio-risk/audit", response_model=list[CareTaskCardioRiskAuditResponse])
def list_care_task_cardio_risk_audits(
    task_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Lista auditorias cardiovasculares de un CareTask para revision historica."""
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")

    audits = CareTaskService.list_cardio_risk_audits(db=db, task_id=task_id, limit=limit)
    return [
        CareTaskCardioRiskAuditResponse(
            audit_id=item.id,
            care_task_id=item.care_task_id,
            agent_run_id=item.agent_run_id,
            ai_risk_level=item.ai_risk_level,
            human_validated_risk_level=item.human_validated_risk_level,
            classification=item.classification,
            ai_non_hdl_target_required=item.ai_non_hdl_target_required,
            human_non_hdl_target_required=item.human_non_hdl_target_required,
            ai_pharmacologic_strategy_suggested=item.ai_pharmacologic_strategy_suggested,
            human_pharmacologic_strategy_suggested=item.human_pharmacologic_strategy_suggested,
            ai_intensive_lifestyle_required=item.ai_intensive_lifestyle_required,
            human_intensive_lifestyle_required=item.human_intensive_lifestyle_required,
            reviewer_note=item.reviewer_note,
            reviewed_by=item.reviewed_by,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
        for item in audits
    ]


@router.get(
    "/{task_id}/cardio-risk/audit/summary",
    response_model=CareTaskCardioRiskAuditSummaryResponse,
)
def get_care_task_cardio_risk_audit_summary(task_id: int, db: Session = Depends(get_db)):
    """Devuelve resumen agregado de calidad cardiovascular para un CareTask."""
    task = CareTaskService.get_care_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTask no encontrado")
    summary = CareTaskService.get_cardio_risk_audit_summary(db=db, task_id=task_id)
    return CareTaskCardioRiskAuditSummaryResponse(**summary)
