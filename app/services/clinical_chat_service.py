"""
Servicio de chat clinico-operativo.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.parse import quote_plus, urlparse
from urllib.request import Request, urlopen
from uuid import uuid4

from sqlalchemy.orm import Session

from app.agents.session_tool_result_guard import SessionToolResultGuard
from app.agents.session_write_lock import SessionWriteLock
from app.agents.tool_policy_pipeline import ToolPolicyContext, ToolPolicyPipeline
from app.core.config import settings
from app.models.care_task import CareTask
from app.models.care_task_chat_message import CareTaskChatMessage
from app.models.clinical_knowledge_source import ClinicalKnowledgeSource
from app.models.user import User
from app.schemas.clinical_chat import CareTaskClinicalChatMessageRequest
from app.schemas.critical_ops_protocol import CriticalOpsProtocolRequest
from app.schemas.scasest_protocol import ScasestProtocolRequest
from app.schemas.sepsis_protocol import SepsisProtocolRequest
from app.security.audit import audit_chat_security
from app.security.dangerous_tools import assess_tool_risk
from app.security.external_content import ExternalContentSecurity
from app.services.agent_run_service import AgentRunService
from app.services.clinical_decision_psychology_service import (
    ClinicalDecisionPsychologyService,
)
from app.services.clinical_flat_clustering_service import ClinicalFlatClusteringService
from app.services.clinical_hierarchical_clustering_service import (
    ClinicalHierarchicalClusteringService,
)
from app.services.clinical_logic_engine_service import ClinicalLogicEngineService
from app.services.clinical_math_inference_service import ClinicalMathInferenceService
from app.services.clinical_naive_bayes_service import ClinicalNaiveBayesService
from app.services.clinical_protocol_contracts_service import ClinicalProtocolContractsService
from app.services.clinical_risk_pipeline_service import ClinicalRiskPipelineService
from app.services.clinical_svm_domain_service import ClinicalSVMDomainService
from app.services.clinical_svm_triage_service import ClinicalSVMTriageService
from app.services.clinical_vector_classification_service import ClinicalVectorClassificationService
from app.services.critical_ops_protocol_service import CriticalOpsProtocolService
from app.services.diagnostic_interrogatory_service import DiagnosticInterrogatoryService
from app.services.knowledge_source_service import KnowledgeSourceService
from app.services.llm_chat_provider import LLMChatProvider
from app.services.nemo_guardrails_service import NeMoGuardrailsService
from app.services.rag_orchestrator import RAGOrchestrator
from app.services.scasest_protocol_service import ScasestProtocolService
from app.services.sepsis_protocol_service import SepsisProtocolService
from app.services.web_link_analysis_service import WebLinkAnalysisService


class ClinicalChatService:
    """Motor de chat operativo con memoria incremental y trazabilidad."""

    _DOMAIN_VARIANCE_THRESHOLDS: dict[str, float] = {
        "oncology": 0.20,
        "nephrology": 0.22,
        "gynecology_obstetrics": 0.22,
        "pediatrics_neonatology": 0.20,
        "critical_ops": 0.24,
    }

    _DOMAIN_CATALOG: list[dict[str, object]] = [
        {
            "key": "critical_ops",
            "label": "Operativa critica transversal",
            "endpoint": "/api/v1/care-tasks/{task_id}/critical-ops/recommendation",
            "summary": "SLA criticos, oxigenoterapia y red flags.",
            "keywords": ["sla", "ecg", "triaje", "shock", "bipap", "cpap"],
        },
        {
            "key": "sepsis",
            "label": "Sepsis",
            "endpoint": "/api/v1/care-tasks/{task_id}/sepsis/recommendation",
            "summary": "Bundle de sepsis y escalado hemodinamico.",
            "keywords": ["sepsis", "lactato", "qsofa", "noradrenalina"],
        },
        {
            "key": "scasest",
            "label": "SCASEST",
            "endpoint": "/api/v1/care-tasks/{task_id}/scasest/recommendation",
            "summary": "Riesgo SCASEST y escalado cardiologico.",
            "keywords": [
                "scasest",
                "troponina",
                "grace",
                "angina",
                "dolor toracico",
                "dolor de pecho",
                "dolor en el pecho",
                "dolor precordial",
                "pecho",
                "opresion toracica",
                "infarto",
                "isquemia",
                "ecg",
            ],
        },
        {
            "key": "resuscitation",
            "label": "Reanimacion y soporte vital",
            "endpoint": "/api/v1/care-tasks/{task_id}/resuscitation/recommendation",
            "summary": "BLS/ACLS, via aerea y ritmos.",
            "keywords": ["rcp", "acls", "desfibrilacion", "cardioversion", "rosc"],
        },
        {
            "key": "medicolegal",
            "label": "Medico-legal",
            "endpoint": "/api/v1/care-tasks/{task_id}/medicolegal/recommendation",
            "summary": "Consentimiento, custodia y bioetica.",
            "keywords": ["consentimiento", "custodia", "bioetica", "menor", "transfusion"],
        },
        {
            "key": "neurology",
            "label": "Neurologia",
            "endpoint": "/api/v1/care-tasks/{task_id}/neurology/recommendation",
            "summary": "Codigo ictus y diferenciales neurocriticos.",
            "keywords": ["ictus", "hsa", "aspects", "trombectomia", "miastenia"],
        },
        {
            "key": "pediatrics_neonatology",
            "label": "Pediatria y neonatologia",
            "endpoint": "/api/v1/care-tasks/{task_id}/pediatrics-neonatology/recommendation",
            "summary": "Urgencias pediatricas/neonatales, aislamiento y seguridad neonatal.",
            "keywords": [
                "pediatria",
                "pediatrico",
                "neonat",
                "lactante",
                "nino",
                "nina",
                "sarampion",
                "tosferina",
                "apgar",
                "invaginacion",
            ],
        },
        {
            "key": "oncology",
            "label": "Oncologia",
            "endpoint": "/api/v1/care-tasks/{task_id}/oncology/recommendation",
            "summary": "Urgencias oncologicas, irAEs, neutropenia febril y seguridad terapeutica.",
            "keywords": [
                "oncologia",
                "oncologico",
                "cancer",
                "tumor",
                "metast",
                "her2",
                "neutropenia",
                "quimioterapia",
                "inmunoterapia",
            ],
        },
        {
            "key": "pneumology",
            "label": "Neumologia",
            "endpoint": "/api/v1/care-tasks/{task_id}/pneumology/recommendation",
            "summary": "Insuficiencia respiratoria, soporte ventilatorio y escalado pulmonar.",
            "keywords": [
                "neumologia",
                "epoc",
                "asma",
                "bronquiolitis",
                "hipoxemia",
                "respiratoria",
            ],
        },
        {
            "key": "trauma",
            "label": "Trauma",
            "endpoint": "/api/v1/care-tasks/{task_id}/trauma/recommendation",
            "summary": "Trauma mayor, via aerea critica y riesgos sistemicos.",
            "keywords": [
                "trauma",
                "politrauma",
                "hemorragia",
                "fractura",
                "glasgow",
                "toracico",
                "rodilla",
                "dolor de rodilla",
                "esguince",
                "contusion",
                "musculoesqueletico",
            ],
        },
        {
            "key": "gynecology_obstetrics",
            "label": "Ginecologia y obstetricia",
            "endpoint": "/api/v1/care-tasks/{task_id}/gynecology-obstetrics/recommendation",
            "summary": (
                "Urgencias gineco-obstetricas, sangrado, hipertension gestacional "
                "y escalado materno-fetal."
            ),
            "keywords": [
                "ginecologia",
                "obstetricia",
                "gestante",
                "embarazo",
                "obstetrico",
                "obstetrica",
                "sangrado vaginal",
                "dolor pelvico",
                "beta-hcg",
                "preeclampsia",
                "eclampsia",
                "fosfenos",
            ],
        },
        {
            "key": "gastro_hepato",
            "label": "Gastro-hepato",
            "endpoint": "/api/v1/care-tasks/{task_id}/gastro-hepato/recommendation",
            "summary": "Urgencias digestivas y hepatobiliares.",
            "keywords": [
                "gastro",
                "hepato",
                "abdomen",
                "dolor abdominal",
                "estomago",
                "dolor de estomago",
                "epigastrio",
                "epigastrico",
                "nauseas",
                "vomitos",
                "pancreatitis",
                "ictericia",
                "digestivo",
            ],
        },
        {
            "key": "rheum_immuno",
            "label": "Reuma-inmuno",
            "endpoint": "/api/v1/care-tasks/{task_id}/rheum-immuno/recommendation",
            "summary": "Urgencias reumatologicas e inmunologicas.",
            "keywords": ["reuma", "autoinmune", "vasculitis", "artritis", "inmuno"],
        },
        {
            "key": "psychiatry",
            "label": "Psiquiatria",
            "endpoint": "/api/v1/care-tasks/{task_id}/psychiatry/recommendation",
            "summary": "Crisis psiquiatricas y seguridad conductual.",
            "keywords": [
                "psiquiatria",
                "psiquiatrico",
                "psiquiatrica",
                "agitado",
                "suicida",
                "psicotico",
                "ansiedad",
                "ideacion suicida",
            ],
        },
        {
            "key": "hematology",
            "label": "Hematologia",
            "endpoint": "/api/v1/care-tasks/{task_id}/hematology/recommendation",
            "summary": "Urgencias hematologicas y coagulacion.",
            "keywords": ["hematologia", "anemia", "trombosis", "coagulacion", "plaquetas"],
        },
        {
            "key": "endocrinology",
            "label": "Endocrinologia",
            "endpoint": "/api/v1/care-tasks/{task_id}/endocrinology/recommendation",
            "summary": "Urgencias endocrinas.",
            "keywords": ["endocrino", "diabetes", "hipoglucemia", "cetoacidosis", "tiroidea"],
        },
        {
            "key": "nephrology",
            "label": "Nefrologia",
            "endpoint": "/api/v1/care-tasks/{task_id}/nephrology/recommendation",
            "summary": "Urgencias renales y trastornos hidroelectroliticos.",
            "keywords": ["nefro", "renal", "creatinina", "hiperkalemia", "dialisis"],
        },
        {
            "key": "geriatrics",
            "label": "Geriatria",
            "endpoint": "/api/v1/care-tasks/{task_id}/geriatrics/recommendation",
            "summary": "Fragilidad, sindromes geriátricos y riesgo funcional.",
            "keywords": ["geriatria", "fragilidad", "anciano", "delirium", "caidas"],
        },
        {
            "key": "anesthesiology",
            "label": "Anestesiologia",
            "endpoint": "/api/v1/care-tasks/{task_id}/anesthesiology/recommendation",
            "summary": "Via aerea, sedacion y soporte perioperatorio.",
            "keywords": ["anestesia", "sedacion", "via aerea", "analgesia", "intubacion"],
        },
        {
            "key": "palliative",
            "label": "Cuidados paliativos",
            "endpoint": "/api/v1/care-tasks/{task_id}/palliative/recommendation",
            "summary": "Control sintomatico y toma de decisiones compartida.",
            "keywords": ["paliativo", "disnea refractaria", "dolor total", "sedacion paliativa"],
        },
        {
            "key": "urology",
            "label": "Urologia",
            "endpoint": "/api/v1/care-tasks/{task_id}/urology/recommendation",
            "summary": "Urgencias urologicas y complicaciones obstructivas.",
            "keywords": ["urologia", "colico renal", "retencion", "hematuria", "prostata"],
        },
        {
            "key": "ophthalmology",
            "label": "Oftalmologia",
            "endpoint": "/api/v1/care-tasks/{task_id}/ophthalmology/recommendation",
            "summary": "Urgencias oftalmologicas y perdida visual aguda.",
            "keywords": [
                "oftalmo",
                "oftalmologia",
                "ocular",
                "dolor ocular",
                "dolor de ojo",
                "dolor en el ojo",
                "ojo derecho",
                "ojo izquierdo",
                "vision",
                "ojo rojo",
                "vision borrosa",
                "disminucion visual",
                "cuerpo extrano ocular",
                "glaucoma",
                "fotofobia",
            ],
        },
        {
            "key": "immunology",
            "label": "Inmunologia",
            "endpoint": "/api/v1/care-tasks/{task_id}/immunology/recommendation",
            "summary": "Riesgos inmunologicos y reacciones severas.",
            "keywords": ["inmunologia", "anafilaxia", "inmunodeficiencia", "hipersensibilidad"],
        },
        {
            "key": "genetic_recurrence",
            "label": "Recurrencia genetica",
            "endpoint": "/api/v1/care-tasks/{task_id}/genetic-recurrence/recommendation",
            "summary": "Consejo genetico operativo en urgencias.",
            "keywords": ["genetica", "recurrencia", "antecedente familiar", "mutacion"],
        },
        {
            "key": "epidemiology",
            "label": "Epidemiologia clinica",
            "endpoint": "/api/v1/care-tasks/{task_id}/epidemiology/recommendation",
            "summary": "Control de brotes y vigilancia epidemiologica.",
            "keywords": ["epidemiologia", "brote", "vigilancia", "rastreo", "contactos"],
        },
        {
            "key": "anisakis",
            "label": "Anisakis",
            "endpoint": "/api/v1/care-tasks/{task_id}/anisakis/recommendation",
            "summary": "Sospecha de anisakiasis y manejo operativo.",
            "keywords": ["anisakis", "anisakiasis", "pescado crudo", "dolor epigastrico"],
        },
    ]
    _SPECIALTY_FALLBACK = {
        "emergency": "critical_ops",
        "emergencias": "critical_ops",
        "icu": "resuscitation",
        "cardiology": "scasest",
        "cardiologia": "scasest",
        "neurology": "neurology",
        "neurologia": "neurology",
        "oncology": "oncology",
        "oncologia": "oncology",
        "pediatrics": "pediatrics_neonatology",
        "pediatria": "pediatrics_neonatology",
        "neonatology": "pediatrics_neonatology",
        "neonatologia": "pediatrics_neonatology",
        "pneumology": "pneumology",
        "neumologia": "pneumology",
        "trauma": "trauma",
        "gynecology_obstetrics": "gynecology_obstetrics",
        "ginecologia": "gynecology_obstetrics",
        "obstetricia": "gynecology_obstetrics",
        "gastro_hepato": "gastro_hepato",
        "gastroenterologia": "gastro_hepato",
        "hepatologia": "gastro_hepato",
        "rheum_immuno": "rheum_immuno",
        "reumatologia": "rheum_immuno",
        "psychiatry": "psychiatry",
        "psiquiatria": "psychiatry",
        "hematology": "hematology",
        "hematologia": "hematology",
        "endocrinology": "endocrinology",
        "endocrinologia": "endocrinology",
        "nephrology": "nephrology",
        "nefrologia": "nephrology",
        "geriatrics": "geriatrics",
        "geriatria": "geriatrics",
        "anesthesiology": "anesthesiology",
        "anestesiologia": "anesthesiology",
        "palliative": "palliative",
        "paliativos": "palliative",
        "urology": "urology",
        "urologia": "urology",
        "ophthalmology": "ophthalmology",
        "oftalmologia": "ophthalmology",
        "oftamologia": "ophthalmology",
        "immunology": "immunology",
        "inmunologia": "immunology",
        "genetic_recurrence": "genetic_recurrence",
        "genetica": "genetic_recurrence",
        "epidemiology": "epidemiology",
        "epidemiologia": "epidemiology",
        "anisakis": "anisakis",
    }
    _DOMAIN_TO_SPECIALTY_SEARCH: dict[str, tuple[str, ...]] = {
        "critical_ops": ("critical_ops", "emergency", "emergencias", "general"),
        "sepsis": ("sepsis", "infectious", "emergency", "general"),
        "scasest": ("scasest", "cardiology", "cardiologia", "general"),
        "resuscitation": ("resuscitation", "icu", "critical_care", "emergency", "general"),
        "medicolegal": ("medicolegal", "general"),
        "neurology": ("neurology", "neurologia", "general"),
        "pediatrics_neonatology": (
            "pediatrics_neonatology",
            "pediatrics",
            "pediatria",
            "neonatology",
            "neonatologia",
            "general",
        ),
        "oncology": ("oncology", "oncologia", "general"),
        "pneumology": ("pneumology", "neumologia", "general"),
        "trauma": ("trauma", "emergency", "general"),
        "gynecology_obstetrics": (
            "gynecology_obstetrics",
            "ginecologia",
            "obstetricia",
            "general",
        ),
        "gastro_hepato": ("gastro_hepato", "gastroenterologia", "hepatologia", "general"),
        "rheum_immuno": ("rheum_immuno", "reumatologia", "inmunologia", "general"),
        "psychiatry": ("psychiatry", "psiquiatria", "general"),
        "hematology": ("hematology", "hematologia", "general"),
        "endocrinology": ("endocrinology", "endocrinologia", "general"),
        "nephrology": ("nephrology", "nefrologia", "general"),
        "geriatrics": ("geriatrics", "geriatria", "general"),
        "anesthesiology": ("anesthesiology", "anestesiologia", "general"),
        "palliative": ("palliative", "paliativos", "general"),
        "urology": ("urology", "urologia", "general"),
        "ophthalmology": ("ophthalmology", "oftalmologia", "general"),
        "immunology": ("immunology", "inmunologia", "general"),
        "genetic_recurrence": ("genetic_recurrence", "genetica", "general"),
        "epidemiology": ("epidemiology", "epidemiologia", "general"),
        "anisakis": ("anisakis", "general"),
    }
    _SPECIALTY_QUERY_HINTS: dict[str, tuple[str, ...]] = {
        "pediatrics_neonatology": (
            "pediatria",
            "pediatrico",
            "neonat",
            "lactante",
            "sarampion",
            "tosferina",
            "apgar",
            "invaginacion",
        ),
        "oncology": (
            "oncologia",
            "oncologico",
            "cancer",
            "tumor",
            "metast",
            "her2",
            "neutropenia",
            "quimioterapia",
            "inmunoterapia",
        ),
        "cardiology": (
            "scasest",
            "troponina",
            "angina",
            "grace",
            "cardiologia",
            "dolor toracico",
            "dolor de pecho",
            "dolor en el pecho",
            "pecho",
            "opresion toracica",
            "dolor precordial",
            "infarto",
        ),
        "neurology": ("ictus", "hsa", "trombectomia", "neurologia"),
        "pneumology": ("epoc", "asma", "bronquiolitis", "hipoxemia", "neumologia"),
        "trauma": (
            "trauma",
            "politrauma",
            "fractura",
            "hemorragia",
            "rodilla",
            "dolor de rodilla",
            "esguince",
            "contusion",
        ),
        "sepsis": ("sepsis", "lactato", "qsofa", "noradrenalina"),
        "resuscitation": ("rcp", "acls", "desfibrilacion", "cardioversion", "rosc"),
        "gynecology_obstetrics": (
            "ginecologia",
            "obstetricia",
            "gestante",
            "embarazo",
            "sangrado vaginal",
            "dolor pelvico",
            "beta-hcg",
            "preeclampsia",
            "eclampsia",
            "fosfenos",
            "cefalea intensa",
        ),
        "gastro_hepato": (
            "gastro",
            "hepato",
            "pancreatitis",
            "ictericia",
            "estomago",
            "dolor de estomago",
            "dolor abdominal",
            "epigastrio",
            "nauseas",
            "vomitos",
        ),
        "rheum_immuno": ("reuma", "artritis", "vasculitis", "inmuno"),
        "psychiatry": (
            "psiquiatria",
            "psiquiatrico",
            "psiquiatrica",
            "suicida",
            "psicotico",
            "agitacion",
            "ideacion suicida",
        ),
        "hematology": ("hematologia", "anemia", "trombosis", "coagulacion"),
        "endocrinology": ("endocrino", "cetoacidosis", "hipoglucemia", "tiroidea"),
        "nephrology": ("nefro", "renal", "hiperkalemia", "dialisis"),
        "geriatrics": ("geriatria", "fragilidad", "delirium", "caidas"),
        "anesthesiology": ("anestesia", "sedacion", "intubacion", "via aerea"),
        "palliative": ("paliativo", "sedacion paliativa", "dolor total"),
        "urology": ("urologia", "retencion", "colico renal", "hematuria"),
        "ophthalmology": (
            "oftalmo",
            "oftalmologia",
            "oftamologia",
            "ocular",
            "dolor ocular",
            "dolor de ojo",
            "dolor en el ojo",
            "ojo derecho",
            "ojo izquierdo",
            "ojo rojo",
            "perdida visual",
            "vision borrosa",
            "disminucion visual",
            "cuerpo extrano ocular",
            "fotofobia",
        ),
        "immunology": ("inmunologia", "anafilaxia", "inmunodeficiencia"),
        "genetic_recurrence": ("genetica", "recurrencia", "mutacion"),
        "epidemiology": ("epidemiologia", "brote", "vigilancia", "contactos"),
        "anisakis": ("anisakis", "anisakiasis", "pescado crudo"),
    }
    _DOMAIN_KNOWLEDGE_INDEX: dict[str, list[dict[str, str]]] = {
        "critical_ops": [
            {
                "source": "docs/66_motor_operativo_critico_transversal_urgencias.md",
                "title": "Motor critico transversal",
            }
        ],
        "sepsis": [{"source": "docs/47_motor_sepsis_urgencias.md", "title": "Bundle de sepsis"}],
        "scasest": [{"source": "docs/49_motor_scasest_urgencias.md", "title": "Soporte SCASEST"}],
        "resuscitation": [
            {
                "source": "docs/58_motor_reanimacion_soporte_vital_urgencias.md",
                "title": "Reanimacion avanzada",
            }
        ],
        "medicolegal": [
            {
                "source": "docs/45_motor_medico_legal_urgencias.md",
                "title": "Soporte medico-legal",
            }
        ],
        "neurology": [
            {"source": "docs/67_motor_operativo_neurologia_urgencias.md", "title": "Neurologia"}
        ],
        "pediatrics_neonatology": [
            {
                "source": "docs/86_motor_operativo_pediatria_neonatologia_urgencias.md",
                "title": "Pediatria y neonatologia",
            }
        ],
        "oncology": [
            {"source": "docs/76_motor_operativo_oncologia_urgencias.md", "title": "Oncologia"}
        ],
        "pneumology": [
            {"source": "docs/74_motor_operativo_neumologia_urgencias.md", "title": "Neumologia"}
        ],
        "trauma": [{"source": "docs/65_motor_trauma_urgencias_trimodal.md", "title": "Trauma"}],
        "gynecology_obstetrics": [
            {
                "source": "docs/85_motor_operativo_ginecologia_obstetricia_urgencias.md",
                "title": "Ginecologia y obstetricia",
            }
        ],
        "gastro_hepato": [
            {
                "source": "docs/68_motor_operativo_gastro_hepato_urgencias.md",
                "title": "Gastro-hepato",
            }
        ],
        "rheum_immuno": [
            {
                "source": "docs/69_motor_operativo_reuma_inmuno_urgencias.md",
                "title": "Reuma-inmuno",
            }
        ],
        "psychiatry": [
            {
                "source": "docs/70_motor_operativo_psiquiatria_urgencias.md",
                "title": "Psiquiatria",
            }
        ],
        "hematology": [
            {"source": "docs/71_motor_operativo_hematologia_urgencias.md", "title": "Hematologia"}
        ],
        "endocrinology": [
            {
                "source": "docs/72_motor_operativo_endocrinologia_urgencias.md",
                "title": "Endocrinologia",
            }
        ],
        "nephrology": [
            {"source": "docs/73_motor_operativo_nefrologia_urgencias.md", "title": "Nefrologia"}
        ],
        "geriatrics": [
            {
                "source": "docs/75_motor_operativo_geriatria_fragilidad_urgencias.md",
                "title": "Geriatria",
            }
        ],
        "anesthesiology": [
            {
                "source": "docs/77_motor_operativo_anestesiologia_reanimacion_urgencias.md",
                "title": "Anestesiologia",
            }
        ],
        "palliative": [
            {
                "source": "docs/78_motor_operativo_cuidados_paliativos_urgencias.md",
                "title": "Paliativos",
            }
        ],
        "urology": [
            {"source": "docs/79_motor_operativo_urologia_urgencias.md", "title": "Urologia"}
        ],
        "anisakis": [
            {"source": "docs/80_motor_operativo_anisakis_urgencias.md", "title": "Anisakis"}
        ],
        "epidemiology": [
            {
                "source": "docs/81_motor_operativo_epidemiologia_clinica_urgencias.md",
                "title": "Epidemiologia clinica",
            }
        ],
        "ophthalmology": [
            {"source": "docs/82_motor_operativo_oftalmologia_urgencias.md", "title": "Oftalmologia"}
        ],
        "immunology": [
            {"source": "docs/83_motor_operativo_inmunologia_urgencias.md", "title": "Inmunologia"}
        ],
        "genetic_recurrence": [
            {
                "source": "docs/84_motor_operativo_recurrencia_genetica_oi_urgencias.md",
                "title": "Recurrencia genetica",
            }
        ],
    }
    _FACT_UNITS_PATTERN = re.compile(
        r"\b\d+(?:[.,]\d+)?\s*(?:mmhg|mg/dl|mmol/l|lpm|%|h|horas|min|ml/kg|cmh2o|ng/ml)\b",
        flags=re.IGNORECASE,
    )
    _FACT_COMPARATOR_PATTERN = re.compile(r"(?:>=|<=|>|<)\s*\d+(?:[.,]\d+)?", flags=re.IGNORECASE)
    _TOKEN_PATTERN = re.compile(r"[a-z0-9]{3,}", flags=re.IGNORECASE)
    _CLINICAL_TERMS = [
        "sepsis",
        "shock",
        "scasest",
        "ictus",
        "hsa",
        "cpap",
        "bipap",
        "consentimiento",
        "rechaza",
        "alergia",
        "pediatria",
        "pediatrico",
        "neonatal",
        "paciente",
        "caso",
        "sospecha",
        "fiebre",
        "febril",
        "dolor",
        "disnea",
        "taquicardia",
        "urgencia",
        "urgencias",
        "oncologia",
        "cancer",
    ]
    _CLINICAL_TOOL_MODES = {"medication", "cases", "treatment", "images"}
    _NON_CLINICAL_MEMORY_PREFIXES = ("modo_respuesta:", "herramienta:")
    _FOLLOW_UP_HINTS = (
        "y ahora",
        "y si",
        "si empeora",
        "resume",
        "reformula",
        "amplia",
        "detalla",
        "que hago",
        "siguiente",
        "continuamos",
    )
    _CONTEXTUAL_REFERENCE_HINTS = (
        "eso",
        "esto",
        "esa",
        "ese",
        "aquello",
        "lo anterior",
        "la anterior",
        "el anterior",
        "mismo",
        "misma",
        "su dosis",
        "y despues",
        "y después",
    )
    _REWRITE_FOCUS_HINTS = (
        "dosis",
        "tratamiento",
        "seguimiento",
        "plan",
        "pauta",
        "criterio",
        "escalado",
        "monitorizacion",
        "monitorización",
        "contraindic",
        "ajuste",
    )
    _MEDICATION_LEXICON = {
        "ibuprofeno",
        "paracetamol",
        "amoxicilina",
        "heparina",
        "enoxaparina",
        "insulina",
        "noradrenalina",
        "adrenalina",
        "metformina",
        "omeprazol",
        "aspirina",
        "clopidogrel",
    }
    _AMBIGUOUS_QUERY_TERMS = {
        "dolor",
        "fiebre",
        "mareo",
        "vomitos",
        "vómitos",
        "malestar",
        "cansancio",
        "debilidad",
        "hinchazon",
        "hinchazón",
        "tos",
        "cefalea",
    }
    _CLARIFICATION_QUESTION_BANK: dict[str, dict[str, str]] = {
        "general": {
            "default": (
                "¿Puedes precisar edad, tiempo de evolucion, constantes (TA/FC/SatO2/Tª) "
                "y signo de alarma principal?"
            ),
            "management_plan": (
                "¿Cual es el objetivo operativo inmediato (estabilizacion, analgesia, "
                "antibioterapia, aislamiento, derivacion) y en que ventana temporal?"
            ),
            "safety_check": (
                "¿Hay alergias, contraindicaciones relevantes o tratamiento cronico que "
                "deba condicionarse en este turno?"
            ),
            "dose_lookup": (
                "¿Que farmaco concreto necesitas dosificar y con que datos clinicos "
                "(peso, funcion renal/hepatica, via, contexto)?"
            ),
        },
        "scasest": {
            "default": (
                "¿Confirmas ECG con cambios isquemicos, troponina y estado hemodinamico "
                "actual (TA/PAM, dolor persistente, SatO2)?"
            ),
        },
        "sepsis": {
            "default": (
                "¿Dispones de foco sospechado, lactato, qSOFA, TA/PAM, diuresis y "
                "si ya se tomaron hemocultivos?"
            ),
        },
        "neurology": {
            "default": (
                "¿Puedes aportar hora de inicio o ultima vez bien, NIHSS aproximado, "
                "glucemia y datos de anticoagulacion?"
            ),
        },
        "oncology": {
            "default": (
                "¿Indicas tipo de tratamiento onco reciente, neutrofilos/plaquetas, "
                "fiebre, estabilidad hemodinamica y toxicidad organica actual?"
            ),
        },
    }
    _DOMAIN_SUGGESTED_QUERIES: dict[str, tuple[str, ...]] = {
        "general": (
            "Prioriza acciones 0-10 y 10-60 minutos con datos disponibles.",
            "Que datos faltan para cerrar un plan seguro en este caso.",
            "Criterios de escalado inmediato y monitorizacion recomendada.",
        ),
        "scasest": (
            "Criterios operativos de alto riesgo en SCASEST para escalado inmediato.",
            "Checklist 0-10 minutos en dolor toracico con troponina positiva.",
            "Que pruebas y reevaluaciones priorizar en los primeros 60 minutos.",
        ),
        "sepsis": (
            "Bundle operativo de primera hora en sospecha de sepsis.",
            "Criterios de shock septico y escalado de soporte hemodinamico.",
            "Que variables vigilar para reevaluacion temprana de respuesta.",
        ),
        "neurology": (
            "Ruta operativa de codigo ictus en ventana tiempo-dependiente.",
            "Criterios de trombolisis o derivacion para trombectomia.",
            "Checklist de seguridad inicial en deficit neurologico agudo.",
        ),
        "oncology": (
            "Manejo inicial de neutropenia febril en urgencias.",
            "Senales de toxicidad onco grave y criterios de escalado.",
            "Datos minimos para plan operativo seguro en urgencia oncologica.",
        ),
    }
    _HISTORY_NQP_MAX_TURNS = 4
    _HISTORY_REWRITE_MAX_TURNS = 2
    _HISTORY_REWRITE_RECENCY_ALPHA = 0.45
    _PROMPT_INJECTION_SIGNALS = {
        "ignore previous instructions": "override_instructions",
        "ignora las instrucciones": "override_instructions_es",
        "system prompt": "system_prompt_probe",
        "developer message": "developer_prompt_probe",
        "act as": "role_escalation",
        "modo desarrollador": "developer_mode_probe",
    }
    _ROLE_TAG_PATTERN = re.compile(
        r"</?(?:system|assistant|developer|tool|instruction)[^>]*>",
        flags=re.IGNORECASE,
    )
    _QUALITY_STOPWORDS = {
        "para",
        "como",
        "esta",
        "este",
        "sobre",
        "desde",
        "entre",
        "donde",
        "cuando",
        "porque",
        "necesito",
        "quiero",
        "puedes",
        "favor",
        "caso",
        "paciente",
        "plan",
    }
    _DOMAIN_QUALITY_THRESHOLDS = {
        "sepsis": {"answer_min": 0.35, "context_min": 0.40, "grounded_min": 0.40},
        "oncology": {"answer_min": 0.35, "context_min": 0.38, "grounded_min": 0.38},
        "pediatrics_neonatology": {"answer_min": 0.36, "context_min": 0.40, "grounded_min": 0.40},
        "scasest": {"answer_min": 0.34, "context_min": 0.38, "grounded_min": 0.38},
    }
    _WEB_SPAM_TERMS = {
        "miracle",
        "cure",
        "garantia",
        "garantizado",
        "sponsor",
        "sponsored",
        "promocion",
        "promo",
        "casino",
        "crypto",
        "bet",
        "click aqui",
        "click here",
        "buy now",
        "oferta",
    }
    _WEB_DOMAIN_AUTHORITY = {
        "who.int": 1.00,
        "cdc.gov": 0.98,
        "nih.gov": 0.98,
        "pubmed.ncbi.nlm.nih.gov": 0.99,
        "scielo.org": 0.90,
        "nejm.org": 0.95,
        "thelancet.com": 0.94,
        "bmj.com": 0.93,
        "jamanetwork.com": 0.93,
        "seimc.org": 0.88,
        "semicyuc.org": 0.86,
        "semes.org": 0.86,
        "guiasalud.es": 0.84,
        "openevidence.com": 0.80,
    }
    _WEB_MINHASH_SEEDS = tuple(range(16))
    _WEB_SHINGLE_SIZE = 3
    _WEB_NEAR_DUP_SIGNATURE_THRESHOLD = 0.85
    _DOC_CHUNK_CACHE: dict[str, list[str]] = {}
    _GENERIC_CLINICAL_SPECIFICITY_MARKERS: tuple[str, ...] = (
        "diverticul",
        "hernia crural",
        "colecistect",
        "vesicula en porcelana",
        "fenobarbital",
        "colestasis",
        "incarceracion",
        "obstruccion intestinal",
        "perforacion",
    )

    @staticmethod
    def _normalize(text: str) -> str:
        normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
        return normalized.lower().strip()

    @classmethod
    def _tokenize(cls, text: str) -> set[str]:
        return {token for token in cls._TOKEN_PATTERN.findall(cls._normalize(text))}

    @classmethod
    def _quality_tokens(cls, text: str) -> set[str]:
        return {token for token in cls._tokenize(text) if token not in cls._QUALITY_STOPWORDS}

    @classmethod
    def _detect_prompt_injection_signals(cls, text: str) -> list[str]:
        normalized = cls._normalize(text)
        signals: list[str] = []
        for needle, signal in cls._PROMPT_INJECTION_SIGNALS.items():
            if needle in normalized and signal not in signals:
                signals.append(signal)
        if cls._ROLE_TAG_PATTERN.search(text):
            signals.append("role_tag_markup")
        if "[SYSTEM]" in text or "[ASSISTANT]" in text or "[DEVELOPER]" in text:
            signals.append("role_block_markup")
        if "```" in text:
            signals.append("code_fence_payload")
        return signals

    @classmethod
    def _sanitize_user_query(cls, query: str) -> tuple[str, list[str]]:
        isolation = ExternalContentSecurity.sanitize_untrusted_text(query, max_chars=4000)
        signals = cls._detect_prompt_injection_signals(query)
        for signal in isolation.signals:
            if signal not in signals:
                signals.append(signal)
        return isolation.sanitized_text, signals

    @classmethod
    def _overlap_f1(cls, left_tokens: set[str], right_tokens: set[str]) -> float:
        if not left_tokens or not right_tokens:
            return 0.0
        shared = len(left_tokens.intersection(right_tokens))
        if shared == 0:
            return 0.0
        precision = shared / len(right_tokens)
        recall = shared / len(left_tokens)
        if precision + recall == 0:
            return 0.0
        return round((2 * precision * recall) / (precision + recall), 3)

    @classmethod
    def _overlap_recall(cls, reference_tokens: set[str], candidate_tokens: set[str]) -> float:
        if not reference_tokens or not candidate_tokens:
            return 0.0
        shared = len(reference_tokens.intersection(candidate_tokens))
        if shared <= 0:
            return 0.0
        return round(shared / max(1, len(reference_tokens)), 3)

    @classmethod
    def _grounding_citation_bonus(
        cls,
        *,
        answer: str,
        knowledge_sources: list[dict[str, str]],
        web_sources: list[dict[str, str]],
    ) -> float:
        normalized_answer = cls._normalize(answer)
        if not normalized_answer:
            return 0.0
        citations_found = 0
        max_citations = 0
        for item in (knowledge_sources[:4] + web_sources[:2]):
            source = cls._normalize(str(item.get("source") or ""))
            title = cls._normalize(str(item.get("title") or ""))
            if source:
                max_citations += 1
                source_leaf = source.split("/")[-1]
                if source_leaf and source_leaf in normalized_answer:
                    citations_found += 1
                    continue
            if title:
                max_citations += 1
                if title in normalized_answer:
                    citations_found += 1
        if max_citations <= 0 or citations_found <= 0:
            return 0.0
        # Bonus pequeño, estable y acotado para no inflar métricas artificialmente.
        return round(min(0.15, citations_found / max_citations * 0.15), 3)

    @classmethod
    def _resolve_quality_thresholds(
        cls,
        matched_domains: list[str],
    ) -> dict[str, float]:
        thresholds = {
            "degraded_answer_min": 0.25,
            "degraded_grounded_min": 0.20,
            "attention_answer_min": 0.40,
            "attention_context_min": 0.35,
            "attention_grounded_min": 0.35,
        }
        for raw_domain in matched_domains or []:
            domain_key = cls._normalize(str(raw_domain or ""))
            domain_thresholds = cls._DOMAIN_QUALITY_THRESHOLDS.get(domain_key)
            if not domain_thresholds:
                continue
            thresholds["attention_answer_min"] = max(
                thresholds["attention_answer_min"],
                float(domain_thresholds["answer_min"]),
            )
            thresholds["attention_context_min"] = max(
                thresholds["attention_context_min"],
                float(domain_thresholds["context_min"]),
            )
            thresholds["attention_grounded_min"] = max(
                thresholds["attention_grounded_min"],
                float(domain_thresholds["grounded_min"]),
            )
            thresholds["degraded_answer_min"] = max(
                thresholds["degraded_answer_min"],
                float(domain_thresholds["answer_min"]) - 0.10,
            )
            thresholds["degraded_grounded_min"] = max(
                thresholds["degraded_grounded_min"],
                float(domain_thresholds["grounded_min"]) - 0.12,
            )
        return thresholds

    @classmethod
    def _build_quality_metrics(
        cls,
        *,
        query: str,
        answer: str,
        matched_domains: list[str],
        knowledge_sources: list[dict[str, str]],
        web_sources: list[dict[str, str]],
    ) -> dict[str, float | str]:
        query_tokens = cls._quality_tokens(query)
        answer_tokens = cls._quality_tokens(answer)
        context_text = " ".join(
            [
                " ".join(matched_domains),
                " ".join(
                    f"{item.get('title', '')} {item.get('snippet', '')}"
                    for item in knowledge_sources[:6]
                ),
                " ".join(
                    f"{item.get('title', '')} {item.get('snippet', '')}" for item in web_sources[:4]
                ),
            ]
        )
        context_tokens = cls._quality_tokens(context_text)
        answer_relevance = max(
            cls._overlap_f1(query_tokens, answer_tokens),
            cls._overlap_recall(query_tokens, answer_tokens),
        )
        context_relevance = max(
            cls._overlap_f1(query_tokens, context_tokens),
            cls._overlap_recall(query_tokens, context_tokens),
        )
        groundedness = max(
            cls._overlap_f1(context_tokens, answer_tokens),
            cls._overlap_recall(context_tokens, answer_tokens),
            cls._overlap_recall(answer_tokens, context_tokens),
        )
        groundedness = round(
            min(
                1.0,
                groundedness
                + cls._grounding_citation_bonus(
                    answer=answer,
                    knowledge_sources=knowledge_sources,
                    web_sources=web_sources,
                ),
            ),
            3,
        )
        thresholds = cls._resolve_quality_thresholds(matched_domains)
        quality_status = "ok"
        if (
            answer_relevance < float(thresholds["degraded_answer_min"])
            or groundedness < float(thresholds["degraded_grounded_min"])
        ):
            quality_status = "degraded"
        elif (
            answer_relevance < float(thresholds["attention_answer_min"])
            or context_relevance < float(thresholds["attention_context_min"])
            or groundedness < float(thresholds["attention_grounded_min"])
        ):
            quality_status = "attention"
        return {
            "answer_relevance": answer_relevance,
            "context_relevance": context_relevance,
            "groundedness": groundedness,
            "quality_status": quality_status,
            "quality_threshold_attention_answer_min": round(
                float(thresholds["attention_answer_min"]),
                3,
            ),
            "quality_threshold_attention_context_min": round(
                float(thresholds["attention_context_min"]),
                3,
            ),
            "quality_threshold_attention_grounded_min": round(
                float(thresholds["attention_grounded_min"]),
                3,
            ),
        }

    @classmethod
    def _build_local_evidence_context(
        cls,
        payload: CareTaskClinicalChatMessageRequest,
    ) -> tuple[list[dict[str, str]], list[str], list[str]]:
        local_sources: list[dict[str, str]] = []
        extracted_facts: list[str] = []
        modalities: set[str] = set()
        for idx, item in enumerate(payload.local_evidence[:5], start=1):
            safe_title = ExternalContentSecurity.sanitize_untrusted_text(
                item.title,
                max_chars=120,
            ).sanitized_text.strip() or f"Evidencia local {idx}"
            safe_source = ExternalContentSecurity.sanitize_untrusted_text(
                item.source or f"local_evidence:{item.modality}:{idx}",
                max_chars=260,
            ).sanitized_text.strip() or f"local_evidence:{item.modality}:{idx}"
            safe_content = ExternalContentSecurity.sanitize_untrusted_text(
                item.content or "",
                max_chars=4000,
            ).sanitized_text.strip()
            if not safe_content and item.metadata:
                safe_content = " ; ".join(
                    f"{key}:{value}" for key, value in list(item.metadata.items())[:5]
                )
            local_sources.append(
                {
                    "type": "local_evidence",
                    "title": safe_title,
                    "source": safe_source,
                    "snippet": safe_content[:280] if safe_content else "Evidencia local adjunta.",
                    "url": "",
                }
            )
            modalities.add(item.modality)
            extracted_facts.append(f"evidencia_local:{item.modality}")
        trace = [
            f"local_evidence_items={len(local_sources)}",
            "local_evidence_modalities="
            + (",".join(sorted(modalities)) if modalities else "none"),
        ]
        return local_sources, extracted_facts, trace

    @staticmethod
    def _safe_session_id(raw_session_id: str | None) -> str:
        return raw_session_id or f"chat-{uuid4().hex[:12]}"

    @classmethod
    def _domain_by_key(cls) -> dict[str, dict[str, object]]:
        return {str(item["key"]): item for item in cls._DOMAIN_CATALOG}

    @classmethod
    def _infer_specialty_from_query(cls, query: str) -> str:
        normalized_query = cls._normalize(query)
        best_specialty = ""
        best_score = 0
        for specialty, hints in cls._SPECIALTY_QUERY_HINTS.items():
            score = sum(1 for hint in hints if cls._normalize(hint) in normalized_query)
            if score > best_score:
                best_score = score
                best_specialty = specialty
        return best_specialty

    @classmethod
    def _canonicalize_specialty(cls, specialty: str) -> str:
        normalized = cls._normalize(specialty)
        if not normalized:
            return ""
        fallback = cls._SPECIALTY_FALLBACK.get(normalized)
        if fallback:
            return str(fallback)
        return normalized

    @classmethod
    def _resolve_effective_specialty(
        cls,
        *,
        payload: CareTaskClinicalChatMessageRequest,
        care_task: CareTask,
        authenticated_user: User | None,
        query: str,
    ) -> str:
        if payload.specialty_hint:
            return cls._canonicalize_specialty(payload.specialty_hint)
        inferred_specialty = cls._infer_specialty_from_query(query)
        if inferred_specialty:
            return cls._canonicalize_specialty(inferred_specialty)
        if payload.use_authenticated_specialty_mode and authenticated_user is not None:
            specialty = cls._canonicalize_specialty(authenticated_user.specialty or "")
            if specialty:
                return specialty
        # Modo neutro: no sesgar el enrutado por specialty persistida en el caso.
        return "general"

    @classmethod
    def _match_domains(
        cls,
        *,
        query: str,
        effective_specialty: str,
        max_domains: int = 3,
    ) -> list[dict[str, object]]:
        normalized_query = cls._normalize(query)
        query_tokens = cls._tokenize(normalized_query)

        def levenshtein_distance(left: str, right: str) -> int:
            if left == right:
                return 0
            if not left:
                return len(right)
            if not right:
                return len(left)
            prev = list(range(len(right) + 1))
            for row, char_left in enumerate(left, start=1):
                curr = [row]
                for col, char_right in enumerate(right, start=1):
                    insert_cost = curr[col - 1] + 1
                    delete_cost = prev[col] + 1
                    replace_cost = prev[col - 1] + (0 if char_left == char_right else 1)
                    curr.append(min(insert_cost, delete_cost, replace_cost))
                prev = curr
            return prev[-1]

        def keyword_match_score(keyword: str) -> tuple[int, bool]:
            normalized_keyword = cls._normalize(keyword)
            if not normalized_keyword:
                return 0, False
            if normalized_keyword in normalized_query:
                return 3, True
            if normalized_keyword in cls._SPECIALTY_FALLBACK:
                canonical = str(cls._SPECIALTY_FALLBACK[normalized_keyword])
                if canonical and canonical in normalized_query:
                    return 2, True
            if len(normalized_keyword) < 7:
                return 0, False
            for token in query_tokens:
                if len(token) < 7:
                    continue
                if abs(len(token) - len(normalized_keyword)) > 2:
                    continue
                if token[:4] != normalized_keyword[:4]:
                    continue
                distance = levenshtein_distance(token, normalized_keyword)
                if distance <= 1:
                    return 2, False
                if distance == 2:
                    return 1, False
            return 0, False

        scored: list[tuple[int, int, int, dict[str, object]]] = []
        for domain in cls._DOMAIN_CATALOG:
            direct_score = 0
            fuzzy_score = 0
            for keyword in domain.get("keywords", []):
                keyword_score, is_direct = keyword_match_score(str(keyword))
                if keyword_score <= 0:
                    continue
                if is_direct:
                    direct_score += keyword_score
                else:
                    fuzzy_score += keyword_score
            total_score = direct_score + fuzzy_score
            # Evita activar dominios por un match fuzzy debil aislado.
            if direct_score == 0 and fuzzy_score < 2:
                continue
            if total_score > 0:
                scored.append((direct_score, total_score, fuzzy_score, domain))
        domain_by_key = cls._domain_by_key()
        fallback_domain = domain_by_key.get("critical_ops")
        if scored:
            has_direct_match = any(item[0] > 0 for item in scored)
            if has_direct_match:
                scored = [item for item in scored if item[0] > 0]
            scored.sort(
                key=lambda item: (item[0], item[1], item[2]),
                reverse=True,
            )
            ordered = [item[3] for item in scored]
            return ordered[:max_domains]
        normalized_specialty = cls._normalize(effective_specialty)
        specialty_domain = domain_by_key.get(normalized_specialty)
        if specialty_domain is not None and normalized_specialty != "general":
            return [specialty_domain]
        return [fallback_domain] if fallback_domain is not None else []

    @classmethod
    def _apply_math_domain_rerank(
        cls,
        *,
        matched_domain_records: list[dict[str, object]],
        math_assessment: dict[str, Any],
        max_domains: int = 3,
    ) -> list[dict[str, object]]:
        if not matched_domain_records or not math_assessment.get("enabled"):
            return matched_domain_records

        top_domain = str(math_assessment.get("top_domain") or "").strip()
        top_probability = float(math_assessment.get("top_probability") or 0.0)
        uncertainty_level = str(math_assessment.get("uncertainty_level") or "high")
        if not top_domain or uncertainty_level == "high":
            return matched_domain_records

        domain_by_key = cls._domain_by_key()
        top_domain_record = domain_by_key.get(top_domain)
        if top_domain_record is None:
            return matched_domain_records

        existing_by_key = {
            str(item.get("key")): item for item in matched_domain_records if item.get("key")
        }
        ordered = list(matched_domain_records)

        # Solo reordena cuando la evidencia matematica es suficientemente fuerte.
        if top_probability >= 0.55:
            if top_domain in existing_by_key:
                ordered = [existing_by_key[top_domain]] + [
                    item for item in ordered if str(item.get("key")) != top_domain
                ]
            elif cls._can_expand_domain_set(matched_domain_records):
                ordered = [top_domain_record] + ordered

        deduplicated: list[dict[str, object]] = []
        seen: set[str] = set()
        for item in ordered:
            key = str(item.get("key") or "")
            if not key or key in seen:
                continue
            seen.add(key)
            deduplicated.append(item)

        return deduplicated[:max_domains]

    @classmethod
    def _can_expand_domain_set(cls, matched_domain_records: list[dict[str, object]]) -> bool:
        if not matched_domain_records:
            return True
        if len(matched_domain_records) == 1:
            key = str(matched_domain_records[0].get("key") or "")
            return key == "critical_ops"
        return False

    @classmethod
    def _apply_naive_bayes_domain_rerank(
        cls,
        *,
        matched_domain_records: list[dict[str, object]],
        naive_bayes_assessment: dict[str, Any],
        math_assessment: dict[str, Any],
        max_domains: int = 3,
    ) -> list[dict[str, object]]:
        if not matched_domain_records or not naive_bayes_assessment.get("enabled"):
            return matched_domain_records

        top_domain = str(naive_bayes_assessment.get("top_domain") or "").strip()
        top_probability = float(naive_bayes_assessment.get("top_probability") or 0.0)
        if not top_domain:
            return matched_domain_records
        if top_probability < float(settings.CLINICAL_CHAT_NB_MIN_CONFIDENCE):
            return matched_domain_records

        if settings.CLINICAL_CHAT_NB_RERANK_WHEN_MATH_UNCERTAIN_ONLY:
            if str(math_assessment.get("uncertainty_level") or "high") == "low":
                return matched_domain_records

        domain_by_key = cls._domain_by_key()
        top_domain_record = domain_by_key.get(top_domain)
        if top_domain_record is None:
            return matched_domain_records

        existing_by_key = {
            str(item.get("key")): item for item in matched_domain_records if item.get("key")
        }
        ordered = list(matched_domain_records)

        if top_domain in existing_by_key:
            ordered = [existing_by_key[top_domain]] + [
                item for item in ordered if str(item.get("key")) != top_domain
            ]
        elif cls._can_expand_domain_set(matched_domain_records):
            ordered = [top_domain_record] + ordered

        deduplicated: list[dict[str, object]] = []
        seen: set[str] = set()
        for item in ordered:
            key = str(item.get("key") or "")
            if not key or key in seen:
                continue
            seen.add(key)
            deduplicated.append(item)
        return deduplicated[:max_domains]

    @classmethod
    def _apply_vector_domain_rerank(
        cls,
        *,
        matched_domain_records: list[dict[str, object]],
        vector_assessment: dict[str, Any],
        math_assessment: dict[str, Any],
        max_domains: int = 3,
    ) -> list[dict[str, object]]:
        if not matched_domain_records or not vector_assessment.get("enabled"):
            return matched_domain_records

        top_domain = str(vector_assessment.get("top_domain") or "").strip()
        top_probability = float(vector_assessment.get("top_probability") or 0.0)
        if not top_domain:
            return matched_domain_records
        if top_probability < float(settings.CLINICAL_CHAT_VECTOR_MIN_CONFIDENCE):
            return matched_domain_records

        if settings.CLINICAL_CHAT_VECTOR_RERANK_WHEN_MATH_UNCERTAIN_ONLY:
            if str(math_assessment.get("uncertainty_level") or "high") == "low":
                return matched_domain_records

        domain_by_key = cls._domain_by_key()
        top_domain_record = domain_by_key.get(top_domain)
        if top_domain_record is None:
            return matched_domain_records

        existing_by_key = {
            str(item.get("key")): item for item in matched_domain_records if item.get("key")
        }
        ordered = list(matched_domain_records)

        if top_domain in existing_by_key:
            ordered = [existing_by_key[top_domain]] + [
                item for item in ordered if str(item.get("key")) != top_domain
            ]
        elif cls._can_expand_domain_set(matched_domain_records):
            ordered = [top_domain_record] + ordered

        deduplicated: list[dict[str, object]] = []
        seen: set[str] = set()
        for item in ordered:
            key = str(item.get("key") or "")
            if not key or key in seen:
                continue
            seen.add(key)
            deduplicated.append(item)
        return deduplicated[:max_domains]

    @classmethod
    def _apply_svm_domain_rerank(
        cls,
        *,
        matched_domain_records: list[dict[str, object]],
        svm_domain_assessment: dict[str, Any],
        math_assessment: dict[str, Any],
        max_domains: int = 3,
    ) -> list[dict[str, object]]:
        if not matched_domain_records or not svm_domain_assessment.get("enabled"):
            return matched_domain_records

        top_domain = str(svm_domain_assessment.get("top_domain") or "").strip()
        top_probability = float(svm_domain_assessment.get("top_probability") or 0.0)
        if not top_domain:
            return matched_domain_records
        if top_probability < float(settings.CLINICAL_CHAT_SVM_DOMAIN_MIN_CONFIDENCE):
            return matched_domain_records

        if settings.CLINICAL_CHAT_SVM_DOMAIN_RERANK_WHEN_MATH_UNCERTAIN_ONLY:
            if str(math_assessment.get("uncertainty_level") or "high") == "low":
                return matched_domain_records

        domain_by_key = cls._domain_by_key()
        top_domain_record = domain_by_key.get(top_domain)
        if top_domain_record is None:
            return matched_domain_records

        existing_by_key = {
            str(item.get("key")): item for item in matched_domain_records if item.get("key")
        }
        ordered = list(matched_domain_records)

        if top_domain in existing_by_key:
            ordered = [existing_by_key[top_domain]] + [
                item for item in ordered if str(item.get("key")) != top_domain
            ]
        elif cls._can_expand_domain_set(matched_domain_records):
            ordered = [top_domain_record] + ordered

        deduplicated: list[dict[str, object]] = []
        seen: set[str] = set()
        for item in ordered:
            key = str(item.get("key") or "")
            if not key or key in seen:
                continue
            seen.add(key)
            deduplicated.append(item)
        return deduplicated[:max_domains]

    @classmethod
    def _apply_cluster_domain_rerank(
        cls,
        *,
        matched_domain_records: list[dict[str, object]],
        cluster_assessment: dict[str, Any],
        math_assessment: dict[str, Any],
        max_domains: int = 3,
    ) -> list[dict[str, object]]:
        if not matched_domain_records or not cluster_assessment.get("enabled"):
            return matched_domain_records

        top_confidence = float(cluster_assessment.get("top_confidence") or 0.0)
        if top_confidence < float(settings.CLINICAL_CHAT_CLUSTER_MIN_CONFIDENCE):
            return matched_domain_records

        if settings.CLINICAL_CHAT_CLUSTER_RERANK_WHEN_MATH_UNCERTAIN_ONLY:
            if str(math_assessment.get("uncertainty_level") or "high") == "low":
                return matched_domain_records

        candidate_domains = [
            str(item).strip()
            for item in list(cluster_assessment.get("candidate_domains") or [])
            if str(item).strip()
        ]
        if not candidate_domains:
            return matched_domain_records

        domain_by_key = cls._domain_by_key()
        existing_by_key = {
            str(item.get("key")): item for item in matched_domain_records if item.get("key")
        }
        ordered: list[dict[str, object]] = []
        allow_expand = cls._can_expand_domain_set(matched_domain_records)
        for domain_key in candidate_domains:
            if domain_key in existing_by_key:
                ordered.append(existing_by_key[domain_key])
                continue
            if not allow_expand:
                continue
            domain_record = domain_by_key.get(domain_key)
            if domain_record is not None:
                ordered.append(domain_record)
        ordered.extend(matched_domain_records)

        deduplicated: list[dict[str, object]] = []
        seen: set[str] = set()
        for item in ordered:
            key = str(item.get("key") or "")
            if not key or key in seen:
                continue
            seen.add(key)
            deduplicated.append(item)
        return deduplicated[:max_domains]

    @classmethod
    def _apply_hcluster_domain_rerank(
        cls,
        *,
        matched_domain_records: list[dict[str, object]],
        hcluster_assessment: dict[str, Any],
        math_assessment: dict[str, Any],
        max_domains: int = 3,
    ) -> list[dict[str, object]]:
        if not matched_domain_records or not hcluster_assessment.get("enabled"):
            return matched_domain_records

        top_confidence = float(hcluster_assessment.get("top_confidence") or 0.0)
        if top_confidence < float(settings.CLINICAL_CHAT_HCLUSTER_MIN_CONFIDENCE):
            return matched_domain_records

        if settings.CLINICAL_CHAT_HCLUSTER_RERANK_WHEN_MATH_UNCERTAIN_ONLY:
            if str(math_assessment.get("uncertainty_level") or "high") == "low":
                return matched_domain_records

        candidate_domains = [
            str(item).strip()
            for item in list(hcluster_assessment.get("candidate_domains") or [])
            if str(item).strip()
        ]
        if not candidate_domains:
            return matched_domain_records

        domain_by_key = cls._domain_by_key()
        existing_by_key = {
            str(item.get("key")): item for item in matched_domain_records if item.get("key")
        }
        ordered: list[dict[str, object]] = []
        allow_expand = cls._can_expand_domain_set(matched_domain_records)
        for domain_key in candidate_domains:
            if domain_key in existing_by_key:
                ordered.append(existing_by_key[domain_key])
                continue
            if not allow_expand:
                continue
            domain_record = domain_by_key.get(domain_key)
            if domain_record is not None:
                ordered.append(domain_record)
        ordered.extend(matched_domain_records)

        deduplicated: list[dict[str, object]] = []
        seen: set[str] = set()
        for item in ordered:
            key = str(item.get("key") or "")
            if not key or key in seen:
                continue
            seen.add(key)
            deduplicated.append(item)
        return deduplicated[:max_domains]

    @classmethod
    def _count_domain_keyword_hits(cls, query: str) -> int:
        normalized_query = cls._normalize(query)
        hits = 0
        for domain in cls._DOMAIN_CATALOG:
            for keyword in domain.get("keywords", []):
                if cls._normalize(str(keyword)) in normalized_query:
                    hits += 1
        return hits

    @classmethod
    def _has_clinical_signal(
        cls,
        *,
        query: str,
        extracted_facts: list[str],
        keyword_hits: int,
    ) -> bool:
        if keyword_hits > 0:
            return True
        if any(
            fact.startswith("umbral:") or fact.startswith("comparador:") for fact in extracted_facts
        ):
            return True
        if any(fact.startswith("termino:") for fact in extracted_facts):
            return True
        normalized_query = cls._normalize(query)
        return any(term in normalized_query for term in cls._CLINICAL_TERMS)

    @classmethod
    def _resolve_response_mode(
        cls,
        *,
        payload: CareTaskClinicalChatMessageRequest,
        query: str,
        extracted_facts: list[str],
        keyword_hits: int,
        tool_mode: str | None = None,
    ) -> str:
        # Modo unico de chat: no forzar el tipo de respuesta por selector de herramienta.
        # La decision se toma solo por senal clinica real en la consulta.
        if cls._has_clinical_signal(
            query=query,
            extracted_facts=extracted_facts,
            keyword_hits=keyword_hits,
        ):
            return "clinical"
        return "general"

    @classmethod
    def _extract_facts(cls, query: str) -> list[str]:
        normalized_query = cls._normalize(query)
        facts: list[str] = []
        for match in cls._FACT_UNITS_PATTERN.findall(query):
            facts.append(f"umbral:{cls._normalize(match).replace(' ', '')}")
        for match in cls._FACT_COMPARATOR_PATTERN.findall(query):
            facts.append(f"comparador:{cls._normalize(match).replace(' ', '')}")
        if "rechaza" in normalized_query:
            facts.append("decision:rechazo_tratamiento")
        if "familiar" in normalized_query or "acompan" in normalized_query:
            facts.append("contexto:acompanante_presente")
        if "consentimiento" in normalized_query:
            facts.append("legal:consentimiento_mencionado")
        if "alerg" in normalized_query:
            facts.append("seguridad:alergia_reportada")
        for term in cls._CLINICAL_TERMS:
            if term in normalized_query:
                facts.append(f"termino:{term}")
        unique_facts: list[str] = []
        for fact in facts:
            if fact not in unique_facts:
                unique_facts.append(fact)
        return unique_facts[:16]

    @classmethod
    def _filter_memory_fact(cls, fact: str) -> bool:
        normalized = cls._normalize(fact)
        return not normalized.startswith(cls._NON_CLINICAL_MEMORY_PREFIXES)

    @classmethod
    def _compose_effective_query(
        cls,
        *,
        query: str,
        recent_dialogue: list[dict[str, str]],
    ) -> tuple[str, bool]:
        normalized_query = cls._normalize(query)
        query_tokens = cls._tokenize(query)
        if not recent_dialogue:
            return query, False
        short_query = len(query_tokens) <= 8
        explicit_follow_up_hint = any(
            hint in normalized_query for hint in cls._FOLLOW_UP_HINTS
        )
        has_context_reference = any(
            hint in normalized_query for hint in cls._CONTEXTUAL_REFERENCE_HINTS
        )
        has_focus_hint = any(hint in normalized_query for hint in cls._REWRITE_FOCUS_HINTS)
        standalone_domain_hits = cls._count_domain_keyword_hits(query)
        standalone_case_markers = (
            "paciente",
            "dolor",
            "fiebre",
            "disnea",
            "cefalea",
            "vomito",
            "vomitos",
            "nausea",
            "nauseas",
            "hemorrag",
            "ocular",
        )
        standalone_clinical_case = bool(
            standalone_domain_hits > 0
            and any(marker in normalized_query for marker in standalone_case_markers)
        )
        looks_interrogative = "?" in query or query.strip().lower().startswith(
            ("que", "qué", "como", "cómo", "cual", "cuál")
        )
        is_follow_up = explicit_follow_up_hint or (
            short_query and not standalone_clinical_case
        )
        is_contextual_query = (
            is_follow_up
            or has_context_reference
            or (looks_interrogative and has_focus_hint and len(query_tokens) <= 14)
        )
        if not is_contextual_query:
            return query, False
        selected_turns = cls._select_history_turns_for_rewrite(
            query=query,
            recent_dialogue=recent_dialogue,
            max_turns=cls._HISTORY_REWRITE_MAX_TURNS,
        )
        if not selected_turns:
            return query, False
        context_seed = " | ".join(selected_turns)[:360]
        effective_query = (
            f"Contexto clinico previo: {context_seed}. "
            f"Consulta de seguimiento: {query.strip()}"
        )
        return effective_query, True

    @classmethod
    def _select_history_turns_for_rewrite(
        cls,
        *,
        query: str,
        recent_dialogue: list[dict[str, str]],
        max_turns: int,
    ) -> list[str]:
        """HAM ligero: prioriza turnos por overlap semantico + recencia + foco clinico."""
        if not recent_dialogue:
            return []
        q_tokens = cls._quality_tokens(query)
        scored_turns: list[tuple[float, str]] = []
        total = len(recent_dialogue)
        for idx, turn in enumerate(recent_dialogue):
            user_query = str(turn.get("user_query") or "").strip()
            if not user_query:
                continue
            turn_tokens = cls._quality_tokens(user_query)
            overlap = cls._overlap_recall(q_tokens, turn_tokens) if q_tokens else 0.0
            distance = max(0, (total - 1) - idx)
            recency = math.exp(-cls._HISTORY_REWRITE_RECENCY_ALPHA * distance)
            normalized_turn = cls._normalize(user_query)
            focus_bonus = (
                1.0
                if any(h in normalized_turn for h in cls._REWRITE_FOCUS_HINTS)
                else 0.0
            )
            # Score HAM (0..1+): mezcla interpretable y barata en CPU.
            score = (0.58 * overlap) + (0.32 * recency) + (0.10 * focus_bonus)
            scored_turns.append((round(score, 4), user_query))
        if not scored_turns:
            return []
        scored_turns.sort(key=lambda item: item[0], reverse=True)
        selected = [text for _, text in scored_turns[: max(1, int(max_turns))]]
        return selected

    @classmethod
    def _parse_semantic_intent(cls, query: str) -> dict[str, str]:
        """Parser semantico determinista (ligero) para slot filling clinico."""
        normalized = cls._normalize(query)
        intent = "general"
        if "dosis" in normalized or "posologia" in normalized or "posologia" in normalized:
            intent = "dose_lookup"
        elif any(term in normalized for term in ("seguimiento", "control", "reevalu")):
            intent = "follow_up_plan"
        elif any(term in normalized for term in ("contraindic", "alerg")):
            intent = "safety_check"
        elif any(term in normalized for term in ("tratamiento", "manejo", "plan")):
            intent = "management_plan"

        entity = ""
        # Regla 1: patron explicito "dosis de X"
        match = re.search(r"(?:dosis|posologia)\s+de\s+([a-z0-9\-]{3,40})", normalized)
        if match:
            entity = match.group(1).strip()
        else:
            # Regla 2: lexicon basico de farmacos frecuentes.
            for med in cls._MEDICATION_LEXICON:
                if med in normalized:
                    entity = med
                    break
        return {"intent": intent, "entity": entity}

    @classmethod
    def _resolve_dialog_state(
        cls,
        *,
        query: str,
        recent_dialogue: list[dict[str, str]],
    ) -> dict[str, str]:
        """DST ligero: consolida intencion y entidad foco para turnos multi-turno."""
        current = cls._parse_semantic_intent(query)
        if current.get("entity"):
            return current

        # Fallback: hereda entidad del historial cercano mas relevante.
        for turn in reversed(recent_dialogue[-4:]):
            parsed = cls._parse_semantic_intent(str(turn.get("user_query") or ""))
            if parsed.get("entity"):
                return {"intent": current.get("intent", "general"), "entity": parsed["entity"]}
        return current

    @classmethod
    def _assess_query_ambiguity(
        cls,
        *,
        query: str,
        parsed_intent: str,
        keyword_hits: int,
        extracted_facts: list[str],
    ) -> dict[str, Any]:
        """Clasificador heuristico liviano (CPU) para decidir clarificacion proactiva."""
        normalized_query = cls._normalize(query)
        tokens = cls._quality_tokens(query)
        token_count = len(tokens)
        shortness = max(0.0, (8.0 - float(min(token_count, 8))) / 8.0)
        has_numeric_structure = any(
            fact.startswith("umbral:") or fact.startswith("comparador:") for fact in extracted_facts
        ) or bool(re.search(r"\d", query))
        weak_domain_signal = 1.0 if keyword_hits <= 0 else 0.0
        ambiguous_hits = sum(1 for term in cls._AMBIGUOUS_QUERY_TERMS if term in normalized_query)
        ambiguity_density = min(1.0, float(ambiguous_hits) / 2.0) if ambiguous_hits else 0.0
        intent_discount = 0.18 if parsed_intent in {"management_plan", "follow_up_plan"} else 0.0

        score = (
            (0.47 * shortness)
            + (0.28 * (0.0 if has_numeric_structure else 1.0))
            + (0.20 * weak_domain_signal)
            + (0.20 * ambiguity_density)
            - intent_discount
        )
        score = max(0.0, min(1.0, score))
        should_ask = bool(
            score >= 0.62
            and token_count <= 16
            and not cls._is_social_or_discovery_query(query)
        )
        reason = "insufficient_context" if should_ask else "sufficient_context"
        return {
            "should_ask": should_ask,
            "score": round(score, 4),
            "shortness": round(shortness, 4),
            "keyword_hits": int(keyword_hits),
            "ambiguous_hits": int(ambiguous_hits),
            "reason": reason,
        }

    @classmethod
    def _pick_clarification_question(
        cls,
        *,
        domain_key: str | None,
        parsed_intent: str,
    ) -> str:
        normalized_domain = cls._normalize(domain_key or "")
        domain_bank = cls._CLARIFICATION_QUESTION_BANK.get(
            normalized_domain, cls._CLARIFICATION_QUESTION_BANK["general"]
        )
        if parsed_intent in domain_bank:
            return domain_bank[parsed_intent]
        if "default" in domain_bank:
            return str(domain_bank["default"])
        general_bank = cls._CLARIFICATION_QUESTION_BANK["general"]
        if parsed_intent in general_bank:
            return str(general_bank[parsed_intent])
        return str(general_bank["default"])

    @classmethod
    def _build_next_query_suggestions(
        cls,
        *,
        query: str,
        matched_domains: list[dict[str, object]] | list[str],
        parsed_intent: str,
        limit: int = 3,
    ) -> list[str]:
        domain_key = "general"
        if matched_domains:
            first = matched_domains[0]
            if isinstance(first, dict):
                domain_key = cls._normalize(str(first.get("key") or "general"))
            else:
                domain_key = cls._normalize(str(first))
        domain_candidates = list(cls._DOMAIN_SUGGESTED_QUERIES.get(domain_key, ()))
        generic_candidates = list(cls._DOMAIN_SUGGESTED_QUERIES["general"])
        intent_candidates: list[str] = []
        if parsed_intent == "dose_lookup":
            intent_candidates.append(
                "Incluye farmaco, peso, funcion renal/hepatica y via para ajustar dosis segura."
            )
        elif parsed_intent == "safety_check":
            intent_candidates.append(
                "Detalla alergias, contraindicaciones y tratamiento cronico relevante."
            )
        elif parsed_intent == "follow_up_plan":
            intent_candidates.append(
                "Especifica evolucion temporal y respuesta a intervenciones previas."
            )

        query_tokens = cls._quality_tokens(query)
        suggestions: list[str] = []
        seen: set[str] = set()
        for candidate in [*intent_candidates, *domain_candidates, *generic_candidates]:
            cleaned = " ".join(str(candidate).split()).strip()
            if not cleaned:
                continue
            key = cls._normalize(cleaned)
            if key in seen:
                continue
            seen.add(key)
            overlap = cls._overlap_recall(query_tokens, cls._quality_tokens(cleaned))
            if overlap >= 0.9:
                continue
            suggestions.append(cleaned)
            if len(suggestions) >= max(1, int(limit)):
                break
        return suggestions

    @staticmethod
    def _list_recent_messages(
        db: Session,
        *,
        care_task_id: int,
        session_id: str | None,
        limit: int,
    ) -> list[CareTaskChatMessage]:
        safe_limit = max(0, min(limit, 100))
        if safe_limit == 0:
            return []
        query = db.query(CareTaskChatMessage).filter(
            CareTaskChatMessage.care_task_id == care_task_id
        )
        if session_id is not None:
            query = query.filter(CareTaskChatMessage.session_id == session_id)
        return (
            query.order_by(CareTaskChatMessage.created_at.desc(), CareTaskChatMessage.id.desc())
            .limit(safe_limit)
            .all()
        )

    @staticmethod
    def _list_patient_messages(
        db: Session,
        *,
        patient_reference: str,
        limit: int,
    ) -> list[CareTaskChatMessage]:
        safe_limit = max(0, min(limit, 300))
        if safe_limit == 0:
            return []
        return (
            db.query(CareTaskChatMessage)
            .join(CareTask, CareTask.id == CareTaskChatMessage.care_task_id)
            .filter(CareTask.patient_reference == patient_reference)
            .order_by(CareTaskChatMessage.created_at.desc(), CareTaskChatMessage.id.desc())
            .limit(safe_limit)
            .all()
        )

    @staticmethod
    def list_messages(
        db: Session,
        *,
        care_task_id: int,
        session_id: str | None,
        limit: int,
    ) -> list[CareTaskChatMessage]:
        safe_limit = max(1, min(limit, 200))
        query = db.query(CareTaskChatMessage).filter(
            CareTaskChatMessage.care_task_id == care_task_id
        )
        if session_id is not None:
            query = query.filter(CareTaskChatMessage.session_id == session_id)
        return (
            query.order_by(CareTaskChatMessage.created_at.desc(), CareTaskChatMessage.id.desc())
            .limit(safe_limit)
            .all()
        )

    @classmethod
    def _build_patient_summary(
        cls,
        db: Session,
        *,
        patient_reference: str | None,
        max_messages: int,
    ) -> dict[str, Any] | None:
        if not patient_reference:
            return None
        messages = cls._list_patient_messages(
            db,
            patient_reference=patient_reference,
            limit=max_messages,
        )
        domain_counter: Counter[str] = Counter()
        fact_counter: Counter[str] = Counter()
        encounter_counter: Counter[int] = Counter()
        for message in messages:
            domain_counter.update(message.matched_domains or [])
            fact_counter.update(message.extracted_facts or [])
            encounter_counter.update([message.care_task_id])
        return {
            "patient_reference": patient_reference,
            "patient_interactions_count": len(messages),
            "patient_encounters_count": len(encounter_counter),
            "patient_top_domains": [item for item, _ in domain_counter.most_common(5)],
            "patient_top_extracted_facts": [item for item, _ in fact_counter.most_common(10)],
        }

    @classmethod
    def summarize_memory(
        cls,
        db: Session,
        *,
        care_task_id: int,
        session_id: str | None,
        limit: int = 200,
    ) -> dict[str, object]:
        messages = cls.list_messages(
            db,
            care_task_id=care_task_id,
            session_id=session_id,
            limit=limit,
        )
        domain_counter: Counter[str] = Counter()
        fact_counter: Counter[str] = Counter()
        for message in messages:
            domain_counter.update(message.matched_domains or [])
            fact_counter.update(message.extracted_facts or [])
        summary: dict[str, object] = {
            "interactions_count": len(messages),
            "top_domains": [domain for domain, _ in domain_counter.most_common(5)],
            "top_extracted_facts": [fact for fact, _ in fact_counter.most_common(10)],
            "patient_reference": None,
            "patient_interactions_count": 0,
            "patient_top_domains": [],
            "patient_top_extracted_facts": [],
        }
        care_task = db.query(CareTask).filter(CareTask.id == care_task_id).first()
        if care_task is None:
            return summary
        patient_summary = cls._build_patient_summary(
            db,
            patient_reference=care_task.patient_reference,
            max_messages=min(limit, 300),
        )
        if patient_summary is None:
            return summary
        summary["patient_reference"] = patient_summary["patient_reference"]
        summary["patient_interactions_count"] = patient_summary["patient_interactions_count"]
        summary["patient_top_domains"] = patient_summary["patient_top_domains"]
        summary["patient_top_extracted_facts"] = patient_summary["patient_top_extracted_facts"]
        return summary

    @classmethod
    def _load_doc_chunks(cls, source_path: str) -> list[str]:
        if source_path in cls._DOC_CHUNK_CACHE:
            return cls._DOC_CHUNK_CACHE[source_path]
        root = Path(__file__).resolve().parents[2]
        full_path = root / source_path
        if not full_path.exists():
            cls._DOC_CHUNK_CACHE[source_path] = []
            return []
        raw_text = full_path.read_text(encoding="utf-8", errors="ignore")
        paragraphs = re.split(r"\n\s*\n", raw_text)
        chunks: list[str] = []
        for paragraph in paragraphs:
            compact = " ".join(paragraph.split())
            if len(compact) < 40:
                continue
            chunks.append(compact[:620])
        cls._DOC_CHUNK_CACHE[source_path] = chunks[:250]
        return cls._DOC_CHUNK_CACHE[source_path]

    @classmethod
    def _build_catalog_knowledge_sources(
        cls,
        *,
        query: str,
        matched_domains: list[dict[str, object]],
        max_internal_sources: int,
    ) -> list[dict[str, str]]:
        query_tokens = cls._tokenize(query)
        normalized_query = cls._normalize(query)
        generic_operational_query = any(
            marker in normalized_query
            for marker in (
                "datos clave",
                "escalado",
                "pasos",
                "que hacer",
                "manejo",
                "acciones",
                "prioridades",
            )
        )
        ranked: list[tuple[int, dict[str, str]]] = []
        for domain in matched_domains:
            domain_key = str(domain["key"])
            for reference in cls._DOMAIN_KNOWLEDGE_INDEX.get(domain_key, []):
                source_path = reference["source"]
                best_score = 0
                best_chunk = ""
                for chunk in cls._load_doc_chunks(source_path):
                    chunk_tokens = cls._tokenize(chunk)
                    normalized_chunk = cls._normalize(chunk)
                    score = len(query_tokens.intersection(chunk_tokens))
                    if generic_operational_query:
                        operational_markers = (
                            "manejo",
                            "prioridad",
                            "prioridades",
                            "abdomen agudo",
                            "exploracion",
                            "reevaluacion",
                            "cirugia",
                            "algoritmo",
                            "escalado",
                        )
                        non_operational_markers = (
                            "validacion",
                            "riesgos pendientes",
                            "imagen y pronostico",
                            "cambios implementados",
                            "gas portal",
                            "neumatosis gastrica",
                            "courvoisier",
                            "aerobilia",
                            "triada critica",
                        )
                        score += sum(
                            2 for marker in operational_markers if marker in normalized_chunk
                        )
                        score -= sum(
                            2 for marker in non_operational_markers if marker in normalized_chunk
                        )
                        query_has_specific_marker = any(
                            marker in normalized_query
                            for marker in cls._GENERIC_CLINICAL_SPECIFICITY_MARKERS
                        )
                        if not query_has_specific_marker:
                            score -= sum(
                                3
                                for marker in cls._GENERIC_CLINICAL_SPECIFICITY_MARKERS
                                if marker in normalized_chunk
                            )
                            neutral_markers = (
                                "constantes",
                                "signos de alarma",
                                "exploracion abdominal",
                                "signos peritoneales",
                                "analitica",
                                "imagen",
                                "reevaluacion",
                                "escalado digestivo",
                                "escalado quirurgico",
                            )
                            score += sum(
                                3 for marker in neutral_markers if marker in normalized_chunk
                            )
                    if (
                        domain_key == "gastro_hepato"
                        and any(
                            token in normalized_query
                            for token in ("abdomen", "abdominal", "estomago", "epigastr")
                        )
                    ):
                        gastro_markers = (
                            "abdomen agudo",
                            "cirugia",
                            "exploracion abdominal",
                            "peritone",
                            "obstruccion",
                            "reevaluacion",
                        )
                        score += sum(
                            3 for marker in gastro_markers if marker in normalized_chunk
                        )
                    if score > best_score:
                        best_score = score
                        best_chunk = chunk
                if best_score == 0:
                    continue
                ranked.append(
                    (
                        best_score,
                        {
                            "type": "internal_catalog",
                            "domain": domain_key,
                            "title": reference["title"],
                            "source": source_path,
                            "snippet": best_chunk[:280],
                        },
                    )
                )
        ranked.sort(key=lambda item: item[0], reverse=True)
        unique: list[dict[str, str]] = []
        seen_keys: set[str] = set()
        for _, source in ranked:
            key = f"{source['domain']}::{source['source']}"
            if key in seen_keys:
                continue
            seen_keys.add(key)
            unique.append(source)
            if len(unique) >= max_internal_sources:
                break
        if unique:
            return unique
        return [
            {
                "type": "internal_catalog",
                "domain": str(domain["key"]),
                "title": str(domain["label"]),
                "source": "domain_catalog",
                "snippet": str(domain["summary"])[:280],
            }
            for domain in matched_domains[:max_internal_sources]
        ]

    @staticmethod
    def _is_generic_operational_query(query: str) -> bool:
        normalized_query = ClinicalChatService._normalize(query)
        return any(
            marker in normalized_query
            for marker in (
                "datos clave",
                "escalado",
                "pasos",
                "que hacer",
                "que podemos hacer",
                "manejo",
                "acciones",
                "prioridades",
                "recomendaciones",
                "seguimiento",
                "a donde derivamos",
                "derivamos",
            )
        )

    @classmethod
    def _source_domain_hits(
        cls,
        *,
        source: dict[str, str],
        domain_candidates: list[tuple[str, str]],
    ) -> list[str]:
        source_blob = " ".join(
            [
                str(source.get("domain") or ""),
                str(source.get("title") or ""),
                str(source.get("source") or ""),
                str(source.get("snippet") or ""),
            ]
        )
        normalized_blob = cls._normalize(source_blob)
        blob_tokens = cls._quality_tokens(source_blob)
        hits: list[str] = []
        for key, label in domain_candidates:
            score = 0
            key_tokens = [token for token in key.split("_") if token]
            score += sum(1 for token in key_tokens if token in normalized_blob)
            label_tokens = cls._quality_tokens(label)
            if label_tokens:
                score += sum(1 for token in label_tokens if token in blob_tokens)
            if score > 0:
                hits.append(key)
        return hits

    @classmethod
    def _filter_knowledge_sources_for_current_turn(
        cls,
        *,
        query: str,
        matched_domains: list[dict[str, object]],
        knowledge_sources: list[dict[str, str]],
    ) -> list[dict[str, str]]:
        if not knowledge_sources:
            return knowledge_sources
        domain_candidates: list[tuple[str, str]] = []
        for domain in matched_domains:
            key = cls._normalize(str(domain.get("key") or "")).strip()
            label = str(domain.get("label") or domain.get("key") or "").strip()
            if not key or not label:
                continue
            if key in {"general", "critical_ops", "administrative"}:
                continue
            domain_candidates.append((key, label))
        if not domain_candidates:
            return knowledge_sources

        strict_single_domain = len(domain_candidates) == 1
        target_domain = domain_candidates[0][0] if strict_single_domain else ""
        filtered: list[dict[str, str]] = []
        unmatched: list[dict[str, str]] = []
        for source in knowledge_sources:
            domain_hits = cls._source_domain_hits(
                source=source,
                domain_candidates=domain_candidates,
            )
            if strict_single_domain:
                if target_domain in domain_hits:
                    filtered.append(source)
                elif not domain_hits:
                    unmatched.append(source)
            elif domain_hits:
                filtered.append(source)

        if strict_single_domain:
            if cls._is_generic_operational_query(query):
                operational_sources = [
                    source
                    for source in filtered
                    if str(source.get("source") or "").lower().endswith(".md")
                ]
                if operational_sources:
                    return operational_sources
            if filtered:
                return filtered
            return unmatched or knowledge_sources

        return filtered or knowledge_sources

    @staticmethod
    def _source_is_active(source: ClinicalKnowledgeSource) -> bool:
        if source.expires_at is None:
            return True
        return source.expires_at >= datetime.now(timezone.utc)

    @classmethod
    def _build_validated_knowledge_sources(
        cls,
        db: Session,
        *,
        query: str,
        effective_specialty: str,
        matched_domains: list[dict[str, object]],
        max_internal_sources: int,
    ) -> list[dict[str, str]]:
        safe_limit = max(1, min(max_internal_sources * 20, 400))
        query_tokens = cls._tokenize(query)
        domain_tokens = {cls._normalize(str(domain["key"])) for domain in matched_domains}
        candidate_specialties: set[str] = {"general"}
        if effective_specialty:
            candidate_specialties.add(effective_specialty)
        for domain in matched_domains:
            domain_key = cls._normalize(str(domain.get("key") or ""))
            candidate_specialties.update(
                cls._DOMAIN_TO_SPECIALTY_SEARCH.get(domain_key, (domain_key,))
            )

        def _rank_sources(
            sources: list[ClinicalKnowledgeSource],
        ) -> list[tuple[int, dict[str, str]]]:
            ranked_sources: list[tuple[int, dict[str, str]]] = []
            for source in sources:
                if not cls._source_is_active(source):
                    continue
                corpus = " ".join(
                    part
                    for part in [
                        source.title or "",
                        source.summary or "",
                        source.content or "",
                        " ".join(source.tags or []),
                        source.specialty or "",
                    ]
                    if part
                )
                source_tokens = cls._tokenize(corpus)
                score = len(query_tokens.intersection(source_tokens))
                normalized_specialty = cls._normalize(source.specialty or "")
                if normalized_specialty == effective_specialty:
                    score += 2
                elif normalized_specialty in candidate_specialties:
                    score += 1
                for token in domain_tokens:
                    if token and token in source_tokens:
                        score += 1
                if score <= 0:
                    continue
                ranked_sources.append(
                    (
                        score,
                        {
                            "type": "internal_validated",
                            "domain": source.specialty,
                            "title": source.title,
                            "source": (
                                source.source_url or source.source_path or f"knowledge:{source.id}"
                            ),
                            "snippet": (source.summary or source.content or "")[:280],
                        },
                    )
                )
            return ranked_sources

        filtered_sources = (
            db.query(ClinicalKnowledgeSource)
            .filter(ClinicalKnowledgeSource.status == "validated")
            .filter(ClinicalKnowledgeSource.specialty.in_(sorted(candidate_specialties)))
            .order_by(
                ClinicalKnowledgeSource.updated_at.desc(),
                ClinicalKnowledgeSource.id.desc(),
            )
            .limit(safe_limit)
            .all()
        )
        ranked = _rank_sources(filtered_sources)
        if not ranked:
            broad_sources = (
                db.query(ClinicalKnowledgeSource)
                .filter(ClinicalKnowledgeSource.status == "validated")
                .order_by(
                    ClinicalKnowledgeSource.updated_at.desc(),
                    ClinicalKnowledgeSource.id.desc(),
                )
                .limit(safe_limit)
                .all()
            )
            ranked = _rank_sources(broad_sources)
        ranked.sort(key=lambda item: item[0], reverse=True)
        unique: list[dict[str, str]] = []
        seen: set[str] = set()
        for _, source in ranked:
            key = f"{source['domain']}::{source['source']}"
            if key in seen:
                continue
            seen.add(key)
            unique.append(source)
            if len(unique) >= max_internal_sources:
                break
        return unique

    @staticmethod
    def _extract_duckduckgo_topics(raw_topics: list[dict[str, Any]]) -> list[dict[str, str]]:
        results: list[dict[str, str]] = []
        for topic in raw_topics:
            nested_topics = topic.get("Topics")
            if isinstance(nested_topics, list):
                results.extend(ClinicalChatService._extract_duckduckgo_topics(nested_topics))
                continue
            title = str(topic.get("Text") or "").strip()
            url = str(topic.get("FirstURL") or "").strip()
            if title and url:
                domain = (urlparse(url).hostname or "").lower()
                results.append(
                    {
                        "type": "web",
                        "title": title[:180],
                        "source": "duckduckgo",
                        "url": url,
                        "domain": domain,
                        "snippet": title[:280],
                    }
                )
        return results

    @staticmethod
    def _canonicalize_source_url(url: str) -> str:
        text = str(url or "").strip()
        if not text:
            return ""
        parsed = urlparse(text)
        scheme = parsed.scheme.lower() or "https"
        host = parsed.netloc.lower()
        path = parsed.path.rstrip("/")
        if not host:
            return text.lower()
        if not path:
            path = "/"
        return f"{scheme}://{host}{path}"

    @classmethod
    def _build_word_shingles(cls, text: str, *, size: int) -> set[str]:
        tokens = cls._TOKEN_PATTERN.findall(cls._normalize(text))
        if not tokens:
            return set()
        if len(tokens) < size:
            return {" ".join(tokens)}
        return {" ".join(tokens[idx : idx + size]) for idx in range(0, len(tokens) - size + 1)}

    @classmethod
    def _minhash_signature(cls, shingles: set[str]) -> tuple[int, ...]:
        if not shingles:
            return ()
        signature: list[int] = []
        for seed in cls._WEB_MINHASH_SEEDS:
            min_hash = min(
                int.from_bytes(
                    hashlib.sha1(f"{seed}:{shingle}".encode("utf-8", errors="ignore")).digest()[:8],
                    byteorder="big",
                    signed=False,
                )
                for shingle in shingles
            )
            signature.append(min_hash)
        return tuple(signature)

    @staticmethod
    def _signature_similarity(left: tuple[int, ...], right: tuple[int, ...]) -> float:
        if not left or not right or len(left) != len(right):
            return 0.0
        matches = sum(
            1 for left_value, right_value in zip(left, right) if left_value == right_value
        )
        return matches / len(left)

    @classmethod
    def _is_web_spam_candidate(cls, *, title: str, snippet: str, url: str) -> bool:
        normalized_title = cls._normalize(title)
        normalized_snippet = cls._normalize(snippet)
        normalized_url = cls._normalize(url)
        combined = f"{normalized_title} {normalized_snippet}"
        spam_score = 0
        if len(normalized_snippet) < 40:
            spam_score += 1
        if "!!!" in snippet or "$$$" in snippet:
            spam_score += 2
        if re.search(r"(.)\1{5,}", combined):
            spam_score += 2
        spam_hits = sum(1 for term in cls._WEB_SPAM_TERMS if term in combined)
        spam_score += min(spam_hits, 3)
        letters = [char for char in f"{title} {snippet}" if char.isalpha()]
        if letters:
            uppercase_ratio = sum(1 for char in letters if char.isupper()) / len(letters)
            if len(letters) > 24 and uppercase_ratio >= 0.45:
                spam_score += 1
        if any(token in normalized_url for token in ("redirect", "aff", "utm_", "click", "promo")):
            spam_score += 1
        return spam_score >= 3

    @classmethod
    def _web_authority_score(cls, domain: str) -> float:
        normalized_domain = cls._normalize(domain)
        if not normalized_domain:
            return 0.0
        score = 0.55
        for reference, value in cls._WEB_DOMAIN_AUTHORITY.items():
            if normalized_domain == reference or normalized_domain.endswith(f".{reference}"):
                score = max(score, value)
        if normalized_domain.endswith(".gov"):
            score = max(score, 0.92)
        elif normalized_domain.endswith(".edu"):
            score = max(score, 0.88)
        return min(max(score, 0.0), 1.0)

    @classmethod
    def _web_relevance_score(cls, *, query_tokens: set[str], title: str, snippet: str) -> float:
        if not query_tokens:
            return 0.0
        title_tokens = cls._tokenize(title)
        snippet_tokens = cls._tokenize(snippet)
        title_overlap = len(query_tokens.intersection(title_tokens)) / max(len(query_tokens), 1)
        snippet_overlap = len(query_tokens.intersection(snippet_tokens)) / max(len(query_tokens), 1)
        coverage = (0.65 * title_overlap) + (0.35 * snippet_overlap)
        snippet_bonus = min(len(snippet.strip()) / 240.0, 1.0) * 0.12
        return min(max(coverage + snippet_bonus, 0.0), 1.0)

    @classmethod
    def _get_web_link_scores(
        cls,
        *,
        query: str,
        candidate_urls: list[str],
    ) -> tuple[dict[str, dict[str, float]], dict[str, str]]:
        if not settings.CLINICAL_CHAT_WEB_LINK_ANALYSIS_ENABLED:
            return {}, {
                "web_search_link_analysis_loaded": "0",
                "web_search_link_analysis_error": "disabled",
            }
        return WebLinkAnalysisService.score_candidates(
            query=query,
            candidate_urls=candidate_urls,
            snapshot_path=settings.CLINICAL_CHAT_WEB_LINK_ANALYSIS_PATH,
            max_hits_base=settings.CLINICAL_CHAT_WEB_LINK_ANALYSIS_MAX_HITS_BASE,
        )

    @classmethod
    def _score_and_filter_web_candidates(
        cls,
        *,
        query: str,
        max_web_sources: int,
        collected: list[dict[str, str]],
    ) -> tuple[list[dict[str, str]], dict[str, str]]:
        query_tokens = cls._quality_tokens(query)
        accepted: list[tuple[float, dict[str, str], tuple[int, ...]]] = []
        seen_urls: set[str] = set()
        filtered_out_whitelist = 0
        filtered_out_spam = 0
        filtered_out_duplicate = 0
        for item in collected:
            domain = str(item.get("domain") or "").strip().lower()
            if not KnowledgeSourceService.is_allowed_domain(domain):
                filtered_out_whitelist += 1
                continue
            canonical_url = cls._canonicalize_source_url(str(item.get("url") or ""))
            if not canonical_url or canonical_url in seen_urls:
                filtered_out_duplicate += 1
                continue
            title = str(item.get("title") or "").strip()
            snippet = str(item.get("snippet") or "").strip()
            if cls._is_web_spam_candidate(title=title, snippet=snippet, url=canonical_url):
                filtered_out_spam += 1
                continue
            shingle_text = f"{title} {snippet}".strip()
            shingles = cls._build_word_shingles(shingle_text, size=cls._WEB_SHINGLE_SIZE)
            signature = cls._minhash_signature(shingles)
            near_duplicate = any(
                cls._signature_similarity(signature, previous_signature)
                >= cls._WEB_NEAR_DUP_SIGNATURE_THRESHOLD
                for _, _, previous_signature in accepted
            )
            if near_duplicate:
                filtered_out_duplicate += 1
                continue
            authority_score = cls._web_authority_score(domain)
            relevance_score = cls._web_relevance_score(
                query_tokens=query_tokens,
                title=title,
                snippet=snippet,
            )
            quality_score = min((0.62 * authority_score) + (0.38 * relevance_score), 1.0)
            accepted.append(
                (
                    quality_score,
                    {
                        **item,
                        "url": canonical_url,
                        "authority_score": f"{authority_score:.3f}",
                        "relevance_score": f"{relevance_score:.3f}",
                        "quality_score": f"{quality_score:.3f}",
                    },
                    signature,
                )
            )
            seen_urls.add(canonical_url)
        accepted.sort(key=lambda entry: (entry[0], entry[1].get("title", "")), reverse=True)
        link_scores, link_trace = cls._get_web_link_scores(
            query=query,
            candidate_urls=[entry[1].get("url", "") for entry in accepted],
        )
        link_blend = float(settings.CLINICAL_CHAT_WEB_LINK_ANALYSIS_BLEND)
        if accepted and link_scores:
            reweighted: list[tuple[float, dict[str, str], tuple[int, ...]]] = []
            for base_quality, item, signature in accepted:
                url = str(item.get("url") or "")
                link_item = link_scores.get(url)
                if not link_item:
                    reweighted.append((base_quality, item, signature))
                    continue
                link_score = float(link_item.get("link_score", 0.0))
                final_quality = min(
                    max(
                        ((1.0 - link_blend) * float(base_quality)) + (link_blend * link_score),
                        0.0,
                    ),
                    1.0,
                )
                enriched_item = {
                    **item,
                    "base_quality_score": f"{float(base_quality):.3f}",
                    "link_score": f"{link_score:.3f}",
                    "link_pagerank_global": f"{float(link_item.get('global_pagerank', 0.0)):.3f}",
                    "link_pagerank_topic": f"{float(link_item.get('topic_pagerank', 0.0)):.3f}",
                    "link_hits_authority": f"{float(link_item.get('hits_authority', 0.0)):.3f}",
                    "link_hits_hub": f"{float(link_item.get('hits_hub', 0.0)):.3f}",
                    "link_anchor_relevance": f"{float(link_item.get('anchor_relevance', 0.0)):.3f}",
                    "quality_score": f"{final_quality:.3f}",
                }
                reweighted.append((final_quality, enriched_item, signature))
            accepted = sorted(
                reweighted,
                key=lambda entry: (entry[0], entry[1].get("title", "")),
                reverse=True,
            )

        web_sources = [entry[1] for entry in accepted[:max_web_sources]]
        trace = {
            "web_search_candidates_total": str(len(collected)),
            "web_search_whitelist_filtered_out": str(filtered_out_whitelist),
            "web_search_spam_filtered_out": str(filtered_out_spam),
            "web_search_duplicate_filtered_out": str(filtered_out_duplicate),
            "web_search_quality_sorted": "1",
            "web_search_link_analysis_blend": f"{link_blend:.2f}",
            "web_search_near_duplicate_threshold": (
                f"{cls._WEB_NEAR_DUP_SIGNATURE_THRESHOLD:.2f}"
            ),
        }
        trace.update(link_trace)
        if web_sources:
            avg_quality = sum(
                float(item.get("quality_score") or "0") for item in web_sources
            ) / len(web_sources)
            trace["web_search_avg_quality_top"] = f"{avg_quality:.3f}"
        else:
            trace["web_search_avg_quality_top"] = "0.000"
        return web_sources, trace

    @classmethod
    def _fetch_web_sources(
        cls,
        query: str,
        max_web_sources: int,
    ) -> tuple[list[dict[str, str]], dict[str, str]]:
        if not settings.CLINICAL_CHAT_WEB_ENABLED:
            return [], {"web_search_enabled": "0"}
        trace: dict[str, str] = {"web_search_enabled": "1"}
        try:
            encoded_query = quote_plus(query)
            url = (
                "https://duckduckgo.com/?q="
                f"{encoded_query}&format=json&no_html=1&no_redirect=1&skip_disambig=1"
            )
            request = Request(url=url, headers={"User-Agent": "clinical-chat/1.0"})
            with urlopen(
                request,
                timeout=max(1, int(settings.CLINICAL_CHAT_WEB_TIMEOUT_SECONDS)),
            ) as response:
                payload = json.loads(response.read().decode("utf-8", errors="ignore"))
        except (URLError, ValueError, TimeoutError):
            trace["web_search_error"] = "request_failed"
            return [], trace

        collected: list[dict[str, str]] = []
        abstract_text = str(payload.get("AbstractText") or "").strip()
        abstract_url = str(payload.get("AbstractURL") or "").strip()
        heading = str(payload.get("Heading") or "DuckDuckGo result").strip()
        if abstract_text and abstract_url:
            abstract_domain = (urlparse(abstract_url).hostname or "").lower()
            collected.append(
                {
                    "type": "web",
                    "title": heading[:180],
                    "source": "duckduckgo",
                    "url": abstract_url,
                    "domain": abstract_domain,
                    "snippet": abstract_text[:280],
                }
            )
        related_topics = payload.get("RelatedTopics", [])
        if isinstance(related_topics, list):
            collected.extend(ClinicalChatService._extract_duckduckgo_topics(related_topics))
        web_sources, quality_trace = cls._score_and_filter_web_candidates(
            query=query,
            max_web_sources=max_web_sources,
            collected=collected,
        )
        trace.update(quality_trace)
        trace["web_search_results"] = str(len(web_sources))
        return web_sources, trace

    @staticmethod
    def _fetch_recommendations(
        *,
        query: str,
        matched_endpoints: list[str],
    ) -> list[dict[str, Any]]:
        normalized_query = ClinicalChatService._normalize(query)
        results: list[dict[str, Any]] = []
        for endpoint in matched_endpoints:
            recommendation: dict[str, Any] | None = None
            if endpoint.endswith("/critical-ops/recommendation"):
                recommendation = CriticalOpsProtocolService.build_recommendation(
                    CriticalOpsProtocolRequest(
                        suspected_septic_shock="sepsis" in normalized_query,
                        non_traumatic_chest_pain="torac" in normalized_query,
                        triage_level="rojo" if "shock" in normalized_query else "amarillo",
                    )
                ).model_dump()
            elif endpoint.endswith("/sepsis/recommendation"):
                recommendation = SepsisProtocolService.build_recommendation(
                    SepsisProtocolRequest(
                        suspected_infection=True,
                        lactate_mmol_l=4.0 if "lactato" in normalized_query else None,
                        systolic_bp=(
                            85 if "tas" in normalized_query or "shock" in normalized_query else None
                        ),
                    )
                ).model_dump()
            elif endpoint.endswith("/scasest/recommendation"):
                recommendation = ScasestProtocolService.build_recommendation(
                    ScasestProtocolRequest(
                        chest_pain_typical="torac" in normalized_query,
                        troponin_positive="troponina" in normalized_query,
                        hemodynamic_instability="shock" in normalized_query,
                    )
                ).model_dump()
            if recommendation is None:
                continue
            results.append(
                {
                    "type": "internal_recommendation",
                    "endpoint": endpoint,
                    "title": f"Recomendacion sintetizada {endpoint.split('/')[-2]}",
                    "source": endpoint,
                    "snippet": json.dumps(recommendation, ensure_ascii=False)[:300],
                    "recommendation": recommendation,
                }
            )
        return results

    @classmethod
    def _render_clinical_answer(
        cls,
        *,
        care_task: CareTask,
        query: str,
        matched_domains: list[dict[str, object]],
        matched_endpoints: list[str],
        effective_specialty: str,
        memory_facts_used: list[str],
        patient_summary: dict[str, Any] | None,
        patient_history_facts_used: list[str],
        extracted_facts: list[str],
        knowledge_sources: list[dict[str, str]],
        web_sources: list[dict[str, str]],
        include_protocol_catalog: bool,
        tool_mode: str,
        recent_dialogue: list[dict[str, str]],
        endpoint_recommendations: list[dict[str, Any]],
        decision_psychology: dict[str, Any] | None = None,
        logic_assessment: dict[str, Any] | None = None,
        contract_assessment: dict[str, Any] | None = None,
        math_assessment: dict[str, Any] | None = None,
    ) -> str:
        lines: list[str] = [
            "Plan operativo inicial (no diagnostico).",
            f"Caso: {care_task.title}. Herramienta: {tool_mode}.",
        ]
        if recent_dialogue:
            last_turn = recent_dialogue[-1]
            last_user_query = str(last_turn.get("user_query", "")).strip()
            if cls._is_clinical_continuity_candidate(last_user_query):
                lines.append(
                    "Continuidad: tomo como referencia el ultimo turno clinico sobre "
                    f"'{last_user_query[:120]}'."
                )
        if matched_domains:
            lines.append("1) Priorizacion inmediata (0-10 min)")
            for idx, domain in enumerate(matched_domains):
                label = str(domain["label"])
                summary = str(domain["summary"])
                if include_protocol_catalog and idx < len(matched_endpoints):
                    lines.append(f"- Activar ruta {label}: {summary}.")
                else:
                    lines.append(f"- Activar ruta {label}: {summary}.")
        display_memory_facts = [fact for fact in memory_facts_used if ":" not in fact]
        if display_memory_facts:
            lines.append("2) Contexto clinico reutilizado")
            lines.append("- Memoria de sesion: " + ", ".join(display_memory_facts[:5]) + ".")
        if patient_summary and patient_summary.get("patient_interactions_count", 0) > 0:
            lines.append("3) Contexto longitudinal")
            lines.append(
                "- Historial paciente: "
                f"{patient_summary['patient_interactions_count']} interacciones, "
                f"{patient_summary['patient_encounters_count']} episodios."
            )
        if patient_history_facts_used:
            lines.append(
                "- Hechos longitudinales: " + ", ".join(patient_history_facts_used[:5]) + "."
            )
        if decision_psychology:
            risk_level = str(decision_psychology.get("risk_level") or "low")
            communication_hint = str(decision_psychology.get("communication_hint") or "").strip()
            if communication_hint:
                lines.append(
                    "- Marco de riesgo y comunicacion (Prospect): "
                    f"{risk_level}. {communication_hint}"
                )
            fechner_intensity = decision_psychology.get("fechner_intensity")
            if fechner_intensity is not None:
                lines.append(
                    "- Intensidad percibida de sintoma (Fechner): "
                    f"{float(fechner_intensity):.2f}/1.00."
                )
            fechner_change = decision_psychology.get("fechner_change")
            if fechner_change is not None:
                lines.append(
                    "- Variacion percibida reciente (Fechner): "
                    f"{float(fechner_change):.2f}/1.00."
                )
        if logic_assessment:
            rules = logic_assessment.get("rules_triggered") or []
            contradictions = logic_assessment.get("contradictions") or []
            actions = logic_assessment.get("recommended_actions") or []
            consistency_status = str(logic_assessment.get("consistency_status") or "consistent")
            abstention_required = bool(logic_assessment.get("abstention_required"))
            abstention_reason = str(logic_assessment.get("abstention_reason") or "none")
            sequence_code = str(logic_assessment.get("protocol_sequence_code") or "")
            beta_signature = str(logic_assessment.get("protocol_beta_signature") or "")
            first_escalation_step = logic_assessment.get("first_escalation_step")
            if rules or contradictions or actions or consistency_status != "consistent":
                lines.append("4) Bloque logico formal")
                if rules:
                    lines.append(
                        "- Reglas activadas: "
                        + ", ".join(str(rule.get("id", "")) for rule in rules[:4])
                        + "."
                    )
                if actions:
                    lines.append("- Acciones derivadas por reglas:")
                    for action in actions[:4]:
                        lines.append(f"  - {action}")
                if contradictions:
                    lines.append("- Alertas de consistencia:")
                    for finding in contradictions[:3]:
                        lines.append(f"  - {finding}")
                lines.append(f"- Estado de consistencia formal: {consistency_status}.")
                if sequence_code:
                    lines.append(f"- Firma estructural del plan (Godel): {sequence_code}.")
                if beta_signature and beta_signature != "na":
                    lines.append(f"- Firma beta (secuencia): {beta_signature}.")
                if first_escalation_step:
                    lines.append(
                        f"- Primera accion de escalado detectada en paso: {first_escalation_step}."
                    )
                if abstention_required:
                    lines.append(
                        "- Estado formal: evidencia insuficiente o inconsistente para "
                        "cierre seguro; escalar validacion humana inmediata."
                    )
                    if abstention_reason != "none":
                        lines.append(f"  - Motivo de abstencion: {abstention_reason}.")
        if contract_assessment and bool(contract_assessment.get("contract_applied")):
            lines.append("4.1) Contrato operativo")
            lines.append(
                "- Contrato aplicado: "
                f"{contract_assessment.get('contract_id', 'n/a')} "
                f"({contract_assessment.get('contract_domain', 'n/a')})."
            )
            lines.append(
                f"- Estado de contrato: {contract_assessment.get('contract_state', 'partial')}."
            )
            missing_data = list(contract_assessment.get("missing_data") or [])
            if missing_data:
                lines.append("- Datos criticos faltantes:")
                for item in missing_data[:4]:
                    lines.append(f"  - {item}")
            steps_0_10 = list(contract_assessment.get("steps_0_10") or [])
            if steps_0_10:
                lines.append("- Pasos contractuales 0-10 min:")
                for item in steps_0_10[:4]:
                    lines.append(f"  - {item}")
            steps_10_60 = list(contract_assessment.get("steps_10_60") or [])
            if steps_10_60:
                lines.append("- Pasos contractuales 10-60 min:")
                for item in steps_10_60[:4]:
                    lines.append(f"  - {item}")
            escalation_criteria = list(contract_assessment.get("escalation_criteria") or [])
            if escalation_criteria:
                lines.append("- Criterios de escalado contractual:")
                for item in escalation_criteria[:3]:
                    lines.append(f"  - {item}")
        if math_assessment and bool(math_assessment.get("enabled")):
            lines.append("4.2) Bloque matematico de similitud")
            lines.append(
                "- Dominio top por similitud+bias bayesiano: "
                f"{math_assessment.get('top_domain', 'n/a')}."
            )
            lines.append(
                "- Probabilidad posterior top: "
                f"{math_assessment.get('top_probability', 0.0)}."
            )
            lines.append(
                "- Score de prioridad matematico: "
                f"{math_assessment.get('priority_score', 'low')}."
            )
            lines.append(
                "- Incertidumbre matematica: "
                f"{math_assessment.get('uncertainty_level', 'high')} "
                f"(margen top2={math_assessment.get('margin_top2', 0.0)}, "
                f"entropia={math_assessment.get('normalized_entropy', 0.0)})."
            )
        if endpoint_recommendations:
            lines.append("5) Recomendaciones operativas internas")
            for recommendation in endpoint_recommendations[:4]:
                title = str(recommendation.get("title", "Ruta operativa")).strip()
                safe_snippet = cls._safe_source_snippet(
                    {"snippet": str(recommendation.get("snippet", ""))}
                )
                lines.append(f"- {title}.")
                if safe_snippet:
                    lines.append(f"  - Sintesis: {safe_snippet[:220]}")
        if knowledge_sources:
            lines.append("6) Evidencia usada")
            lines.append("- Fuentes internas indexadas:")
            for source in knowledge_sources[:4]:
                lines.append(f"  - {cls._display_internal_source_label(source)}")
        elif settings.CLINICAL_CHAT_REQUIRE_VALIDATED_INTERNAL_SOURCES:
            lines.append(
                "6) Evidencia usada\n- Sin fuentes internas validadas para esta consulta. "
                "Escalar revision profesional antes de tomar decision."
            )
        if web_sources:
            lines.append("- Fuentes web consultadas (dominios en whitelist):")
            for source in web_sources[:3]:
                lines.append(f"  - {source['title']}: {source['url']}")
        lines.append("7) Cierre operativo")
        lines.append(
            "- Validar decisiones con protocolo local, "
            "responsable clinico y estado dinamico del paciente."
        )
        lines.append(
            "- Este fallback operativo no constituye diagnostico final; "
            "requiere verificacion clinica presencial."
        )
        return "\n".join(lines)

    @classmethod
    def _is_clinical_continuity_candidate(cls, query: str) -> bool:
        normalized = cls._normalize(query)
        if not normalized or cls._is_social_or_discovery_query(query):
            return False
        query_facts = cls._extract_facts(query)
        keyword_hits = cls._count_domain_keyword_hits(query)
        return cls._has_clinical_signal(
            query=query,
            extracted_facts=query_facts,
            keyword_hits=keyword_hits,
        )

    @staticmethod
    def _is_social_or_discovery_query(query: str) -> bool:
        normalized = ClinicalChatService._normalize(query)
        if normalized.startswith(("hola", "buenas", "hey", "que tal")):
            return True
        discovery_tokens = {"caso", "casos", "informacion", "info", "resumen"}
        return len(normalized.split()) <= 8 and any(
            token in normalized for token in discovery_tokens
        )

    @staticmethod
    def _is_simple_greeting_query(query: str) -> bool:
        normalized = ClinicalChatService._normalize(query)
        if not normalized:
            return False
        greeting_phrases = {
            "hola",
            "hola que tal",
            "que tal",
            "buenas",
            "buenos dias",
            "buenas tardes",
            "buenas noches",
            "hey",
            "hello",
            "hi",
        }
        if normalized in greeting_phrases:
            return True
        if len(normalized.split()) > 6:
            return False
        if not normalized.startswith(("hola", "buenas", "hey", "hello", "hi")):
            return False
        discovery_or_task_tokens = {
            "caso",
            "casos",
            "informacion",
            "info",
            "resumen",
            "tratamiento",
            "dosis",
            "protocolo",
        }
        return not any(token in normalized for token in discovery_or_task_tokens)

    @staticmethod
    def _safe_source_snippet(source: dict[str, str]) -> str:
        snippet = str(source.get("snippet") or "").strip()
        if not snippet:
            return ""
        if snippet.startswith("{") or snippet.startswith("["):
            return ""
        sanitized = snippet
        sanitized = re.sub(
            r"(?:[A-Za-z]:)?[\\/](?:[^\\/\s]+[\\/])+[^\\/\s]+(?:\.(?:md|txt|pdf))?",
            "",
            sanitized,
            flags=re.IGNORECASE,
        )
        sanitized = re.sub(
            r"\bdocs[\\/][^\s)]+",
            "",
            sanitized,
            flags=re.IGNORECASE,
        )
        sanitized = re.sub(r"\s{2,}", " ", sanitized).strip()
        return sanitized

    @classmethod
    def _display_internal_source_label(cls, source: dict[str, str]) -> str:
        title = str(source.get("title") or "").strip()
        locator = str(source.get("source") or "").strip()
        if title and not re.search(r"(?:^|[\\/])docs[\\/]", title, flags=re.IGNORECASE):
            return title
        if locator:
            normalized = locator.replace("\\", "/")
            leaf = normalized.split("/")[-1]
            stem = re.sub(r"\.(md|txt|pdf)$", "", leaf, flags=re.IGNORECASE)
            stem = stem.replace("_", " ").replace("-", " ").strip()
            if stem:
                return stem.title()
        return title or "Fuente interna"

    @staticmethod
    def _describe_available_domains(matched_domains: list[dict[str, object]]) -> list[str]:
        labels: list[str] = []
        for domain in matched_domains[:4]:
            label = str(domain.get("label") or domain.get("key") or "ruta clinica")
            if label not in labels:
                labels.append(label)
        return labels

    @staticmethod
    def _render_general_answer(
        *,
        query: str,
        memory_facts_used: list[str],
        knowledge_sources: list[dict[str, str]],
        web_sources: list[dict[str, str]],
        tool_mode: str,
        recent_dialogue: list[dict[str, str]],
        matched_domains: list[dict[str, object]],
    ) -> str:
        if ClinicalChatService._is_simple_greeting_query(query):
            return "Hola! Estoy bien, gracias. Y tu? En que puedo ayudarte hoy?"
        lines: list[str] = []
        parsed_intent = ClinicalChatService._parse_semantic_intent(query).get("intent", "general")
        suggested_queries = ClinicalChatService._build_next_query_suggestions(
            query=query,
            matched_domains=matched_domains,
            parsed_intent=str(parsed_intent),
            limit=3,
        )
        if ClinicalChatService._is_social_or_discovery_query(query):
            lines.append("Hola. Puedo ayudarte con dudas clinicas y documentacion interna.")
            available_domains = ClinicalChatService._describe_available_domains(matched_domains)
            if available_domains:
                lines.append("Especialidades internas disponibles ahora:")
                lines.append("- " + ", ".join(available_domains))
            if knowledge_sources:
                source_titles = [
                    str(source.get("title") or "Fuente interna") for source in knowledge_sources[:3]
                ]
                lines.append("Puedo apoyarme en:")
                lines.append("- " + ", ".join(source_titles))
            if suggested_queries:
                lines.append("Puedes preguntarme, por ejemplo:")
                for item in suggested_queries:
                    lines.append(f"- {item}")
            lines.append(
                "Si me das un caso concreto, te respondo directo y con fuentes internas si hay."
            )
        else:
            if web_sources:
                first_source = web_sources[0]
                snippet = ClinicalChatService._safe_source_snippet(first_source)
                if snippet:
                    lines.append(snippet)
                lines.append("Fuente principal:")
                lines.append(
                    f"- {first_source.get('title', 'Referencia web')}: "
                    f"{first_source.get('url', '')}"
                )
            elif knowledge_sources:
                first_source = knowledge_sources[0]
                snippet = ClinicalChatService._safe_source_snippet(first_source)
                if snippet:
                    lines.append(snippet)
                lines.append(
                    "Referencia interna: "
                    f"{ClinicalChatService._display_internal_source_label(first_source)}"
                )
            else:
                lines.append("Te escucho. Dime que necesitas y voy al grano.")
            if suggested_queries:
                lines.append("Preguntas que pueden ayudarte:")
                for item in suggested_queries:
                    lines.append(f"- {item}")

        if not lines:
            lines.append("Te escucho.")
        if memory_facts_used and len(lines) < 2:
            lines.append("Tengo contexto de la sesion para continuar mejor.")
        if recent_dialogue and len(lines) < 3:
            lines.append("Puedo continuar desde el ultimo turno cuando quieras.")
        return "\n".join(lines)

    @staticmethod
    def _merge_source_lists(
        primary: list[dict[str, str]],
        secondary: list[dict[str, str]],
        *,
        limit: int,
    ) -> list[dict[str, str]]:
        merged: list[dict[str, str]] = []
        seen: set[tuple[str, str]] = set()
        for source in [*primary, *secondary]:
            title = str(source.get("title") or "Fuente")
            locator = str(source.get("source") or source.get("url") or "")
            key = (title, locator)
            if key in seen:
                continue
            seen.add(key)
            merged.append(
                {
                    "type": str(source.get("type") or "internal"),
                    "title": title,
                    "source": locator,
                    "snippet": str(source.get("snippet") or "")[:360],
                    "url": str(source.get("url") or ""),
                }
            )
            if len(merged) >= limit:
                break
        return merged

    @staticmethod
    def _render_clarifying_question_answer(
        *,
        question_text: str,
        domain: str,
        turn_index: int,
        max_turns: int,
        top_probability: float,
        suggested_queries: list[str] | None = None,
    ) -> str:
        lines = [
            "Antes de darte un plan operativo completo, necesito un dato clinico clave.\n"
            f"Pregunta de aclaracion ({turn_index}/{max_turns}) [{domain}]:",
            f"- {question_text}",
            "En cuanto respondas ese punto, te devuelvo pasos 0-10 y 10-60 minutos "
            "con acciones priorizadas y fuentes internas exactas.",
            f"Estado de incertidumbre actual: {top_probability:.2f} de confianza en "
            "la hipotesis principal (insuficiente para cierre operativo).",
        ]
        if suggested_queries:
            lines.append("Si prefieres, puedes responder con alguno de estos enfoques:")
            for suggestion in suggested_queries[:3]:
                lines.append(f"- {suggestion}")
        return "\n".join(lines)

    @staticmethod
    def _render_uncertainty_gate_answer(
        *,
        query: str,
        top_domain: str,
        posterior_variance: float,
    ) -> str:
        return (
            "Evidencia insuficiente para cierre seguro en este turno.\n"
            f"Dominio probable: {top_domain or 'indeterminado'}.\n"
            f"Incertidumbre estimada (varianza posterior): {posterior_variance:.3f}.\n"
            "Necesito datos clinicos adicionales de alto impacto (signos vitales, analitica "
            "urgente y evolucion temporal) para emitir un plan operativo mas preciso.\n"
            f"Consulta original: {query[:220]}"
        )

    @classmethod
    def _render_evidence_first_clinical_answer(
        cls,
        *,
        care_task: CareTask,
        query: str,
        matched_domains: list[dict[str, object]],
        matched_endpoints: list[str],
        knowledge_sources: list[dict[str, str]],
    ) -> str:
        prioritized_sources = sorted(knowledge_sources, key=cls._source_priority)
        lines: list[str] = ["Resumen operativo basado en evidencia interna (no diagnostico)."]
        query_tokens = cls._quality_tokens(query)
        ranked_actions: list[tuple[float, str, str]] = []
        domain_candidates: list[tuple[str, str]] = []
        for domain in matched_domains[:4]:
            key = cls._normalize(str(domain.get("key") or "")).strip()
            label = str(domain.get("label") or domain.get("key") or "").strip()
            if not key or not label:
                continue
            if key in {"general", "critical_ops", "administrative"}:
                continue
            domain_candidates.append((key, label))

        def resolve_action_domain(source: dict[str, str], action_text: str) -> str:
            if not domain_candidates:
                return "general"
            source_blob = " ".join(
                [
                    str(source.get("title") or ""),
                    str(source.get("source") or ""),
                    str(source.get("snippet") or ""),
                    action_text,
                ]
            )
            normalized_blob = cls._normalize(source_blob)
            best_key = "general"
            best_hits = 0
            for key, label in domain_candidates:
                hit = 0
                key_tokens = [token for token in key.split("_") if token]
                if any(token in normalized_blob for token in key_tokens):
                    hit += 1
                label_tokens = cls._quality_tokens(label)
                if (
                    label_tokens
                    and cls._overlap_recall(
                        label_tokens,
                        cls._quality_tokens(source_blob),
                    )
                    > 0
                ):
                    hit += 1
                if hit > best_hits:
                    best_hits = hit
                    best_key = key
            return best_key

        for source in prioritized_sources[:10]:
            snippet = cls._clean_evidence_snippet(
                str(source.get("snippet") or ""),
                max_chars=220,
            )
            if len(snippet) < 30:
                continue
            action = re.sub(
                r"^\s*(?:\d+[\).\-\s]+|[-*]+\s*)",
                "",
                snippet[:220],
            ).rstrip(" .,;")
            if len(action) < 20:
                continue
            overlap = cls._overlap_recall(query_tokens, cls._quality_tokens(action))
            if query_tokens and overlap <= 0.0:
                continue
            action_domain = resolve_action_domain(source, action)
            ranked_actions.append((overlap, f"{action}.", action_domain))

        ranked_actions.sort(key=lambda item: item[0], reverse=True)
        seen_actions: set[str] = set()
        actions: list[tuple[str, str]] = []
        for _, action, action_domain in ranked_actions:
            norm_action = cls._normalize(action)
            if norm_action in seen_actions:
                continue
            seen_actions.add(norm_action)
            actions.append((action, action_domain))
            if len(actions) >= 6:
                break
        multi_domain_mode = len(domain_candidates) >= 2
        if multi_domain_mode:
            actions_by_domain: dict[str, list[str]] = {
                key: [] for key, _ in domain_candidates
            }
            for action_text, action_domain in actions:
                domain_bucket = (
                    action_domain
                    if action_domain in actions_by_domain
                    else domain_candidates[0][0]
                )
                actions_by_domain[domain_bucket].append(action_text)
            for key, label in domain_candidates[:2]:
                domain_actions = actions_by_domain.get(key, [])
                lines.append(f"Bloque {label}:")
                lines.append("Prioridades 0-10 minutos:")
                for item in domain_actions[:2]:
                    lines.append(f"- {item}")
                if not domain_actions[:2]:
                    lines.append(
                        "- Sin evidencia operativa suficiente en este bloque; completar datos."
                    )
                lines.append("Prioridades 10-60 minutos:")
                for item in domain_actions[2:4]:
                    lines.append(f"- {item}")
                if not domain_actions[2:4]:
                    lines.append(
                        "- Completar pruebas objetivo y reevaluar respuesta "
                        "a intervenciones iniciales."
                    )
                lines.append("Escalado y seguridad:")
                lines.append(
                    f"- Escalar de inmediato ante deterioro clinico en {label.lower()}."
                )
                lines.append(
                    "- Registrar decisiones y contrastar cada paso con protocolo local vigente."
                )
        else:
            lines.append("Prioridades 0-10 minutos:")
            for item, _domain in actions[:3]:
                lines.append(f"- {item}")
            if not actions[:3]:
                lines.append(
                    "- Estabilizar via aerea, respiracion y circulacion "
                    "con monitorizacion continua."
                )

            lines.append("Prioridades 10-60 minutos:")
            for item, _domain in actions[3:6]:
                lines.append(f"- {item}")
            if not actions[3:6]:
                lines.append(
                    "- Completar pruebas objetivo y reevaluar respuesta a intervenciones iniciales."
                )

            lines.append("Escalado y seguridad:")
            lines.append(
                "- Escalar de inmediato ante deterioro clinico o criterios de alto riesgo."
            )
            lines.append(
                "- Registrar decisiones y contrastar cada paso con protocolo local vigente."
            )

        lines.append("Fuentes internas exactas:")
        cited = 0
        seen_sources: set[str] = set()
        for source in prioritized_sources[:12]:
            locator = str(source.get("source") or "").strip()
            if not locator or locator in seen_sources:
                continue
            locator_norm = cls._normalize(locator).replace("\\", "/")
            if "/api/" in locator_norm or locator_norm.startswith("app/"):
                continue
            if not cls._is_clinical_source_locator(locator):
                continue
            seen_sources.add(locator)
            title = cls._display_internal_source_label(source)
            lines.append(f"- {title}")
            cited += 1
        if cited == 0:
            lines.append("- No se localizaron fuentes internas para esta consulta.")

        lines.append(
            "Validar decisiones con protocolo local, responsable clinico "
            "y estado dinamico del paciente."
        )
        return "\n".join(lines)

    @classmethod
    def _clean_evidence_snippet(cls, text: str, *, max_chars: int) -> str:
        lines = [segment.strip() for segment in str(text or "").splitlines() if segment.strip()]
        blocked_markers = (
            "python.exe",
            ".py",
            "pytest",
            "curl ",
            "/api/v1/",
            "/api/",
            "endpoint",
            "workflow",
            "agent_run",
            "tool_mode",
            "py_compile",
            "venv\\",
            "venv/",
            "app/",
            "app\\",
            "{",
            "}",
            "uvicorn",
            "http://",
            "https://",
            "`",
            "motor operativo",
            "sistema no tenia",
            "sistema no tenía",
            "logica operativa cubierta",
            "lógica operativa cubierta",
            "validacion -",
            "validación -",
            "documento >",
        )
        kept: list[str] = []
        for line in lines:
            normalized = cls._normalize(line)
            if any(marker in normalized for marker in blocked_markers):
                continue
            compact = re.sub(r"^\s*(?:\d+[\).\-\s]+|[-*]+\s*)", "", " ".join(line.split())).strip()
            alpha_chars = sum(1 for char in compact if char.isalpha())
            if alpha_chars < 18:
                continue
            kept.append(compact)
            if sum(len(item) for item in kept) >= max_chars:
                break
        if not kept:
            compact = " ".join(str(text or "").split())
            return compact[:max_chars]
        return " ".join(kept)[:max_chars]

    @classmethod
    def _sanitize_final_answer_text(cls, answer: str) -> str:
        if not answer:
            return answer
        blocked_patterns = (
            r"/api/v\d+/[^\s]*",
            r"\bpy_compile\b",
            r"\bpython\.exe\b",
            r"\buvicorn\b",
            r"\bvenv[\\/]\S*",
            r"\bapp[\\/]\S*",
            r"\bagent_run\b",
            r"\bworkflow\b",
            r"\btool_mode\b",
        )
        lines = [line.rstrip() for line in str(answer).splitlines()]
        cleaned_lines: list[str] = []
        skip_route_block = False
        for line in lines:
            stripped = line.strip()
            lowered = cls._normalize(stripped)
            if lowered.startswith("ruta operativa activa"):
                skip_route_block = True
                continue
            if skip_route_block and stripped.startswith("-"):
                continue
            if skip_route_block and not stripped.startswith("-"):
                skip_route_block = False
            if "`" in stripped:
                stripped = stripped.replace("`", "")
            if stripped.startswith("- {") or stripped.startswith("{"):
                continue
            if '{"' in stripped or '":' in stripped:
                continue
            sanitized = stripped
            for pattern in blocked_patterns:
                sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)
            sanitized = re.sub(r"\s{2,}", " ", sanitized).strip()
            if not sanitized:
                continue
            cleaned_lines.append(sanitized)
        return "\n".join(cleaned_lines).strip()

    @classmethod
    def _is_clinical_source_locator(cls, locator: str) -> bool:
        normalized = cls._normalize(locator).replace("\\", "/")
        if not normalized:
            return False
        blocked = (
            "docs/01_current_state.md",
            "docs/decisions/",
            "agents/shared/",
            "api_contract.md",
            "data_contract.md",
            "deploy_notes.md",
            "test_plan.md",
            "task_board.md",
        )
        if any(token in normalized for token in blocked):
            return False
        return "docs/" in normalized

    @classmethod
    def _source_priority(cls, source: dict[str, str]) -> tuple[int, int]:
        locator = cls._normalize(str(source.get("source") or "")).replace("\\", "/")
        title = cls._normalize(str(source.get("title") or ""))
        if "docs/decisions/" in locator:
            return (3, -len(title))
        if locator.startswith("docs/"):
            if "docs/pdf_raw/" in locator:
                return (1, -len(title))
            return (0, -len(title))
        return (2, -len(title))

    @classmethod
    def _variance_threshold_for_domain(cls, domain: str) -> float:
        normalized = cls._normalize(domain)
        configured_default = settings.CLINICAL_CHAT_UNCERTAINTY_GATE_MAX_VARIANCE
        return cls._DOMAIN_VARIANCE_THRESHOLDS.get(normalized, configured_default)

    @classmethod
    def _is_actionable_llm_answer(cls, *, answer: str, response_mode: str) -> bool:
        text = answer.strip()
        if not text:
            return False
        normalized = cls._normalize(text)
        refusal_markers = (
            "no puedo proporcionar",
            "no puedo ofrecer",
            "no puedo dar asesoramiento",
            "consulta a un profesional de la salud",
            "lo siento, pero no puedo",
            "i cannot provide medical advice",
            "consult a healthcare professional",
        )
        if any(marker in normalized for marker in refusal_markers):
            return False
        if response_mode != "clinical":
            return len(text) >= 24
        forbidden_reference_markers = (
            "\nreferencias",
            "\nreferencia bibliografica",
            "\nreferencias bibliograficas",
            "\nfuentes internas relevantes",
        )
        if any(marker in normalized for marker in forbidden_reference_markers):
            return False
        if re.search(r"\(\s*(?:19|20)\d{2}\s*\)\.", text):
            return False
        if any(token in text for token in ("[edad]", "[dato]", "[x]", "[xxx]")):
            return False
        if re.search(r"\[[^\]]{2,80}\]", text):
            return False
        if text.count("(") > text.count(")"):
            return False
        if len(text) >= 160 and text.rstrip()[-1].isalnum():
            return False
        if len(text) < 220:
            return False
        has_structure = any(marker in text for marker in ("1)", "2)", "\n- ", "\n1."))
        has_operational_signal = any(
            token in normalized
            for token in (
                "paso",
                "prior",
                "accion",
                "verificacion",
                "fuente",
                "evidencia",
            )
        )
        return has_structure and has_operational_signal

    @classmethod
    def _has_source_grounding_in_answer(
        cls,
        *,
        answer: str,
        knowledge_sources: list[dict[str, str]],
    ) -> bool:
        if not knowledge_sources:
            return True
        normalized_answer = cls._normalize(answer)
        matched_references: set[str] = set()
        available_references = 0
        for source in knowledge_sources[:6]:
            title = cls._normalize(str(source.get("title") or ""))
            locator = cls._normalize(str(source.get("source") or ""))
            has_reference = bool(title or locator)
            if has_reference:
                available_references += 1
            if title and title in normalized_answer:
                matched_references.add(f"title:{title}")
            if locator:
                tail = locator.split("/")[-1].split("\\")[-1]
                tail = cls._normalize(tail.replace(".md", "").replace(".txt", ""))
                if tail and tail in normalized_answer:
                    matched_references.add(f"tail:{tail}")
        if available_references == 0:
            return True
        required_matches = 2 if available_references >= 2 else 1
        return len(matched_references) >= required_matches

    @classmethod
    def create_message(
        cls,
        db: Session,
        *,
        care_task: CareTask,
        payload: CareTaskClinicalChatMessageRequest,
        authenticated_user: User | None,
    ) -> tuple[
        CareTaskChatMessage,
        int,
        str,
        list[str],
        str,
        str,
        dict[str, float | str],
        str,
        list[dict[str, str]],
    ]:
        session_id = cls._safe_session_id(payload.session_id)
        safe_query, prompt_injection_signals = cls._sanitize_user_query(payload.query)
        effective_specialty = cls._resolve_effective_specialty(
            payload=payload,
            care_task=care_task,
            authenticated_user=authenticated_user,
            query=safe_query,
        )
        recent_messages = cls._list_recent_messages(
            db,
            care_task_id=care_task.id,
            session_id=session_id,
            limit=payload.max_history_messages,
        )
        recent_dialogue = [
            {
                "user_query": message.user_query,
                "assistant_answer": message.assistant_answer,
            }
            for message in reversed(recent_messages[:8])
        ]
        effective_query, query_expanded = cls._compose_effective_query(
            query=safe_query,
            recent_dialogue=recent_dialogue,
        )
        dialog_state = cls._resolve_dialog_state(
            query=safe_query,
            recent_dialogue=recent_dialogue,
        )
        parsed_intent = str(dialog_state.get("intent") or "general")
        parsed_entity = str(dialog_state.get("entity") or "")
        if parsed_entity and "dosis" in cls._normalize(safe_query):
            effective_query = (
                f"{effective_query}. Entidad foco para dosis: {parsed_entity}"
            )
        fact_counter: Counter[str] = Counter()
        for history_message in recent_messages:
            filtered_facts = [
                fact
                for fact in (history_message.extracted_facts or [])
                if cls._filter_memory_fact(fact)
            ]
            fact_counter.update(filtered_facts)
        session_memory_facts = [fact for fact, _ in fact_counter.most_common(5)]

        patient_summary = None
        patient_history_facts_used: list[str] = []
        if payload.use_patient_history:
            patient_summary = cls._build_patient_summary(
                db,
                patient_reference=care_task.patient_reference,
                max_messages=payload.max_patient_history_messages,
            )
            if patient_summary is not None:
                patient_history_facts_used = [
                    fact
                    for fact in patient_summary["patient_top_extracted_facts"]
                    if cls._filter_memory_fact(fact)
                ][:5]
        memory_facts_used: list[str] = []
        for fact in session_memory_facts + patient_history_facts_used:
            if fact not in memory_facts_used:
                memory_facts_used.append(fact)

        keyword_hits = cls._count_domain_keyword_hits(effective_query)
        matched_domain_records = cls._match_domains(
            query=effective_query,
            effective_specialty=effective_specialty,
            max_domains=3,
        )
        matched_domains = [str(domain["key"]) for domain in matched_domain_records]
        matched_endpoints = [
            str(domain["endpoint"]).format(task_id=care_task.id)
            for domain in matched_domain_records
        ]
        extracted_facts = cls._extract_facts(safe_query) if payload.persist_extracted_facts else []
        extracted_facts.append(f"dst_intent:{parsed_intent}")
        if parsed_entity:
            extracted_facts.append(f"dst_entity:{parsed_entity}")
        local_evidence_sources, local_evidence_facts, local_evidence_trace = (
            cls._build_local_evidence_context(payload)
        )

        requested_tool_mode = "chat"
        provisional_response_mode = cls._resolve_response_mode(
            payload=payload,
            query=safe_query,
            extracted_facts=extracted_facts,
            keyword_hits=keyword_hits,
            tool_mode=requested_tool_mode,
        )
        risk_assessment = assess_tool_risk(
            tool_mode=requested_tool_mode,
            response_mode=provisional_response_mode,
            prompt_injection_detected=bool(prompt_injection_signals),
            use_web_sources=payload.use_web_sources,
        )
        policy_decision = ToolPolicyPipeline.evaluate(
            ToolPolicyContext(
                requested_tool_mode=requested_tool_mode,
                response_mode=provisional_response_mode,
                user_is_superuser=bool(authenticated_user and authenticated_user.is_superuser),
                prompt_injection_detected=bool(prompt_injection_signals),
                human_review_required=bool(care_task.human_review_required),
                use_web_sources=payload.use_web_sources,
                include_protocol_catalog=payload.include_protocol_catalog,
            )
        )
        tool_mode = "chat"
        response_mode = cls._resolve_response_mode(
            payload=payload,
            query=safe_query,
            extracted_facts=extracted_facts,
            keyword_hits=keyword_hits,
            tool_mode=tool_mode,
        )
        pipeline_relaxed_mode = bool(payload.pipeline_relaxed_mode)
        pipeline_profile = "evaluation" if pipeline_relaxed_mode else "strict"
        if response_mode != "clinical":
            # En modo general no se debe forzar enrutado clinico ni inyectar catalogo medico.
            matched_domain_records = []
            matched_domains = []
            matched_endpoints = []

        extracted_facts.append(f"modo_respuesta:{response_mode}")
        extracted_facts.extend(local_evidence_facts)
        extracted_facts.append(f"herramienta_solicitada:{requested_tool_mode}")
        extracted_facts.append(f"herramienta:{tool_mode}")
        if not policy_decision.allowed:
            extracted_facts.append(f"tool_policy:{policy_decision.reason_code}")

        math_assessment = ClinicalMathInferenceService.analyze_query(
            query=safe_query,
            matched_domains=matched_domains,
            effective_specialty=effective_specialty,
            extracted_facts=extracted_facts,
            memory_facts_used=memory_facts_used,
        )
        vector_assessment = ClinicalVectorClassificationService.analyze_query(
            query=safe_query,
            domain_catalog=cls._DOMAIN_CATALOG,
            matched_domains=matched_domains,
            effective_specialty=effective_specialty,
        )
        cluster_assessment = ClinicalFlatClusteringService.analyze_query(
            query=safe_query,
            domain_catalog=cls._DOMAIN_CATALOG,
            matched_domains=matched_domains,
            effective_specialty=effective_specialty,
        )
        hcluster_assessment = ClinicalHierarchicalClusteringService.analyze_query(
            query=safe_query,
            domain_catalog=cls._DOMAIN_CATALOG,
            matched_domains=matched_domains,
            effective_specialty=effective_specialty,
        )
        svm_domain_assessment = ClinicalSVMDomainService.analyze_query(
            query=safe_query,
            domain_catalog=cls._DOMAIN_CATALOG,
            matched_domains=matched_domains,
            effective_specialty=effective_specialty,
        )
        naive_bayes_assessment = ClinicalNaiveBayesService.analyze_query(
            query=safe_query,
            domain_catalog=cls._DOMAIN_CATALOG,
            matched_domains=matched_domains,
            effective_specialty=effective_specialty,
        )
        risk_pipeline_assessment = ClinicalRiskPipelineService.analyze_query(
            query=safe_query,
            matched_domains=matched_domains,
            effective_specialty=effective_specialty,
            extracted_facts=extracted_facts,
        )
        svm_assessment = ClinicalSVMTriageService.analyze_query(
            query=safe_query,
            matched_domains=matched_domains,
            effective_specialty=effective_specialty,
            extracted_facts=extracted_facts,
            memory_facts_used=memory_facts_used,
        )
        matched_domain_records = cls._apply_math_domain_rerank(
            matched_domain_records=matched_domain_records,
            math_assessment=math_assessment,
            max_domains=3,
        )
        matched_domain_records = cls._apply_cluster_domain_rerank(
            matched_domain_records=matched_domain_records,
            cluster_assessment=cluster_assessment,
            math_assessment=math_assessment,
            max_domains=3,
        )
        matched_domain_records = cls._apply_hcluster_domain_rerank(
            matched_domain_records=matched_domain_records,
            hcluster_assessment=hcluster_assessment,
            math_assessment=math_assessment,
            max_domains=3,
        )
        matched_domain_records = cls._apply_vector_domain_rerank(
            matched_domain_records=matched_domain_records,
            vector_assessment=vector_assessment,
            math_assessment=math_assessment,
            max_domains=3,
        )
        matched_domain_records = cls._apply_svm_domain_rerank(
            matched_domain_records=matched_domain_records,
            svm_domain_assessment=svm_domain_assessment,
            math_assessment=math_assessment,
            max_domains=3,
        )
        matched_domain_records = cls._apply_naive_bayes_domain_rerank(
            matched_domain_records=matched_domain_records,
            naive_bayes_assessment=naive_bayes_assessment,
            math_assessment=math_assessment,
            max_domains=3,
        )
        matched_domains = [str(domain["key"]) for domain in matched_domain_records]
        matched_endpoints = [
            str(domain["endpoint"]).format(task_id=care_task.id)
            for domain in matched_domain_records
        ]
        if math_assessment.get("enabled"):
            extracted_facts.append(
                f"math_top_domain:{str(math_assessment.get('top_domain') or 'none')}"
            )
            extracted_facts.append(
                f"math_priority_score:{str(math_assessment.get('priority_score') or 'low')}"
            )
        if risk_pipeline_assessment.get("enabled"):
            extracted_facts.append(
                f"risk_probability:{str(risk_pipeline_assessment.get('probability') or 0.0)}"
            )
            extracted_facts.append(
                f"risk_priority:{str(risk_pipeline_assessment.get('priority') or 'low')}"
            )
            if bool(risk_pipeline_assessment.get("anomaly_flag")):
                extracted_facts.append("risk_anomaly:1")
            for memory_fact in list(risk_pipeline_assessment.get("memory_facts", []))[:3]:
                if memory_fact not in memory_facts_used:
                    memory_facts_used.append(memory_fact)
        if svm_assessment.get("enabled"):
            extracted_facts.append(
                f"svm_class:{str(svm_assessment.get('predicted_class') or 'stable')}"
            )
            extracted_facts.append(
                f"svm_priority:{str(svm_assessment.get('priority_score') or 'low')}"
            )
            for memory_fact in list(svm_assessment.get("memory_facts", []))[:2]:
                if memory_fact not in memory_facts_used:
                    memory_facts_used.append(memory_fact)
        if svm_domain_assessment.get("enabled"):
            extracted_facts.append(
                f"svm_domain_top:{str(svm_domain_assessment.get('top_domain') or 'none')}"
            )
            extracted_facts.append(
                "svm_domain_probability:"
                f"{str(svm_domain_assessment.get('top_probability') or 0.0)}"
            )
            for memory_fact in list(svm_domain_assessment.get("memory_facts", []))[:2]:
                if memory_fact not in memory_facts_used:
                    memory_facts_used.append(memory_fact)
        if cluster_assessment.get("enabled"):
            extracted_facts.append(
                f"cluster_top_id:{str(cluster_assessment.get('top_cluster_id') or -1)}"
            )
            extracted_facts.append(
                f"cluster_top_confidence:{str(cluster_assessment.get('top_confidence') or 0.0)}"
            )
            for memory_fact in list(cluster_assessment.get("memory_facts", []))[:2]:
                if memory_fact not in memory_facts_used:
                    memory_facts_used.append(memory_fact)
        if hcluster_assessment.get("enabled"):
            extracted_facts.append(
                f"hcluster_top_id:{str(hcluster_assessment.get('top_cluster_id') or -1)}"
            )
            extracted_facts.append(
                "hcluster_top_confidence:"
                f"{str(hcluster_assessment.get('top_confidence') or 0.0)}"
            )
            for memory_fact in list(hcluster_assessment.get("memory_facts", []))[:2]:
                if memory_fact not in memory_facts_used:
                    memory_facts_used.append(memory_fact)
        if naive_bayes_assessment.get("enabled"):
            extracted_facts.append(
                f"nb_top_domain:{str(naive_bayes_assessment.get('top_domain') or 'none')}"
            )
            extracted_facts.append(
                f"nb_top_probability:{str(naive_bayes_assessment.get('top_probability') or 0.0)}"
            )
            for memory_fact in list(naive_bayes_assessment.get("memory_facts", []))[:2]:
                if memory_fact not in memory_facts_used:
                    memory_facts_used.append(memory_fact)
        if vector_assessment.get("enabled"):
            extracted_facts.append(
                f"vector_top_domain:{str(vector_assessment.get('top_domain') or 'none')}"
            )
            extracted_facts.append(
                f"vector_top_probability:{str(vector_assessment.get('top_probability') or 0.0)}"
            )
            for memory_fact in list(vector_assessment.get("memory_facts", []))[:2]:
                if memory_fact not in memory_facts_used:
                    memory_facts_used.append(memory_fact)
        decision_psychology = ClinicalDecisionPsychologyService.analyze_query(
            query=safe_query,
            matched_domains=matched_domains,
            effective_specialty=effective_specialty,
        )
        extracted_facts.append(f"risk_level:{decision_psychology['risk_level']}")
        extracted_facts.append(f"risk_frame:{decision_psychology['prospect_frame']}")
        if decision_psychology.get("fechner_intensity") is not None:
            extracted_facts.append(
                f"fechner_intensity:{float(decision_psychology['fechner_intensity']):.3f}"
            )
        if decision_psychology.get("fechner_change") is not None:
            extracted_facts.append(
                f"fechner_change:{float(decision_psychology['fechner_change']):.3f}"
            )
        for memory_fact in list(decision_psychology.get("memory_facts", []))[:4]:
            if memory_fact not in memory_facts_used:
                memory_facts_used.append(memory_fact)
        logic_assessment = ClinicalLogicEngineService.analyze_query(
            query=safe_query,
            matched_domains=matched_domains,
            effective_specialty=effective_specialty,
            extracted_facts=extracted_facts,
            memory_facts_used=memory_facts_used,
        )
        for rule in logic_assessment.get("rules_triggered", [])[:4]:
            rule_id = str(rule.get("id") or "")
            if rule_id:
                extracted_facts.append(f"logic_rule:{rule_id}")
        if logic_assessment.get("contradictions"):
            extracted_facts.append(
                f"logic_contradictions:{len(logic_assessment.get('contradictions', []))}"
            )
        consistency_status = str(logic_assessment.get("consistency_status") or "consistent")
        if consistency_status != "consistent":
            extracted_facts.append(f"logic_consistency:{consistency_status}")
        if bool(logic_assessment.get("abstention_required")):
            extracted_facts.append("logic_abstention:1")
        for action in logic_assessment.get("recommended_actions", [])[:4]:
            memory_fact = f"logic_action:{action}"
            if memory_fact not in memory_facts_used:
                memory_facts_used.append(memory_fact)
        contract_assessment = ClinicalProtocolContractsService.evaluate(
            query=safe_query,
            effective_specialty=effective_specialty,
            matched_domains=matched_domains,
            extracted_facts=extracted_facts,
            memory_facts_used=memory_facts_used,
            logic_assessment=logic_assessment,
        )
        if contract_assessment.get("contract_applied"):
            contract_domain = str(contract_assessment.get("contract_domain") or "")
            contract_state = str(contract_assessment.get("contract_state") or "")
            contract_id = str(contract_assessment.get("contract_id") or "")
            if contract_domain:
                extracted_facts.append(f"contract_domain:{contract_domain}")
            if contract_state:
                extracted_facts.append(f"contract_state:{contract_state}")
            if contract_id:
                extracted_facts.append(f"contract_id:{contract_id}")
            for item in list(contract_assessment.get("missing_data") or [])[:3]:
                memory_fact = f"contract_missing:{item}"
                if memory_fact not in memory_facts_used:
                    memory_facts_used.append(memory_fact)

        ambiguity_gate = cls._assess_query_ambiguity(
            query=safe_query,
            parsed_intent=parsed_intent,
            keyword_hits=keyword_hits,
            extracted_facts=extracted_facts,
        )
        cir_clarification_triggered = False
        cir_suggested_queries: list[str] = []
        interrogatory_result: dict[str, Any] = {"should_ask": False, "reason": "disabled"}
        interrogatory_short_circuit = False
        if (
            payload.enable_active_interrogation
            and response_mode == "clinical"
            and tool_mode == "chat"
        ):
            interrogatory_result = DiagnosticInterrogatoryService.propose_next_question(
                query=safe_query,
                effective_specialty=effective_specialty,
                matched_domains=matched_domains,
                extracted_facts=extracted_facts,
                memory_facts_used=memory_facts_used,
                patient_history_facts_used=patient_history_facts_used,
                recent_messages=recent_messages,
                max_turns=payload.interrogation_max_turns,
                confidence_threshold=payload.interrogation_confidence_threshold,
            )
            interrogatory_short_circuit = bool(interrogatory_result.get("should_ask"))
            if interrogatory_short_circuit:
                extracted_facts.append(
                    f"clarify_question:{interrogatory_result.get('question_feature', '')}"
                )
                extracted_facts.append(
                    f"clarify_turn:{int(interrogatory_result.get('turn_index', 1))}"
                )
        if (
            not interrogatory_short_circuit
            and response_mode == "clinical"
            and tool_mode == "chat"
            and bool(ambiguity_gate.get("should_ask"))
        ):
            cir_clarification_triggered = True
            top_domain = str(
                (matched_domain_records[0].get("key") if matched_domain_records else "")
                or effective_specialty
                or "general"
            )
            cir_suggested_queries = cls._build_next_query_suggestions(
                query=safe_query,
                matched_domains=matched_domain_records,
                parsed_intent=parsed_intent,
                limit=3,
            )
            interrogatory_result = {
                "should_ask": True,
                "reason": "cir_ambiguity_gate",
                "domain": top_domain,
                "question": cls._pick_clarification_question(
                    domain_key=top_domain,
                    parsed_intent=parsed_intent,
                ),
                "question_feature": "cir_ambiguity_gate",
                "turn_index": 1,
                "max_turns": 1,
                "top_probability": round(max(0.0, 1.0 - float(ambiguity_gate["score"])), 4),
                "ambiguity_score": ambiguity_gate["score"],
                "suggested_queries": cir_suggested_queries,
            }
            interrogatory_short_circuit = True
            extracted_facts.append("clarify_question:cir_ambiguity_gate")
            extracted_facts.append("clarify_turn:1")
            extracted_facts.append(f"clarify_score:{ambiguity_gate['score']}")

        endpoint_recommendations: list[dict[str, Any]] = []
        if response_mode == "clinical" and not interrogatory_short_circuit:
            endpoint_recommendations = cls._fetch_recommendations(
                query=effective_query,
                matched_endpoints=matched_endpoints,
            )
            endpoint_recommendations = SessionToolResultGuard.sanitize(
                endpoint_recommendations,
                max_items=4,
            )

        if tool_mode in {"medication", "treatment", "cases"}:
            extracted_facts.append(f"tool_focus:{tool_mode}")
        unique_facts: list[str] = []
        for fact in extracted_facts:
            if fact not in unique_facts:
                unique_facts.append(fact)
        prioritized_facts = [
            fact
            for fact in unique_facts
            if fact.startswith("clarify_question:") or fact.startswith("clarify_turn:")
        ]
        if prioritized_facts and len(unique_facts) > 20:
            regular_facts = [fact for fact in unique_facts if fact not in prioritized_facts]
            keep_regular = max(0, 20 - len(prioritized_facts))
            extracted_facts = (regular_facts[:keep_regular] + prioritized_facts)[:20]
        else:
            extracted_facts = unique_facts[:20]

        internal_sources_limit = payload.max_internal_sources
        if interrogatory_short_circuit:
            internal_sources_limit = min(payload.max_internal_sources, 2)

        knowledge_sources: list[dict[str, str]] = []
        if response_mode == "clinical":
            knowledge_sources = cls._build_validated_knowledge_sources(
                db,
                query=effective_query,
                effective_specialty=effective_specialty,
                matched_domains=matched_domain_records,
                max_internal_sources=internal_sources_limit,
            )
            allow_catalog_fallback = (
                not settings.CLINICAL_CHAT_REQUIRE_VALIDATED_INTERNAL_SOURCES
                or settings.ENVIRONMENT == "development"
            )
            if not knowledge_sources and allow_catalog_fallback:
                knowledge_sources = cls._build_catalog_knowledge_sources(
                    query=effective_query,
                    matched_domains=matched_domain_records,
                    max_internal_sources=internal_sources_limit,
                )
        web_limit = payload.max_web_sources
        use_web_sources = (
            payload.use_web_sources and policy_decision.allowed and not interrogatory_short_circuit
        )
        if tool_mode == "deep_search":
            use_web_sources = True
            web_limit = max(payload.max_web_sources, 6)
        if requested_tool_mode == "deep_search" and tool_mode != "deep_search":
            use_web_sources = False
        web_trace: dict[str, str] = {}
        if use_web_sources:
            web_sources, web_trace = cls._fetch_web_sources(effective_query, web_limit)
        else:
            web_sources = []
        endpoint_sources = [
            {
                "type": "internal_recommendation",
                "title": str(item.get("title") or "Recomendacion interna"),
                "source": str(item.get("source") or "internal"),
                "snippet": str(item.get("snippet") or "")[:280],
            }
            for item in endpoint_recommendations
        ]
        if response_mode == "clinical":
            knowledge_sources = [*knowledge_sources, *endpoint_sources][
                : max(internal_sources_limit, 6)
            ]
        if local_evidence_sources:
            knowledge_sources = cls._merge_source_lists(
                local_evidence_sources,
                knowledge_sources,
                limit=max(payload.max_internal_sources, 10),
            )
        raw_internal_sources_count = len(knowledge_sources)
        if response_mode == "clinical":
            knowledge_sources = cls._filter_knowledge_sources_for_current_turn(
                query=effective_query,
                matched_domains=matched_domain_records,
                knowledge_sources=knowledge_sources,
            )
        security_findings = [
            item.to_dict()
            for item in audit_chat_security(
                prompt_injection_signals=prompt_injection_signals,
                risk=risk_assessment,
                tool_policy_allowed=policy_decision.allowed,
                tool_policy_reason=policy_decision.reason_code,
                response_mode=response_mode,
                internal_sources_count=len(knowledge_sources),
                validated_sources_required=settings.CLINICAL_CHAT_REQUIRE_VALIDATED_INTERNAL_SOURCES,
                use_web_sources=use_web_sources,
            )
        ]
        interpretability_trace = [
            f"query_length={len(payload.query)}",
            f"effective_specialty={effective_specialty}",
            "conversation_mode=intent_auto",
            f"response_mode={response_mode}",
            f"pipeline_profile={pipeline_profile}",
            f"requested_tool_mode={requested_tool_mode}",
            f"tool_mode={tool_mode}",
            f"tool_policy_decision={'allowed' if policy_decision.allowed else 'denied'}",
            f"tool_policy_reason={policy_decision.reason_code}",
            f"tool_risk_level={risk_assessment.risk_level}",
            "tool_risk_categories="
            + (",".join(risk_assessment.categories) if risk_assessment.categories else "none"),
            f"query_sanitized={1 if safe_query != payload.query.strip() else 0}",
            f"prompt_injection_detected={1 if prompt_injection_signals else 0}",
            "prompt_injection_signals="
            + (",".join(prompt_injection_signals) if prompt_injection_signals else "none"),
            f"query_expanded={1 if query_expanded else 0}",
            f"dst_intent={parsed_intent}",
            f"dst_entity={parsed_entity or 'none'}",
            f"keyword_hits={keyword_hits}",
            f"history_messages_used={len(recent_messages)}",
            f"patient_history_used={1 if patient_summary else 0}",
            f"matched_domains={','.join(matched_domains) if matched_domains else 'none'}",
            f"matched_endpoints={','.join(matched_endpoints) if matched_endpoints else 'none'}",
            f"internal_sources_pre_filter={raw_internal_sources_count}",
            f"internal_sources={len(knowledge_sources)}",
            f"web_sources={len(web_sources)}",
            f"endpoint_recommendations={len(endpoint_recommendations)}",
            "reasoning_threads=intent>context>sources>actions",
            "source_policy=internal_first_web_whitelist",
            *[f"{key}={value}" for key, value in web_trace.items()],
            f"memory_facts_used={len(memory_facts_used)}",
            f"extracted_facts={len(extracted_facts)}",
            f"security_findings_count={len(security_findings)}",
            "security_findings=" + ",".join(finding["code"] for finding in security_findings[:4]),
            *local_evidence_trace,
            f"interrogatory_enabled={1 if payload.enable_active_interrogation else 0}",
            f"interrogatory_active={1 if interrogatory_short_circuit else 0}",
            f"interrogatory_reason={interrogatory_result.get('reason', 'na')}",
            f"clarification_gate_triggered={1 if cir_clarification_triggered else 0}",
            f"clarification_gate_score={ambiguity_gate.get('score', 0.0)}",
            f"clarification_gate_reason={ambiguity_gate.get('reason', 'na')}",
            f"clarification_suggestions={len(cir_suggested_queries)}",
            "psychology_enabled=1",
            f"prospect_risk_level={decision_psychology['risk_level']}",
            f"prospect_frame={decision_psychology['prospect_frame']}",
            f"prospect_risk_score={decision_psychology['risk_score']}",
            "prospect_signals="
            + (
                ",".join(str(item) for item in decision_psychology.get("signals", []))
                if decision_psychology.get("signals")
                else "none"
            ),
            "fechner_intensity="
            + (
                str(decision_psychology["fechner_intensity"])
                if decision_psychology.get("fechner_intensity") is not None
                else "na"
            ),
            "fechner_change="
            + (
                str(decision_psychology["fechner_change"])
                if decision_psychology.get("fechner_change") is not None
                else "na"
            ),
            f"logic_enabled={logic_assessment['trace']['logic_enabled']}",
            f"logic_rules_fired={logic_assessment['trace']['logic_rules_fired']}",
            f"logic_contradictions={logic_assessment['trace']['logic_contradictions']}",
            f"logic_epistemic_facts={logic_assessment['trace']['logic_epistemic_facts']}",
            f"logic_rule_ids={logic_assessment['trace']['logic_rule_ids']}",
            f"logic_consistency_status={logic_assessment['trace']['logic_consistency_status']}",
            f"logic_abstention_required={logic_assessment['trace']['logic_abstention_required']}",
            f"logic_abstention_reason={logic_assessment['trace']['logic_abstention_reason']}",
            f"logic_evidence_items={logic_assessment['trace']['logic_evidence_items']}",
            f"logic_structural_steps={logic_assessment['trace']['logic_structural_steps']}",
            f"logic_godel_code={logic_assessment['trace']['logic_godel_code']}",
            f"logic_godel_roundtrip={logic_assessment['trace']['logic_godel_roundtrip']}",
            f"logic_beta_signature={logic_assessment['trace']['logic_beta_signature']}",
            f"logic_first_escalation_step={logic_assessment['trace']['logic_first_escalation_step']}",
            f"contract_enabled={contract_assessment['trace']['contract_enabled']}",
            f"contract_domain={contract_assessment['trace']['contract_domain']}",
            f"contract_id={contract_assessment['trace']['contract_id']}",
            f"contract_state={contract_assessment['trace']['contract_state']}",
            f"contract_has_trigger={contract_assessment['trace']['contract_has_trigger']}",
            f"contract_missing_data_count={contract_assessment['trace']['contract_missing_data_count']}",
            f"contract_force_fallback={contract_assessment['trace']['contract_force_fallback']}",
            f"math_enabled={math_assessment['trace']['math_enabled']}",
            f"math_top_domain={math_assessment['trace']['math_top_domain']}",
            f"math_top_probability={math_assessment['trace']['math_top_probability']}",
            f"math_margin_top2={math_assessment['trace']['math_margin_top2']}",
            f"math_entropy={math_assessment['trace']['math_entropy']}",
            f"math_posterior_variance={math_assessment['trace']['math_posterior_variance']}",
            f"math_uncertainty_level={math_assessment['trace']['math_uncertainty_level']}",
            f"math_abstention_recommended={math_assessment['trace']['math_abstention_recommended']}",
            f"math_priority_score={math_assessment['trace']['math_priority_score']}",
            f"math_ood_score={math_assessment['trace']['math_ood_score']}",
            f"math_ood_level={math_assessment['trace']['math_ood_level']}",
            f"math_domains_evaluated={math_assessment['trace']['math_domains_evaluated']}",
            f"math_model={math_assessment['trace']['math_model']}",
            f"risk_pipeline_enabled={risk_pipeline_assessment['trace']['risk_pipeline_enabled']}",
            f"risk_model_linear_score={risk_pipeline_assessment['trace']['risk_model_linear_score']}",
            f"risk_model_probability={risk_pipeline_assessment['trace']['risk_model_probability']}",
            f"risk_model_priority={risk_pipeline_assessment['trace']['risk_model_priority']}",
            f"risk_model_features_missing={risk_pipeline_assessment['trace']['risk_model_features_missing']}",
            f"risk_model_anomaly_score={risk_pipeline_assessment['trace']['risk_model_anomaly_score']}",
            f"risk_model_anomaly_flag={risk_pipeline_assessment['trace']['risk_model_anomaly_flag']}",
            f"svm_enabled={svm_assessment['trace']['svm_enabled']}",
            f"svm_score={svm_assessment['trace']['svm_score']}",
            f"svm_margin={svm_assessment['trace']['svm_margin']}",
            f"svm_hinge_loss={svm_assessment['trace']['svm_hinge_loss']}",
            f"svm_class={svm_assessment['trace']['svm_class']}",
            f"svm_priority_score={svm_assessment['trace']['svm_priority_score']}",
            f"svm_support_signals={svm_assessment['trace']['svm_support_signals']}",
            f"cluster_enabled={cluster_assessment['trace']['cluster_enabled']}",
            f"cluster_method={cluster_assessment['trace']['cluster_method']}",
            f"cluster_k_selected={cluster_assessment['trace']['cluster_k_selected']}",
            f"cluster_k_min={cluster_assessment['trace']['cluster_k_min']}",
            f"cluster_k_max={cluster_assessment['trace']['cluster_k_max']}",
            f"cluster_top_id={cluster_assessment['trace']['cluster_top_id']}",
            f"cluster_top_confidence={cluster_assessment['trace']['cluster_top_confidence']}",
            f"cluster_margin_top2={cluster_assessment['trace']['cluster_margin_top2']}",
            f"cluster_entropy={cluster_assessment['trace']['cluster_entropy']}",
            f"cluster_candidate_domains={cluster_assessment['trace']['cluster_candidate_domains']}",
            f"cluster_singletons={cluster_assessment['trace']['cluster_singletons']}",
            f"cluster_rss={cluster_assessment['trace']['cluster_rss']}",
            f"cluster_aic={cluster_assessment['trace']['cluster_aic']}",
            f"cluster_purity={cluster_assessment['trace']['cluster_purity']}",
            f"cluster_nmi={cluster_assessment['trace']['cluster_nmi']}",
            f"cluster_rand_index={cluster_assessment['trace']['cluster_rand_index']}",
            f"cluster_f_measure={cluster_assessment['trace']['cluster_f_measure']}",
            f"cluster_vocab_size={cluster_assessment['trace']['cluster_vocab_size']}",
            f"cluster_training_docs={cluster_assessment['trace']['cluster_training_docs']}",
            (
                "cluster_rerank_recommended="
                f"{cluster_assessment['trace']['cluster_rerank_recommended']}"
            ),
            f"hcluster_enabled={hcluster_assessment['trace']['hcluster_enabled']}",
            f"hcluster_method={hcluster_assessment['trace']['hcluster_method']}",
            f"hcluster_strategy={hcluster_assessment['trace']['hcluster_strategy']}",
            f"hcluster_linkage={hcluster_assessment['trace']['hcluster_linkage']}",
            f"hcluster_k_selected={hcluster_assessment['trace']['hcluster_k_selected']}",
            f"hcluster_k_min={hcluster_assessment['trace']['hcluster_k_min']}",
            f"hcluster_k_max={hcluster_assessment['trace']['hcluster_k_max']}",
            f"hcluster_top_id={hcluster_assessment['trace']['hcluster_top_id']}",
            (
                "hcluster_top_confidence="
                f"{hcluster_assessment['trace']['hcluster_top_confidence']}"
            ),
            f"hcluster_margin_top2={hcluster_assessment['trace']['hcluster_margin_top2']}",
            f"hcluster_entropy={hcluster_assessment['trace']['hcluster_entropy']}",
            (
                "hcluster_candidate_domains="
                f"{hcluster_assessment['trace']['hcluster_candidate_domains']}"
            ),
            f"hcluster_singletons={hcluster_assessment['trace']['hcluster_singletons']}",
            f"hcluster_merge_steps={hcluster_assessment['trace']['hcluster_merge_steps']}",
            f"hcluster_sample_size={hcluster_assessment['trace']['hcluster_sample_size']}",
            f"hcluster_purity={hcluster_assessment['trace']['hcluster_purity']}",
            f"hcluster_nmi={hcluster_assessment['trace']['hcluster_nmi']}",
            f"hcluster_rand_index={hcluster_assessment['trace']['hcluster_rand_index']}",
            f"hcluster_f_measure={hcluster_assessment['trace']['hcluster_f_measure']}",
            f"hcluster_vocab_size={hcluster_assessment['trace']['hcluster_vocab_size']}",
            (
                "hcluster_training_docs="
                f"{hcluster_assessment['trace']['hcluster_training_docs']}"
            ),
            (
                "hcluster_rerank_recommended="
                f"{hcluster_assessment['trace']['hcluster_rerank_recommended']}"
            ),
            f"svm_domain_enabled={svm_domain_assessment['trace']['svm_domain_enabled']}",
            f"svm_domain_method={svm_domain_assessment['trace']['svm_domain_method']}",
            f"svm_domain_c={svm_domain_assessment['trace']['svm_domain_c']}",
            f"svm_domain_l2={svm_domain_assessment['trace']['svm_domain_l2']}",
            f"svm_domain_epochs={svm_domain_assessment['trace']['svm_domain_epochs']}",
            f"svm_domain_top_domain={svm_domain_assessment['trace']['svm_domain_top_domain']}",
            (
                "svm_domain_top_probability="
                f"{svm_domain_assessment['trace']['svm_domain_top_probability']}"
            ),
            (
                "svm_domain_margin_top2="
                f"{svm_domain_assessment['trace']['svm_domain_margin_top2']}"
            ),
            f"svm_domain_entropy={svm_domain_assessment['trace']['svm_domain_entropy']}",
            (
                "svm_domain_support_vectors="
                f"{svm_domain_assessment['trace']['svm_domain_support_vectors']}"
            ),
            (
                "svm_domain_avg_hinge_loss="
                f"{svm_domain_assessment['trace']['svm_domain_avg_hinge_loss']}"
            ),
            f"svm_domain_vocab_size={svm_domain_assessment['trace']['svm_domain_vocab_size']}",
            f"svm_domain_classes={svm_domain_assessment['trace']['svm_domain_classes']}",
            (
                "svm_domain_training_docs="
                f"{svm_domain_assessment['trace']['svm_domain_training_docs']}"
            ),
            (
                "svm_domain_rerank_recommended="
                f"{svm_domain_assessment['trace']['svm_domain_rerank_recommended']}"
            ),
            (
                "svm_domain_support_terms="
                f"{svm_domain_assessment['trace']['svm_domain_support_terms']}"
            ),
            f"vector_enabled={vector_assessment['trace']['vector_enabled']}",
            f"vector_method={vector_assessment['trace']['vector_method']}",
            f"vector_k={vector_assessment['trace']['vector_k']}",
            f"vector_top_domain={vector_assessment['trace']['vector_top_domain']}",
            f"vector_top_probability={vector_assessment['trace']['vector_top_probability']}",
            f"vector_margin_top2={vector_assessment['trace']['vector_margin_top2']}",
            f"vector_entropy={vector_assessment['trace']['vector_entropy']}",
            f"vector_tokens={vector_assessment['trace']['vector_tokens']}",
            f"vector_vocab_size={vector_assessment['trace']['vector_vocab_size']}",
            f"vector_classes={vector_assessment['trace']['vector_classes']}",
            f"vector_training_docs={vector_assessment['trace']['vector_training_docs']}",
            (
                "vector_rerank_recommended="
                f"{vector_assessment['trace']['vector_rerank_recommended']}"
            ),
            f"nb_enabled={naive_bayes_assessment['trace']['nb_enabled']}",
            f"nb_model={naive_bayes_assessment['trace']['nb_model']}",
            f"nb_alpha={naive_bayes_assessment['trace']['nb_alpha']}",
            f"nb_top_domain={naive_bayes_assessment['trace']['nb_top_domain']}",
            f"nb_top_probability={naive_bayes_assessment['trace']['nb_top_probability']}",
            f"nb_margin_top2={naive_bayes_assessment['trace']['nb_margin_top2']}",
            f"nb_entropy={naive_bayes_assessment['trace']['nb_entropy']}",
            f"nb_tokens={naive_bayes_assessment['trace']['nb_tokens']}",
            f"nb_vocab_size={naive_bayes_assessment['trace']['nb_vocab_size']}",
            f"nb_classes={naive_bayes_assessment['trace']['nb_classes']}",
            f"nb_features_selected={naive_bayes_assessment['trace']['nb_features_selected']}",
            f"nb_rerank_recommended={naive_bayes_assessment['trace']['nb_rerank_recommended']}",
        ]
        if interrogatory_result:
            if "domain" in interrogatory_result:
                interpretability_trace.append(f"interrogatory_domain={interrogatory_result['domain']}")
            if "deig_score" in interrogatory_result:
                interpretability_trace.append(
                    f"deig_score={round(float(interrogatory_result['deig_score']), 4)}"
                )
            if "entropy_before" in interrogatory_result:
                interpretability_trace.append(
                    f"interrogatory_entropy={interrogatory_result['entropy_before']}"
                )
            if "top_probability" in interrogatory_result:
                interpretability_trace.append(
                    f"interrogatory_top_probability={interrogatory_result['top_probability']}"
                )
        interpretability_trace.extend(policy_decision.trace)
        rag_trace: dict[str, Any] = {}
        llm_trace: dict[str, Any] = {}
        guardrails_trace: dict[str, str] = {}
        llm_answer: str | None = None
        rag_candidate_answer: str | None = None
        rag_validation_status = "unknown"
        rag_answer_authoritative = False

        if response_mode == "clinical":
            interpretability_trace.append(
                f"rag_enabled={1 if settings.CLINICAL_CHAT_RAG_ENABLED else 0}"
            )

        if interrogatory_short_circuit:
            llm_answer = cls._render_clarifying_question_answer(
                question_text=str(
                    interrogatory_result.get("question") or "Amplia datos clinicos clave."
                ),
                domain=str(interrogatory_result.get("domain") or effective_specialty),
                turn_index=int(interrogatory_result.get("turn_index") or 1),
                max_turns=int(
                    interrogatory_result.get("max_turns") or payload.interrogation_max_turns
                ),
                top_probability=float(interrogatory_result.get("top_probability") or 0.0),
                suggested_queries=[
                    str(item)
                    for item in list(interrogatory_result.get("suggested_queries") or [])[:3]
                    if str(item).strip()
                ],
            )
            llm_trace = {
                "llm_used": "false",
                "llm_provider": "interrogatory",
                "llm_endpoint": "clarifying_question",
            }
            guardrails_trace = {"guardrails_status": "skipped_interrogatory"}
        elif response_mode == "clinical" and settings.CLINICAL_CHAT_RAG_ENABLED:
            rag_answer, rag_trace = RAGOrchestrator(db=db).process_query_with_rag(
                query=effective_query,
                response_mode=response_mode,
                effective_specialty=effective_specialty,
                tool_mode=tool_mode,
                matched_domains=matched_domains,
                matched_endpoints=matched_endpoints,
                memory_facts_used=memory_facts_used,
                patient_summary=patient_summary,
                patient_history_facts_used=patient_history_facts_used,
                knowledge_sources=knowledge_sources,
                web_sources=web_sources,
                recent_dialogue=recent_dialogue,
                endpoint_results=endpoint_recommendations,
                care_task_id=care_task.id,
                pipeline_relaxed_mode=pipeline_relaxed_mode,
            )
            rag_sources = rag_trace.get("rag_sources")
            rag_extractive_llm_failure = (
                str(rag_trace.get("rag_generation_mode", "")).startswith("extractive_")
                and str(rag_trace.get("llm_used", "false")) == "false"
                and bool(str(rag_trace.get("llm_error") or "").strip())
            )
            if isinstance(rag_sources, list):
                normalized_rag_sources: list[dict[str, str]] = []
                for item in rag_sources:
                    if isinstance(item, dict):
                        source_locator = str(item.get("source") or "catalogo interno")
                        if not cls._is_clinical_source_locator(source_locator):
                            continue
                        normalized_rag_sources.append(
                            {
                                "type": str(item.get("type") or "rag_chunk"),
                                "title": str(item.get("title") or "Fragmento RAG"),
                                "source": source_locator,
                                "snippet": str(item.get("snippet") or "")[:360],
                                "url": str(item.get("url") or ""),
                            }
                        )
                if rag_extractive_llm_failure and knowledge_sources:
                    interpretability_trace.append(
                        "rag_sources_merge=skipped_extract_fallback_prefers_catalog"
                    )
                else:
                    knowledge_sources = cls._merge_source_lists(
                        knowledge_sources,
                        normalized_rag_sources,
                        limit=max(payload.max_internal_sources, 8),
                    )
                    knowledge_sources = cls._filter_knowledge_sources_for_current_turn(
                        query=effective_query,
                        matched_domains=matched_domain_records,
                        knowledge_sources=knowledge_sources,
                    )
            if rag_answer:
                rag_candidate_answer = rag_answer
                rag_llm_trace = {
                    str(key): str(value)
                    for key, value in rag_trace.items()
                    if isinstance(key, str) and key.startswith("llm_")
                }
                rag_validation_status = str(rag_trace.get("rag_validation_status", "valid"))
                if rag_llm_trace.get("llm_used") == "true":
                    llm_answer = rag_answer
                    llm_trace.update(rag_llm_trace)
                    llm_trace.setdefault("llm_origin", "rag_orchestrator")
                elif rag_llm_trace:
                    llm_trace.update(rag_llm_trace)
                elif settings.CLINICAL_CHAT_LLM_ENABLED:
                    knowledge_sources = cls._merge_source_lists(
                        knowledge_sources,
                        [
                            {
                                "type": "rag_summary",
                                "title": "Sintesis RAG interna",
                                "source": "rag_orchestrator",
                                "snippet": str(rag_answer)[:360],
                                "url": "",
                            }
                        ],
                        limit=max(payload.max_internal_sources, 8),
                    )
                    interpretability_trace.append("rag_answer_buffered_for_llm_synthesis=1")
                else:
                    llm_answer = rag_answer
                if (
                    str(rag_trace.get("rag_status") or "") == "success"
                    and not rag_llm_trace
                    and rag_validation_status == "valid"
                ):
                    rag_answer_authoritative = True
                    llm_trace.setdefault("llm_used", "false")
                    llm_trace.setdefault("llm_provider", "rag_orchestrator")
                    llm_trace.setdefault("llm_endpoint", "retrieval_answer")
                    llm_trace.setdefault("llm_origin", "rag_orchestrator")

        uncertainty_gate_triggered = False
        uncertainty_gate_reason = "none"
        variance_threshold = settings.CLINICAL_CHAT_UNCERTAINTY_GATE_MAX_VARIANCE
        ood_score = float(math_assessment.get("ood_score") or 0.0)
        ood_level = str(math_assessment.get("ood_level") or "high")
        uncertainty_gate_enabled = bool(
            settings.CLINICAL_CHAT_UNCERTAINTY_GATE_ENABLED and not pipeline_relaxed_mode
        )
        if (
            response_mode == "clinical"
            and not interrogatory_short_circuit
            and not pipeline_relaxed_mode
            and uncertainty_gate_enabled
            and str(rag_trace.get("rag_status") or "") != "failed_exception"
        ):
            posterior_variance = float(math_assessment.get("posterior_variance_top") or 0.0)
            top_domain = str(math_assessment.get("top_domain") or "")
            variance_threshold = cls._variance_threshold_for_domain(top_domain)
            uncertainty_level = str(math_assessment.get("uncertainty_level") or "high")
            has_internal_evidence = len(knowledge_sources) > 0
            rag_success = str(rag_trace.get("rag_status") or "") == "success"
            if posterior_variance >= variance_threshold or ood_level == "high":
                if not has_internal_evidence:
                    llm_answer = cls._render_uncertainty_gate_answer(
                        query=safe_query,
                        top_domain=top_domain,
                        posterior_variance=posterior_variance,
                    )
                    llm_trace["llm_used"] = llm_trace.get("llm_used", "false")
                    llm_trace["llm_provider"] = "uncertainty_gate"
                    llm_trace["llm_endpoint"] = llm_trace.get(
                        "llm_endpoint",
                        "abstain_insufficient_evidence",
                    )
                    uncertainty_gate_triggered = True
                    uncertainty_gate_reason = (
                        "high_variance_no_evidence"
                        if posterior_variance >= variance_threshold
                        else "ood_high_no_evidence"
                    )
                elif (
                    settings.CLINICAL_CHAT_UNCERTAINTY_GATE_FAILFAST_ON_RAG
                    and rag_success
                ):
                    llm_trace["llm_used"] = llm_trace.get("llm_used", "false")
                    llm_trace["llm_provider"] = llm_trace.get(
                        "llm_provider",
                        "uncertainty_gate",
                    )
                    llm_trace["llm_endpoint"] = llm_trace.get(
                        "llm_endpoint",
                        "skip_llm_use_evidence_first",
                    )
                    uncertainty_gate_triggered = True
                    uncertainty_gate_reason = (
                        "high_variance_failfast_on_rag"
                        if posterior_variance >= variance_threshold
                        else "ood_high_failfast_on_rag"
                    )
            elif uncertainty_level == "high" and not has_internal_evidence:
                llm_answer = cls._render_uncertainty_gate_answer(
                    query=safe_query,
                    top_domain=top_domain,
                    posterior_variance=posterior_variance,
                )
                llm_trace["llm_used"] = llm_trace.get("llm_used", "false")
                llm_trace["llm_provider"] = "uncertainty_gate"
                llm_trace["llm_endpoint"] = llm_trace.get(
                    "llm_endpoint",
                    "abstain_high_uncertainty",
                )
                uncertainty_gate_triggered = True
                uncertainty_gate_reason = "high_uncertainty_no_evidence"
        interpretability_trace.append(
            "uncertainty_gate_enabled="
            f"{1 if uncertainty_gate_enabled else 0}"
        )
        interpretability_trace.append(
            "uncertainty_gate_variance_threshold="
            f"{round(variance_threshold, 4) if response_mode == 'clinical' else 'na'}"
        )
        interpretability_trace.append(
            "uncertainty_gate_ood_score="
            f"{round(ood_score, 4) if response_mode == 'clinical' else 'na'}"
        )
        interpretability_trace.append(
            f"uncertainty_gate_ood_level={ood_level if response_mode == 'clinical' else 'na'}"
        )
        interpretability_trace.append(
            f"uncertainty_gate_triggered={1 if uncertainty_gate_triggered else 0}"
        )
        interpretability_trace.append(f"uncertainty_gate_reason={uncertainty_gate_reason}")

        if llm_answer is None and not uncertainty_gate_triggered:
            rag_force_extractive_only = (
                response_mode == "clinical"
                and settings.CLINICAL_CHAT_RAG_ENABLED
                and settings.CLINICAL_CHAT_RAG_FORCE_EXTRACTIVE_ONLY
            )
            rag_fact_only_mode = (
                response_mode == "clinical"
                and settings.CLINICAL_CHAT_RAG_ENABLED
                and settings.CLINICAL_CHAT_RAG_FACT_ONLY_MODE_ENABLED
            )
            rag_failed_generation_with_llm_failure = (
                response_mode == "clinical"
                and str(rag_trace.get("rag_status", "")) == "failed_generation"
                and bool(str(rag_trace.get("llm_error", "")).strip())
            )
            rag_hard_fail_retrieval = (
                response_mode == "clinical"
                and str(rag_trace.get("rag_status", "")) == "failed_retrieval"
                and not query_expanded
            )
            if rag_force_extractive_only:
                interpretability_trace.append("llm_second_pass_skipped=force_extractive_only")
            elif rag_fact_only_mode:
                interpretability_trace.append("llm_second_pass_skipped=fact_only_mode")
            elif rag_hard_fail_retrieval:
                interpretability_trace.append("llm_second_pass_skipped=rag_failed_retrieval")
            elif rag_failed_generation_with_llm_failure:
                interpretability_trace.append("llm_second_pass_skipped=rag_failed_generation")
            else:
                llm_answer, llm_trace = LLMChatProvider.generate_answer(
                    query=safe_query,
                    response_mode=response_mode,
                    effective_specialty=effective_specialty,
                    tool_mode=tool_mode,
                    matched_domains=matched_domains,
                    matched_endpoints=matched_endpoints,
                    memory_facts_used=memory_facts_used,
                    patient_summary=patient_summary,
                    patient_history_facts_used=patient_history_facts_used,
                    knowledge_sources=knowledge_sources,
                    web_sources=web_sources,
                    recent_dialogue=recent_dialogue,
                    endpoint_results=endpoint_recommendations,
                )

        should_attempt_llm_rewrite = (
            settings.CLINICAL_CHAT_LLM_REWRITE_ENABLED
            and
            not settings.CLINICAL_CHAT_LLM_NATIVE_STYLE_ENABLED
            and
            response_mode == "clinical"
            and bool(llm_answer)
            and llm_trace.get("llm_used") == "true"
            and llm_trace.get("llm_provider") == settings.CLINICAL_CHAT_LLM_PROVIDER
            and not llm_trace.get("llm_chat_error")
        )
        if should_attempt_llm_rewrite:
            initial_actionable = cls._is_actionable_llm_answer(
                answer=str(llm_answer or ""),
                response_mode=response_mode,
            )
            initial_grounded = cls._has_source_grounding_in_answer(
                answer=str(llm_answer or ""),
                knowledge_sources=knowledge_sources,
            )
            rag_validation_status = str(rag_trace.get("rag_validation_status", "valid"))
            initial_rag_valid = rag_validation_status == "valid"
            if not initial_actionable or not initial_grounded or not initial_rag_valid:
                rewritten_answer, rewrite_trace = (
                    LLMChatProvider.rewrite_clinical_answer_with_verification(
                        query=safe_query,
                        draft_answer=str(llm_answer or ""),
                        effective_specialty=effective_specialty,
                        matched_domains=matched_domains,
                        knowledge_sources=knowledge_sources,
                        endpoint_results=endpoint_recommendations,
                    )
                )
                llm_trace.update(rewrite_trace)
                interpretability_trace.append(
                    "llm_rewrite_attempted=1"
                    f";initial_actionable={1 if initial_actionable else 0}"
                    f";initial_grounded={1 if initial_grounded else 0}"
                    f";initial_rag_valid={1 if initial_rag_valid else 0}"
                )
                if rewritten_answer:
                    llm_answer = rewritten_answer
            else:
                llm_trace["llm_rewrite_status"] = "skipped_not_needed"

        if (
            response_mode == "clinical"
            and bool(llm_answer)
            and llm_trace.get("llm_origin") == "rag_orchestrator"
            and not pipeline_relaxed_mode
            and str(rag_trace.get("rag_validation_status", "valid")) != "valid"
        ):
            interpretability_trace.append("llm_quality_gate=rag_validation_warning_fallback")
            llm_answer = None

        should_apply_llm_quality_gate = (
            settings.CLINICAL_CHAT_LLM_QUALITY_GATES_ENABLED
            and not settings.CLINICAL_CHAT_LLM_NATIVE_STYLE_ENABLED
            and not pipeline_relaxed_mode
            and
            bool(llm_answer)
            and llm_trace.get("llm_used") == "true"
            and "llm_latency_ms" in llm_trace
        )
        if should_apply_llm_quality_gate and not cls._is_actionable_llm_answer(
            answer=str(llm_answer or ""),
            response_mode=response_mode,
        ):
            interpretability_trace.append("llm_quality_gate=short_or_generic_fallback")
            llm_answer = None
        elif (
            should_apply_llm_quality_gate
            and response_mode == "clinical"
            and not cls._has_source_grounding_in_answer(
                answer=str(llm_answer or ""),
                knowledge_sources=knowledge_sources,
            )
        ):
            interpretability_trace.append("llm_quality_gate=missing_source_grounding_fallback")
            llm_answer = None

        if (
            response_mode == "clinical"
            and bool(llm_answer)
            and not interrogatory_short_circuit
            and not pipeline_relaxed_mode
            and bool(contract_assessment.get("force_structured_fallback"))
        ):
            interpretability_trace.append("contract_guard=forced_structured_fallback")
            if (
                llm_trace.get("llm_used") == "true"
                and "clinical_answer_quality_gate=final_structured_fallback"
                not in interpretability_trace
            ):
                interpretability_trace.append(
                    "clinical_answer_quality_gate=final_structured_fallback"
                )
            llm_answer = None

        if (
            response_mode == "clinical"
            and bool(llm_answer)
            and not interrogatory_short_circuit
            and not pipeline_relaxed_mode
            and bool(logic_assessment.get("abstention_required"))
        ):
            interpretability_trace.append("logic_abstention_guard=forced_structured_fallback")
            if (
                llm_trace.get("llm_used") == "true"
                and "clinical_answer_quality_gate=final_structured_fallback"
                not in interpretability_trace
            ):
                interpretability_trace.append(
                    "clinical_answer_quality_gate=final_structured_fallback"
                )
            llm_answer = None

        rag_chunks_retrieved_raw = rag_trace.get("rag_chunks_retrieved", 0)
        try:
            rag_chunks_retrieved = int(rag_chunks_retrieved_raw)
        except (TypeError, ValueError):
            rag_chunks_retrieved = 0
        use_evidence_first_fallback = (
            response_mode == "clinical"
            and not interrogatory_short_circuit
            and len(knowledge_sources) > 0
            and (rag_chunks_retrieved > 0 or bool(rag_candidate_answer))
        )
        rag_extract_fallback_on_llm_failure = (
            response_mode == "clinical"
            and bool(rag_candidate_answer)
            and str(rag_trace.get("rag_generation_mode", "")).startswith("extractive_")
            and str(rag_trace.get("llm_used", "false")) == "false"
            and bool(str(rag_trace.get("llm_error") or "").strip())
            and use_evidence_first_fallback
        )
        if rag_extract_fallback_on_llm_failure:
            interpretability_trace.append(
                "rag_candidate_rejected=extractive_llm_failure_prefers_evidence_first"
            )
        rag_candidate_usable = (
            response_mode == "clinical"
            and bool(rag_candidate_answer)
            and not rag_extract_fallback_on_llm_failure
            and (
                pipeline_relaxed_mode
                or rag_validation_status in {"valid", "warning_insufficient_chunks"}
            )
        )

        if llm_answer:
            answer = llm_answer
        elif rag_candidate_usable:
            answer = str(rag_candidate_answer)
            interpretability_trace.append("clinical_fallback_mode=rag_candidate")
        elif response_mode == "clinical" and use_evidence_first_fallback:
            answer = cls._render_evidence_first_clinical_answer(
                care_task=care_task,
                query=safe_query,
                matched_domains=matched_domain_records,
                matched_endpoints=matched_endpoints,
                knowledge_sources=knowledge_sources,
            )
            interpretability_trace.append("clinical_fallback_mode=evidence_first")
        elif response_mode == "clinical":
            answer = cls._render_clinical_answer(
                care_task=care_task,
                query=safe_query,
                matched_domains=matched_domain_records,
                matched_endpoints=matched_endpoints,
                effective_specialty=effective_specialty,
                memory_facts_used=memory_facts_used,
                patient_summary=patient_summary,
                patient_history_facts_used=patient_history_facts_used,
                extracted_facts=extracted_facts,
                knowledge_sources=knowledge_sources,
                web_sources=web_sources,
                include_protocol_catalog=payload.include_protocol_catalog,
                tool_mode=tool_mode,
                recent_dialogue=recent_dialogue,
                endpoint_recommendations=endpoint_recommendations,
                decision_psychology=decision_psychology,
                logic_assessment=logic_assessment,
                contract_assessment=contract_assessment,
                math_assessment=math_assessment,
            )
            if (
                not pipeline_relaxed_mode
                and "clinical_answer_quality_gate=final_structured_fallback"
                not in interpretability_trace
            ):
                interpretability_trace.append(
                    "clinical_answer_quality_gate=final_structured_fallback"
                )
        else:
            answer = cls._render_general_answer(
                query=safe_query,
                memory_facts_used=memory_facts_used,
                knowledge_sources=knowledge_sources,
                web_sources=web_sources,
                tool_mode=tool_mode,
                recent_dialogue=recent_dialogue,
                matched_domains=matched_domain_records,
            )

        if not interrogatory_short_circuit:
            answer, guardrails_trace = NeMoGuardrailsService.apply_output_guardrails(
                query=safe_query,
                answer=answer,
                response_mode=response_mode,
                effective_specialty=effective_specialty,
                tool_mode=tool_mode,
                knowledge_sources=knowledge_sources,
                web_sources=web_sources,
            )
        should_apply_final_clinical_quality_gate = (
            response_mode == "clinical"
            and not pipeline_relaxed_mode
            and llm_trace.get("llm_used") == "true"
            and guardrails_trace.get("guardrails_status")
            in {"skipped_disabled", "skipped_empty_answer"}
        )
        if should_apply_final_clinical_quality_gate and not cls._is_actionable_llm_answer(
            answer=answer,
            response_mode=response_mode,
        ):
            interpretability_trace.append("clinical_answer_quality_gate=final_structured_fallback")
            if use_evidence_first_fallback:
                answer = cls._render_evidence_first_clinical_answer(
                    care_task=care_task,
                    query=safe_query,
                    matched_domains=matched_domain_records,
                    matched_endpoints=matched_endpoints,
                    knowledge_sources=knowledge_sources,
                )
                interpretability_trace.append("clinical_fallback_mode=evidence_first")
            else:
                answer = cls._render_clinical_answer(
                    care_task=care_task,
                    query=safe_query,
                    matched_domains=matched_domain_records,
                    matched_endpoints=matched_endpoints,
                    effective_specialty=effective_specialty,
                    memory_facts_used=memory_facts_used,
                    patient_summary=patient_summary,
                    patient_history_facts_used=patient_history_facts_used,
                    extracted_facts=extracted_facts,
                    knowledge_sources=knowledge_sources,
                    web_sources=web_sources,
                    include_protocol_catalog=payload.include_protocol_catalog,
                    tool_mode=tool_mode,
                    recent_dialogue=recent_dialogue,
                    endpoint_recommendations=endpoint_recommendations,
                    decision_psychology=decision_psychology,
                    logic_assessment=logic_assessment,
                    contract_assessment=contract_assessment,
                    math_assessment=math_assessment,
                )
        elif (
            should_apply_final_clinical_quality_gate
            and not cls._has_source_grounding_in_answer(
                answer=answer,
                knowledge_sources=knowledge_sources,
            )
        ):
            interpretability_trace.append(
                "clinical_answer_quality_gate=final_missing_source_grounding_fallback"
            )
            if use_evidence_first_fallback:
                answer = cls._render_evidence_first_clinical_answer(
                    care_task=care_task,
                    query=safe_query,
                    matched_domains=matched_domain_records,
                    matched_endpoints=matched_endpoints,
                    knowledge_sources=knowledge_sources,
                )
                interpretability_trace.append("clinical_fallback_mode=evidence_first")
            else:
                answer = cls._render_clinical_answer(
                    care_task=care_task,
                    query=safe_query,
                    matched_domains=matched_domain_records,
                    matched_endpoints=matched_endpoints,
                    effective_specialty=effective_specialty,
                    memory_facts_used=memory_facts_used,
                    patient_summary=patient_summary,
                    patient_history_facts_used=patient_history_facts_used,
                    extracted_facts=extracted_facts,
                    knowledge_sources=knowledge_sources,
                    web_sources=web_sources,
                    include_protocol_catalog=payload.include_protocol_catalog,
                    tool_mode=tool_mode,
                    recent_dialogue=recent_dialogue,
                    endpoint_recommendations=endpoint_recommendations,
                    decision_psychology=decision_psychology,
                    logic_assessment=logic_assessment,
                    contract_assessment=contract_assessment,
                    math_assessment=math_assessment,
                )

        quality_metrics = cls._build_quality_metrics(
            query=safe_query,
            answer=answer,
            matched_domains=matched_domains,
            knowledge_sources=knowledge_sources,
            web_sources=web_sources,
        )
        should_repair_degraded_with_evidence = (
            response_mode == "clinical"
            and quality_metrics.get("quality_status") in {"degraded", "attention"}
            and use_evidence_first_fallback
            and not pipeline_relaxed_mode
            and not rag_answer_authoritative
            and (
                not answer.startswith("Resumen operativo basado en evidencia interna")
                or answer.startswith(
                    "Resumen operativo basado en evidencia interna (RAG extractivo)."
                )
            )
        )
        if should_repair_degraded_with_evidence:
            answer = cls._render_evidence_first_clinical_answer(
                care_task=care_task,
                query=safe_query,
                matched_domains=matched_domain_records,
                matched_endpoints=matched_endpoints,
                knowledge_sources=knowledge_sources,
            )
            quality_metrics = cls._build_quality_metrics(
                query=safe_query,
                answer=answer,
                matched_domains=matched_domains,
                knowledge_sources=knowledge_sources,
                web_sources=web_sources,
            )
            interpretability_trace.append("quality_repair_applied=evidence_first_from_degraded")
        answer = cls._sanitize_final_answer_text(answer)
        quality_metrics = cls._build_quality_metrics(
            query=safe_query,
            answer=answer,
            matched_domains=matched_domains,
            knowledge_sources=knowledge_sources,
            web_sources=web_sources,
        )
        interpretability_trace.extend(
            [
                f"answer_relevance={quality_metrics['answer_relevance']}",
                f"context_relevance={quality_metrics['context_relevance']}",
                f"groundedness={quality_metrics['groundedness']}",
                f"quality_status={quality_metrics['quality_status']}",
            ]
        )
        if rag_trace:
            for key, value in rag_trace.items():
                if key == "rag_sources":
                    continue
                if isinstance(value, list):
                    rendered_value = ",".join(str(item) for item in value[:6]) if value else "none"
                else:
                    rendered_value = str(value)
                interpretability_trace.append(f"{key}={rendered_value}")
        if llm_trace:
            interpretability_trace.extend([f"{key}={value}" for key, value in llm_trace.items()])
        if guardrails_trace:
            interpretability_trace.extend(
                [f"{key}={value}" for key, value in guardrails_trace.items()]
            )
        run = AgentRunService.run_care_task_clinical_chat_workflow(
            db=db,
            care_task=care_task,
            chat_input={
                "query": payload.query,
                "session_id": session_id,
                "clinician_id": payload.clinician_id,
                "specialty_hint": payload.specialty_hint,
                "effective_specialty": effective_specialty,
                "conversation_mode": "intent_auto",
                "requested_tool_mode": requested_tool_mode,
                "tool_mode": tool_mode,
                "tool_policy_decision": "allowed" if policy_decision.allowed else "denied",
                "tool_policy_reason": policy_decision.reason_code,
                "response_mode": response_mode,
                "use_patient_history": payload.use_patient_history,
                "use_web_sources": use_web_sources,
                "max_web_sources": web_limit,
                "max_history_messages": payload.max_history_messages,
                "max_patient_history_messages": payload.max_patient_history_messages,
                "pipeline_relaxed_mode": payload.pipeline_relaxed_mode,
                "enable_active_interrogation": payload.enable_active_interrogation,
                "interrogation_max_turns": payload.interrogation_max_turns,
                "interrogation_confidence_threshold": payload.interrogation_confidence_threshold,
                "local_evidence_items": len(local_evidence_sources),
            },
            chat_output={
                "answer": answer,
                "response_mode": response_mode,
                "tool_mode": tool_mode,
                "matched_domains": matched_domains,
                "matched_endpoints": matched_endpoints,
                "knowledge_sources": knowledge_sources,
                "web_sources": web_sources,
                "endpoint_recommendations": endpoint_recommendations,
                "memory_facts_used": memory_facts_used,
                "patient_history_facts_used": patient_history_facts_used,
                "extracted_facts": extracted_facts,
                "patient_summary": patient_summary,
                "interpretability_trace": interpretability_trace,
                "quality_metrics": quality_metrics,
                "guardrails_trace": guardrails_trace,
                "interrogatory_result": interrogatory_result,
                "decision_psychology": decision_psychology,
                "logic_assessment": logic_assessment,
                "contract_assessment": contract_assessment,
                "math_assessment": math_assessment,
                "cluster_assessment": cluster_assessment,
                "hcluster_assessment": hcluster_assessment,
                "vector_assessment": vector_assessment,
                "svm_domain_assessment": svm_domain_assessment,
                "naive_bayes_assessment": naive_bayes_assessment,
                "risk_pipeline_assessment": risk_pipeline_assessment,
                "svm_assessment": svm_assessment,
                "security_findings": security_findings,
                "tool_policy_trace": policy_decision.trace,
                "tool_risk": {
                    "risk_level": risk_assessment.risk_level,
                    "categories": risk_assessment.categories,
                    "reasons": risk_assessment.reasons,
                },
            },
        )
        message = CareTaskChatMessage(
            care_task_id=care_task.id,
            session_id=session_id,
            clinician_id=payload.clinician_id,
            effective_specialty=effective_specialty,
            user_query=payload.query,
            assistant_answer=answer,
            matched_domains=matched_domains,
            matched_endpoints=matched_endpoints,
            knowledge_sources=knowledge_sources,
            web_sources=web_sources,
            memory_facts_used=memory_facts_used,
            patient_history_facts_used=patient_history_facts_used,
            extracted_facts=extracted_facts,
        )
        lock_key = f"care-task:{care_task.id}:session:{session_id}"
        lock_owner = f"chat-message:{uuid4().hex[:10]}"
        with SessionWriteLock.acquire(
            lock_key=lock_key,
            owner=lock_owner,
            timeout_seconds=2.5,
            stale_after_seconds=20.0,
        ):
            db.add(message)
            db.commit()
            db.refresh(message)
        return (
            message,
            run.id,
            run.workflow_name,
            interpretability_trace,
            response_mode,
            tool_mode,
            quality_metrics,
            "allowed" if policy_decision.allowed else "denied",
            security_findings,
        )
