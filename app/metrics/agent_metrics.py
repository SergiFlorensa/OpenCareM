from prometheus_client import Gauge
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import SessionLocal
from app.models.agent_run import AgentRun
from app.services.agent_run_service import AgentRunService
from app.services.care_task_service import CareTaskService

AGENT_RUNS_TOTAL = Gauge(
    "agent_runs_total",
    "Numero total de ejecuciones de agente persistidas.",
)
AGENT_RUNS_COMPLETED_TOTAL = Gauge(
    "agent_runs_completed_total",
    "Numero total de ejecuciones de agente completadas.",
)
AGENT_RUNS_FAILED_TOTAL = Gauge(
    "agent_runs_failed_total",
    "Numero total de ejecuciones de agente fallidas.",
)
AGENT_STEPS_FALLBACK_TOTAL = Gauge(
    "agent_steps_fallback_total",
    "Numero total de pasos de agente donde se uso fallback.",
)
AGENT_FALLBACK_RATE_PERCENT = Gauge(
    "agent_fallback_rate_percent",
    "Tasa de fallback como porcentaje del total de ejecuciones.",
)
RESPIRATORY_PROTOCOL_RUNS_TOTAL = Gauge(
    "respiratory_protocol_runs_total",
    "Numero total de ejecuciones del workflow respiratorio.",
)
RESPIRATORY_PROTOCOL_RUNS_COMPLETED_TOTAL = Gauge(
    "respiratory_protocol_runs_completed_total",
    "Numero de ejecuciones completadas del workflow respiratorio.",
)
PEDIATRIC_HUMANIZATION_RUNS_TOTAL = Gauge(
    "pediatric_humanization_runs_total",
    "Numero total de ejecuciones del workflow de humanizacion pediatrica.",
)
PEDIATRIC_HUMANIZATION_RUNS_COMPLETED_TOTAL = Gauge(
    "pediatric_humanization_runs_completed_total",
    "Numero de ejecuciones completadas del workflow de humanizacion pediatrica.",
)
ADVANCED_SCREENING_RUNS_TOTAL = Gauge(
    "advanced_screening_runs_total",
    "Numero total de ejecuciones del workflow de screening avanzado.",
)
ADVANCED_SCREENING_RUNS_COMPLETED_TOTAL = Gauge(
    "advanced_screening_runs_completed_total",
    "Numero de ejecuciones completadas del workflow de screening avanzado.",
)
ADVANCED_SCREENING_ALERTS_GENERATED_TOTAL = Gauge(
    "advanced_screening_alerts_generated_total",
    "Total acumulado de alertas generadas por el workflow de screening avanzado.",
)
ADVANCED_SCREENING_ALERTS_SUPPRESSED_TOTAL = Gauge(
    "advanced_screening_alerts_suppressed_total",
    "Total acumulado de alertas suprimidas por control de fatiga.",
)
ACNE_ROSACEA_DIFFERENTIAL_RUNS_TOTAL = Gauge(
    "acne_rosacea_differential_runs_total",
    "Numero total de ejecuciones del workflow diferencial acne/rosacea.",
)
ACNE_ROSACEA_DIFFERENTIAL_RUNS_COMPLETED_TOTAL = Gauge(
    "acne_rosacea_differential_runs_completed_total",
    "Numero de ejecuciones completadas del workflow diferencial acne/rosacea.",
)
ACNE_ROSACEA_DIFFERENTIAL_RED_FLAGS_TOTAL = Gauge(
    "acne_rosacea_differential_red_flags_total",
    "Total acumulado de red flags detectadas por workflow diferencial acne/rosacea.",
)
CRITICAL_OPS_SUPPORT_RUNS_TOTAL = Gauge(
    "critical_ops_support_runs_total",
    "Numero total de ejecuciones del workflow operativo critico transversal.",
)
CRITICAL_OPS_SUPPORT_RUNS_COMPLETED_TOTAL = Gauge(
    "critical_ops_support_runs_completed_total",
    "Numero de ejecuciones completadas del workflow operativo critico transversal.",
)
CRITICAL_OPS_SUPPORT_CRITICAL_ALERTS_TOTAL = Gauge(
    "critical_ops_support_critical_alerts_total",
    "Total acumulado de alertas criticas detectadas por workflow operativo critico transversal.",
)
NEUROLOGY_SUPPORT_RUNS_TOTAL = Gauge(
    "neurology_support_runs_total",
    "Numero total de ejecuciones del workflow operativo neurologico.",
)
NEUROLOGY_SUPPORT_RUNS_COMPLETED_TOTAL = Gauge(
    "neurology_support_runs_completed_total",
    "Numero de ejecuciones completadas del workflow operativo neurologico.",
)
NEUROLOGY_SUPPORT_CRITICAL_ALERTS_TOTAL = Gauge(
    "neurology_support_critical_alerts_total",
    "Total acumulado de alertas criticas detectadas por workflow operativo neurologico.",
)
GASTRO_HEPATO_SUPPORT_RUNS_TOTAL = Gauge(
    "gastro_hepato_support_runs_total",
    "Numero total de ejecuciones del workflow operativo gastro-hepato.",
)
GASTRO_HEPATO_SUPPORT_RUNS_COMPLETED_TOTAL = Gauge(
    "gastro_hepato_support_runs_completed_total",
    "Numero de ejecuciones completadas del workflow operativo gastro-hepato.",
)
GASTRO_HEPATO_SUPPORT_CRITICAL_ALERTS_TOTAL = Gauge(
    "gastro_hepato_support_critical_alerts_total",
    "Total acumulado de alertas criticas detectadas por workflow operativo gastro-hepato.",
)
RHEUM_IMMUNO_SUPPORT_RUNS_TOTAL = Gauge(
    "rheum_immuno_support_runs_total",
    "Numero total de ejecuciones del workflow operativo reuma-inmuno.",
)
RHEUM_IMMUNO_SUPPORT_RUNS_COMPLETED_TOTAL = Gauge(
    "rheum_immuno_support_runs_completed_total",
    "Numero de ejecuciones completadas del workflow operativo reuma-inmuno.",
)
RHEUM_IMMUNO_SUPPORT_CRITICAL_ALERTS_TOTAL = Gauge(
    "rheum_immuno_support_critical_alerts_total",
    "Total acumulado de alertas criticas detectadas por workflow operativo reuma-inmuno.",
)
PSYCHIATRY_SUPPORT_RUNS_TOTAL = Gauge(
    "psychiatry_support_runs_total",
    "Numero total de ejecuciones del workflow operativo de psiquiatria.",
)
PSYCHIATRY_SUPPORT_RUNS_COMPLETED_TOTAL = Gauge(
    "psychiatry_support_runs_completed_total",
    "Numero de ejecuciones completadas del workflow operativo de psiquiatria.",
)
PSYCHIATRY_SUPPORT_CRITICAL_ALERTS_TOTAL = Gauge(
    "psychiatry_support_critical_alerts_total",
    "Total acumulado de alertas criticas detectadas por workflow operativo de psiquiatria.",
)
HEMATOLOGY_SUPPORT_RUNS_TOTAL = Gauge(
    "hematology_support_runs_total",
    "Numero total de ejecuciones del workflow operativo de hematologia.",
)
HEMATOLOGY_SUPPORT_RUNS_COMPLETED_TOTAL = Gauge(
    "hematology_support_runs_completed_total",
    "Numero de ejecuciones completadas del workflow operativo de hematologia.",
)
HEMATOLOGY_SUPPORT_CRITICAL_ALERTS_TOTAL = Gauge(
    "hematology_support_critical_alerts_total",
    "Total acumulado de alertas criticas detectadas por workflow operativo de hematologia.",
)
ENDOCRINOLOGY_SUPPORT_RUNS_TOTAL = Gauge(
    "endocrinology_support_runs_total",
    "Numero total de ejecuciones del workflow operativo de endocrinologia.",
)
ENDOCRINOLOGY_SUPPORT_RUNS_COMPLETED_TOTAL = Gauge(
    "endocrinology_support_runs_completed_total",
    "Numero de ejecuciones completadas del workflow operativo de endocrinologia.",
)
ENDOCRINOLOGY_SUPPORT_CRITICAL_ALERTS_TOTAL = Gauge(
    "endocrinology_support_critical_alerts_total",
    "Total acumulado de alertas criticas detectadas por workflow operativo de endocrinologia.",
)
NEPHROLOGY_SUPPORT_RUNS_TOTAL = Gauge(
    "nephrology_support_runs_total",
    "Numero total de ejecuciones del workflow operativo de nefrologia.",
)
NEPHROLOGY_SUPPORT_RUNS_COMPLETED_TOTAL = Gauge(
    "nephrology_support_runs_completed_total",
    "Numero de ejecuciones completadas del workflow operativo de nefrologia.",
)
NEPHROLOGY_SUPPORT_CRITICAL_ALERTS_TOTAL = Gauge(
    "nephrology_support_critical_alerts_total",
    "Total acumulado de alertas criticas detectadas por workflow operativo de nefrologia.",
)
PNEUMOLOGY_SUPPORT_RUNS_TOTAL = Gauge(
    "pneumology_support_runs_total",
    "Numero total de ejecuciones del workflow operativo de neumologia.",
)
PNEUMOLOGY_SUPPORT_RUNS_COMPLETED_TOTAL = Gauge(
    "pneumology_support_runs_completed_total",
    "Numero de ejecuciones completadas del workflow operativo de neumologia.",
)
PNEUMOLOGY_SUPPORT_CRITICAL_ALERTS_TOTAL = Gauge(
    "pneumology_support_critical_alerts_total",
    "Total acumulado de alertas criticas detectadas por workflow operativo de neumologia.",
)
GERIATRICS_SUPPORT_RUNS_TOTAL = Gauge(
    "geriatrics_support_runs_total",
    "Numero total de ejecuciones del workflow operativo de geriatria.",
)
GERIATRICS_SUPPORT_RUNS_COMPLETED_TOTAL = Gauge(
    "geriatrics_support_runs_completed_total",
    "Numero de ejecuciones completadas del workflow operativo de geriatria.",
)
GERIATRICS_SUPPORT_CRITICAL_ALERTS_TOTAL = Gauge(
    "geriatrics_support_critical_alerts_total",
    "Total acumulado de alertas criticas detectadas por workflow operativo de geriatria.",
)
ONCOLOGY_SUPPORT_RUNS_TOTAL = Gauge(
    "oncology_support_runs_total",
    "Numero total de ejecuciones del workflow operativo de oncologia.",
)
ONCOLOGY_SUPPORT_RUNS_COMPLETED_TOTAL = Gauge(
    "oncology_support_runs_completed_total",
    "Numero de ejecuciones completadas del workflow operativo de oncologia.",
)
ONCOLOGY_SUPPORT_CRITICAL_ALERTS_TOTAL = Gauge(
    "oncology_support_critical_alerts_total",
    "Total acumulado de alertas criticas detectadas por workflow operativo de oncologia.",
)
ANESTHESIOLOGY_SUPPORT_RUNS_TOTAL = Gauge(
    "anesthesiology_support_runs_total",
    "Numero total de ejecuciones del workflow operativo de anestesiologia/reanimacion.",
)
ANESTHESIOLOGY_SUPPORT_RUNS_COMPLETED_TOTAL = Gauge(
    "anesthesiology_support_runs_completed_total",
    "Numero de ejecuciones completadas del workflow operativo de anestesiologia/reanimacion.",
)
ANESTHESIOLOGY_SUPPORT_CRITICAL_ALERTS_TOTAL = Gauge(
    "anesthesiology_support_critical_alerts_total",
    "Total acumulado de alertas criticas detectadas por workflow operativo de "
    "anestesiologia/reanimacion.",
)
PALLIATIVE_SUPPORT_RUNS_TOTAL = Gauge(
    "palliative_support_runs_total",
    "Numero total de ejecuciones del workflow operativo de cuidados paliativos.",
)
PALLIATIVE_SUPPORT_RUNS_COMPLETED_TOTAL = Gauge(
    "palliative_support_runs_completed_total",
    "Numero de ejecuciones completadas del workflow operativo de cuidados paliativos.",
)
PALLIATIVE_SUPPORT_CRITICAL_ALERTS_TOTAL = Gauge(
    "palliative_support_critical_alerts_total",
    "Total acumulado de alertas criticas detectadas por workflow operativo de "
    "cuidados paliativos.",
)
OPHTHALMOLOGY_SUPPORT_RUNS_TOTAL = Gauge(
    "ophthalmology_support_runs_total",
    "Numero total de ejecuciones del workflow operativo de oftalmologia.",
)
OPHTHALMOLOGY_SUPPORT_RUNS_COMPLETED_TOTAL = Gauge(
    "ophthalmology_support_runs_completed_total",
    "Numero de ejecuciones completadas del workflow operativo de oftalmologia.",
)
OPHTHALMOLOGY_SUPPORT_CRITICAL_ALERTS_TOTAL = Gauge(
    "ophthalmology_support_critical_alerts_total",
    "Total acumulado de alertas criticas detectadas por workflow operativo de oftalmologia.",
)
IMMUNOLOGY_SUPPORT_RUNS_TOTAL = Gauge(
    "immunology_support_runs_total",
    "Numero total de ejecuciones del workflow operativo de inmunologia.",
)
IMMUNOLOGY_SUPPORT_RUNS_COMPLETED_TOTAL = Gauge(
    "immunology_support_runs_completed_total",
    "Numero de ejecuciones completadas del workflow operativo de inmunologia.",
)
IMMUNOLOGY_SUPPORT_CRITICAL_ALERTS_TOTAL = Gauge(
    "immunology_support_critical_alerts_total",
    "Total acumulado de alertas criticas detectadas por workflow operativo de inmunologia.",
)
GENETIC_RECURRENCE_SUPPORT_RUNS_TOTAL = Gauge(
    "genetic_recurrence_support_runs_total",
    "Numero total de ejecuciones del workflow operativo de recurrencia genetica.",
)
GENETIC_RECURRENCE_SUPPORT_RUNS_COMPLETED_TOTAL = Gauge(
    "genetic_recurrence_support_runs_completed_total",
    "Numero de ejecuciones completadas del workflow operativo de recurrencia genetica.",
)
GENETIC_RECURRENCE_SUPPORT_CRITICAL_ALERTS_TOTAL = Gauge(
    "genetic_recurrence_support_critical_alerts_total",
    "Total acumulado de alertas criticas detectadas por workflow operativo de "
    "recurrencia genetica.",
)
GYNECOLOGY_OBSTETRICS_SUPPORT_RUNS_TOTAL = Gauge(
    "gynecology_obstetrics_support_runs_total",
    "Numero total de ejecuciones del workflow operativo de ginecologia/obstetricia.",
)
GYNECOLOGY_OBSTETRICS_SUPPORT_RUNS_COMPLETED_TOTAL = Gauge(
    "gynecology_obstetrics_support_runs_completed_total",
    "Numero de ejecuciones completadas del workflow operativo de ginecologia/obstetricia.",
)
GYNECOLOGY_OBSTETRICS_SUPPORT_CRITICAL_ALERTS_TOTAL = Gauge(
    "gynecology_obstetrics_support_critical_alerts_total",
    "Total acumulado de alertas criticas detectadas por workflow operativo de "
    "ginecologia/obstetricia.",
)
PEDIATRICS_NEONATOLOGY_SUPPORT_RUNS_TOTAL = Gauge(
    "pediatrics_neonatology_support_runs_total",
    "Numero total de ejecuciones del workflow operativo de pediatria/neonatologia.",
)
PEDIATRICS_NEONATOLOGY_SUPPORT_RUNS_COMPLETED_TOTAL = Gauge(
    "pediatrics_neonatology_support_runs_completed_total",
    "Numero de ejecuciones completadas del workflow operativo de pediatria/neonatologia.",
)
PEDIATRICS_NEONATOLOGY_SUPPORT_CRITICAL_ALERTS_TOTAL = Gauge(
    "pediatrics_neonatology_support_critical_alerts_total",
    "Total acumulado de alertas criticas detectadas por workflow operativo de "
    "pediatria/neonatologia.",
)
UROLOGY_SUPPORT_RUNS_TOTAL = Gauge(
    "urology_support_runs_total",
    "Numero total de ejecuciones del workflow operativo de urologia.",
)
UROLOGY_SUPPORT_RUNS_COMPLETED_TOTAL = Gauge(
    "urology_support_runs_completed_total",
    "Numero de ejecuciones completadas del workflow operativo de urologia.",
)
UROLOGY_SUPPORT_CRITICAL_ALERTS_TOTAL = Gauge(
    "urology_support_critical_alerts_total",
    "Total acumulado de alertas criticas detectadas por workflow operativo de urologia.",
)
EPIDEMIOLOGY_SUPPORT_RUNS_TOTAL = Gauge(
    "epidemiology_support_runs_total",
    "Numero total de ejecuciones del workflow operativo de epidemiologia clinica.",
)
EPIDEMIOLOGY_SUPPORT_RUNS_COMPLETED_TOTAL = Gauge(
    "epidemiology_support_runs_completed_total",
    "Numero de ejecuciones completadas del workflow operativo de epidemiologia clinica.",
)
EPIDEMIOLOGY_SUPPORT_CRITICAL_ALERTS_TOTAL = Gauge(
    "epidemiology_support_critical_alerts_total",
    "Total acumulado de alertas criticas detectadas por workflow operativo de epidemiologia "
    "clinica.",
)
ANISAKIS_SUPPORT_RUNS_TOTAL = Gauge(
    "anisakis_support_runs_total",
    "Numero total de ejecuciones del workflow operativo de anisakis.",
)
ANISAKIS_SUPPORT_RUNS_COMPLETED_TOTAL = Gauge(
    "anisakis_support_runs_completed_total",
    "Numero de ejecuciones completadas del workflow operativo de anisakis.",
)
ANISAKIS_SUPPORT_CRITICAL_ALERTS_TOTAL = Gauge(
    "anisakis_support_critical_alerts_total",
    "Total acumulado de alertas criticas detectadas por workflow operativo de anisakis.",
)
TRAUMA_SUPPORT_RUNS_TOTAL = Gauge(
    "trauma_support_runs_total",
    "Numero total de ejecuciones del workflow operativo de trauma.",
)
TRAUMA_SUPPORT_RUNS_COMPLETED_TOTAL = Gauge(
    "trauma_support_runs_completed_total",
    "Numero de ejecuciones completadas del workflow operativo de trauma.",
)
TRAUMA_SUPPORT_CRITICAL_ALERTS_TOTAL = Gauge(
    "trauma_support_critical_alerts_total",
    "Total acumulado de alertas generadas por workflow operativo de trauma.",
)
CHEST_XRAY_SUPPORT_RUNS_TOTAL = Gauge(
    "chest_xray_support_runs_total",
    "Numero total de ejecuciones del workflow de soporte radiografico.",
)
CHEST_XRAY_SUPPORT_RUNS_COMPLETED_TOTAL = Gauge(
    "chest_xray_support_runs_completed_total",
    "Numero de ejecuciones completadas del workflow de soporte radiografico.",
)
CHEST_XRAY_SUPPORT_CRITICAL_ALERTS_TOTAL = Gauge(
    "chest_xray_support_critical_alerts_total",
    "Total acumulado de alertas criticas (red flags) detectadas por workflow de RX torax.",
)
PITYRIASIS_DIFFERENTIAL_RUNS_TOTAL = Gauge(
    "pityriasis_differential_runs_total",
    "Numero total de ejecuciones del workflow diferencial de pitiriasis.",
)
PITYRIASIS_DIFFERENTIAL_RUNS_COMPLETED_TOTAL = Gauge(
    "pityriasis_differential_runs_completed_total",
    "Numero de ejecuciones completadas del workflow diferencial de pitiriasis.",
)
PITYRIASIS_DIFFERENTIAL_RED_FLAGS_TOTAL = Gauge(
    "pityriasis_differential_red_flags_total",
    "Total acumulado de red flags detectadas por workflow diferencial de pitiriasis.",
)
MEDICOLEGAL_OPS_RUNS_TOTAL = Gauge(
    "medicolegal_ops_runs_total",
    "Numero total de ejecuciones del workflow de soporte medico-legal.",
)
MEDICOLEGAL_OPS_RUNS_COMPLETED_TOTAL = Gauge(
    "medicolegal_ops_runs_completed_total",
    "Numero de ejecuciones completadas del workflow de soporte medico-legal.",
)
MEDICOLEGAL_OPS_CRITICAL_ALERTS_TOTAL = Gauge(
    "medicolegal_ops_critical_alerts_total",
    "Total acumulado de alertas criticas detectadas por workflow medico-legal.",
)
SEPSIS_PROTOCOL_RUNS_TOTAL = Gauge(
    "sepsis_protocol_runs_total",
    "Numero total de ejecuciones del workflow operativo de sepsis.",
)
SEPSIS_PROTOCOL_RUNS_COMPLETED_TOTAL = Gauge(
    "sepsis_protocol_runs_completed_total",
    "Numero de ejecuciones completadas del workflow operativo de sepsis.",
)
SEPSIS_PROTOCOL_CRITICAL_ALERTS_TOTAL = Gauge(
    "sepsis_protocol_critical_alerts_total",
    "Total acumulado de alertas generadas por workflow de sepsis.",
)
SCASEST_PROTOCOL_RUNS_TOTAL = Gauge(
    "scasest_protocol_runs_total",
    "Numero total de ejecuciones del workflow operativo de SCASEST.",
)
SCASEST_PROTOCOL_RUNS_COMPLETED_TOTAL = Gauge(
    "scasest_protocol_runs_completed_total",
    "Numero de ejecuciones completadas del workflow operativo de SCASEST.",
)
SCASEST_PROTOCOL_CRITICAL_ALERTS_TOTAL = Gauge(
    "scasest_protocol_critical_alerts_total",
    "Total acumulado de alertas generadas por workflow de SCASEST.",
)
CARDIO_RISK_SUPPORT_RUNS_TOTAL = Gauge(
    "cardio_risk_support_runs_total",
    "Numero total de ejecuciones del workflow operativo de riesgo cardiovascular.",
)
CARDIO_RISK_SUPPORT_RUNS_COMPLETED_TOTAL = Gauge(
    "cardio_risk_support_runs_completed_total",
    "Numero de ejecuciones completadas del workflow operativo de riesgo cardiovascular.",
)
CARDIO_RISK_SUPPORT_ALERTS_TOTAL = Gauge(
    "cardio_risk_support_alerts_total",
    "Total acumulado de alertas generadas por workflow de riesgo cardiovascular.",
)
RESUSCITATION_PROTOCOL_RUNS_TOTAL = Gauge(
    "resuscitation_protocol_runs_total",
    "Numero total de ejecuciones del workflow operativo de reanimacion.",
)
RESUSCITATION_PROTOCOL_RUNS_COMPLETED_TOTAL = Gauge(
    "resuscitation_protocol_runs_completed_total",
    "Numero de ejecuciones completadas del workflow operativo de reanimacion.",
)
RESUSCITATION_PROTOCOL_ALERTS_TOTAL = Gauge(
    "resuscitation_protocol_alerts_total",
    "Total acumulado de alertas generadas por workflow de reanimacion.",
)
TRIAGE_AUDIT_TOTAL = Gauge(
    "triage_audit_total",
    "Numero total de auditorias de triaje IA vs validacion humana.",
)
TRIAGE_AUDIT_MATCH_TOTAL = Gauge(
    "triage_audit_match_total",
    "Numero de auditorias donde IA y humano coincidieron.",
)
TRIAGE_AUDIT_UNDER_TOTAL = Gauge(
    "triage_audit_under_total",
    "Numero de auditorias con under-triage (IA menos urgente).",
)
TRIAGE_AUDIT_OVER_TOTAL = Gauge(
    "triage_audit_over_total",
    "Numero de auditorias con over-triage (IA mas urgente).",
)
TRIAGE_AUDIT_UNDER_RATE_PERCENT = Gauge(
    "triage_audit_under_rate_percent",
    "Porcentaje de under-triage sobre total auditado.",
)
TRIAGE_AUDIT_OVER_RATE_PERCENT = Gauge(
    "triage_audit_over_rate_percent",
    "Porcentaje de over-triage sobre total auditado.",
)
SCREENING_AUDIT_TOTAL = Gauge(
    "screening_audit_total",
    "Numero total de auditorias de screening avanzado.",
)
SCREENING_AUDIT_MATCH_TOTAL = Gauge(
    "screening_audit_match_total",
    "Numero de auditorias de screening donde IA y humano coinciden en riesgo global.",
)
SCREENING_AUDIT_UNDER_TOTAL = Gauge(
    "screening_audit_under_total",
    "Numero de auditorias con under-screening (IA menos severa).",
)
SCREENING_AUDIT_OVER_TOTAL = Gauge(
    "screening_audit_over_total",
    "Numero de auditorias con over-screening (IA mas severa).",
)
SCREENING_AUDIT_UNDER_RATE_PERCENT = Gauge(
    "screening_audit_under_rate_percent",
    "Porcentaje de under-screening sobre total auditado.",
)
SCREENING_AUDIT_OVER_RATE_PERCENT = Gauge(
    "screening_audit_over_rate_percent",
    "Porcentaje de over-screening sobre total auditado.",
)
SCREENING_RULE_HIV_MATCH_RATE_PERCENT = Gauge(
    "screening_rule_hiv_match_rate_percent",
    "Porcentaje de coincidencia IA vs humano para regla de cribado VIH.",
)
SCREENING_RULE_SEPSIS_MATCH_RATE_PERCENT = Gauge(
    "screening_rule_sepsis_match_rate_percent",
    "Porcentaje de coincidencia IA vs humano para regla de ruta de sepsis.",
)
SCREENING_RULE_PERSISTENT_COVID_MATCH_RATE_PERCENT = Gauge(
    "screening_rule_persistent_covid_match_rate_percent",
    "Porcentaje de coincidencia IA vs humano para regla de COVID persistente.",
)
SCREENING_RULE_LONG_ACTING_MATCH_RATE_PERCENT = Gauge(
    "screening_rule_long_acting_match_rate_percent",
    "Porcentaje de coincidencia IA vs humano para regla de candidato long-acting.",
)
MEDICOLEGAL_AUDIT_TOTAL = Gauge(
    "medicolegal_audit_total",
    "Numero total de auditorias de soporte medico-legal.",
)
MEDICOLEGAL_AUDIT_MATCH_TOTAL = Gauge(
    "medicolegal_audit_match_total",
    "Numero de auditorias medico-legales donde IA y humano coinciden en riesgo global.",
)
MEDICOLEGAL_AUDIT_UNDER_TOTAL = Gauge(
    "medicolegal_audit_under_total",
    "Numero de auditorias con under-legal-risk (IA menos severa).",
)
MEDICOLEGAL_AUDIT_OVER_TOTAL = Gauge(
    "medicolegal_audit_over_total",
    "Numero de auditorias con over-legal-risk (IA mas severa).",
)
MEDICOLEGAL_AUDIT_UNDER_RATE_PERCENT = Gauge(
    "medicolegal_audit_under_rate_percent",
    "Porcentaje de under-legal-risk sobre total auditado.",
)
MEDICOLEGAL_AUDIT_OVER_RATE_PERCENT = Gauge(
    "medicolegal_audit_over_rate_percent",
    "Porcentaje de over-legal-risk sobre total auditado.",
)
MEDICOLEGAL_RULE_CONSENT_MATCH_RATE_PERCENT = Gauge(
    "medicolegal_rule_consent_match_rate_percent",
    "Porcentaje de coincidencia IA vs humano para regla de consentimiento.",
)
MEDICOLEGAL_RULE_JUDICIAL_NOTIFICATION_MATCH_RATE_PERCENT = Gauge(
    "medicolegal_rule_judicial_notification_match_rate_percent",
    "Porcentaje de coincidencia IA vs humano para regla de notificacion judicial.",
)
MEDICOLEGAL_RULE_CHAIN_OF_CUSTODY_MATCH_RATE_PERCENT = Gauge(
    "medicolegal_rule_chain_of_custody_match_rate_percent",
    "Porcentaje de coincidencia IA vs humano para regla de cadena de custodia.",
)
SCASEST_AUDIT_TOTAL = Gauge(
    "scasest_audit_total",
    "Numero total de auditorias de soporte SCASEST.",
)
SCASEST_AUDIT_MATCH_TOTAL = Gauge(
    "scasest_audit_match_total",
    "Numero de auditorias SCASEST donde IA y humano coinciden en riesgo global.",
)
SCASEST_AUDIT_UNDER_TOTAL = Gauge(
    "scasest_audit_under_total",
    "Numero de auditorias con under-scasest-risk (IA menos severa).",
)
SCASEST_AUDIT_OVER_TOTAL = Gauge(
    "scasest_audit_over_total",
    "Numero de auditorias con over-scasest-risk (IA mas severa).",
)
SCASEST_AUDIT_UNDER_RATE_PERCENT = Gauge(
    "scasest_audit_under_rate_percent",
    "Porcentaje de under-scasest-risk sobre total auditado.",
)
SCASEST_AUDIT_OVER_RATE_PERCENT = Gauge(
    "scasest_audit_over_rate_percent",
    "Porcentaje de over-scasest-risk sobre total auditado.",
)
SCASEST_RULE_ESCALATION_MATCH_RATE_PERCENT = Gauge(
    "scasest_rule_escalation_match_rate_percent",
    "Porcentaje de coincidencia IA vs humano para regla de escalado SCASEST.",
)
SCASEST_RULE_IMMEDIATE_ANTIISCHEMIC_MATCH_RATE_PERCENT = Gauge(
    "scasest_rule_immediate_antiischemic_match_rate_percent",
    "Porcentaje de coincidencia IA vs humano para estrategia antiisquemica inicial.",
)
CARDIO_RISK_AUDIT_TOTAL = Gauge(
    "cardio_risk_audit_total",
    "Numero total de auditorias de soporte cardiovascular.",
)
CARDIO_RISK_AUDIT_MATCH_TOTAL = Gauge(
    "cardio_risk_audit_match_total",
    "Numero de auditorias cardiovasculares donde IA y humano coinciden en riesgo global.",
)
CARDIO_RISK_AUDIT_UNDER_TOTAL = Gauge(
    "cardio_risk_audit_under_total",
    "Numero de auditorias con under-cardio-risk (IA menos severa).",
)
CARDIO_RISK_AUDIT_OVER_TOTAL = Gauge(
    "cardio_risk_audit_over_total",
    "Numero de auditorias con over-cardio-risk (IA mas severa).",
)
CARDIO_RISK_AUDIT_UNDER_RATE_PERCENT = Gauge(
    "cardio_risk_audit_under_rate_percent",
    "Porcentaje de under-cardio-risk sobre total auditado.",
)
CARDIO_RISK_AUDIT_OVER_RATE_PERCENT = Gauge(
    "cardio_risk_audit_over_rate_percent",
    "Porcentaje de over-cardio-risk sobre total auditado.",
)
CARDIO_RISK_RULE_NON_HDL_TARGET_MATCH_RATE_PERCENT = Gauge(
    "cardio_risk_rule_non_hdl_target_match_rate_percent",
    "Porcentaje de coincidencia IA vs humano para regla de objetivo no-HDL.",
)
CARDIO_RISK_RULE_PHARMACOLOGIC_STRATEGY_MATCH_RATE_PERCENT = Gauge(
    "cardio_risk_rule_pharmacologic_strategy_match_rate_percent",
    "Porcentaje de coincidencia IA vs humano para recomendacion farmacologica.",
)
CARDIO_RISK_RULE_INTENSIVE_LIFESTYLE_MATCH_RATE_PERCENT = Gauge(
    "cardio_risk_rule_intensive_lifestyle_match_rate_percent",
    "Porcentaje de coincidencia IA vs humano para intensidad de intervencion en estilo de vida.",
)
RESUSCITATION_AUDIT_TOTAL = Gauge(
    "resuscitation_audit_total",
    "Numero total de auditorias de soporte de reanimacion.",
)
RESUSCITATION_AUDIT_MATCH_TOTAL = Gauge(
    "resuscitation_audit_match_total",
    "Numero de auditorias de reanimacion donde IA y humano coinciden en severidad global.",
)
RESUSCITATION_AUDIT_UNDER_TOTAL = Gauge(
    "resuscitation_audit_under_total",
    "Numero de auditorias con under-resuscitation-risk (IA menos severa).",
)
RESUSCITATION_AUDIT_OVER_TOTAL = Gauge(
    "resuscitation_audit_over_total",
    "Numero de auditorias con over-resuscitation-risk (IA mas severa).",
)
RESUSCITATION_AUDIT_UNDER_RATE_PERCENT = Gauge(
    "resuscitation_audit_under_rate_percent",
    "Porcentaje de under-resuscitation-risk sobre total auditado.",
)
RESUSCITATION_AUDIT_OVER_RATE_PERCENT = Gauge(
    "resuscitation_audit_over_rate_percent",
    "Porcentaje de over-resuscitation-risk sobre total auditado.",
)
RESUSCITATION_RULE_SHOCK_MATCH_RATE_PERCENT = Gauge(
    "resuscitation_rule_shock_match_rate_percent",
    "Porcentaje de coincidencia IA vs humano para recomendacion de choque/cardioversion.",
)
RESUSCITATION_RULE_REVERSIBLE_CAUSES_MATCH_RATE_PERCENT = Gauge(
    "resuscitation_rule_reversible_causes_match_rate_percent",
    "Porcentaje de coincidencia IA vs humano para accion sobre causas reversibles.",
)
RESUSCITATION_RULE_AIRWAY_PLAN_MATCH_RATE_PERCENT = Gauge(
    "resuscitation_rule_airway_plan_match_rate_percent",
    "Porcentaje de coincidencia IA vs humano para adecuacion del plan de via aerea.",
)
CARE_TASK_QUALITY_AUDIT_TOTAL = Gauge(
    "care_task_quality_audit_total",
    "Numero total de auditorias consideradas en el scorecard global de calidad IA clinica.",
)
CARE_TASK_QUALITY_AUDIT_MATCH_TOTAL = Gauge(
    "care_task_quality_audit_match_total",
    "Numero total de coincidencias IA vs humano en el scorecard global.",
)
CARE_TASK_QUALITY_AUDIT_UNDER_TOTAL = Gauge(
    "care_task_quality_audit_under_total",
    "Numero total de eventos under-risk agregados en el scorecard global.",
)
CARE_TASK_QUALITY_AUDIT_OVER_TOTAL = Gauge(
    "care_task_quality_audit_over_total",
    "Numero total de eventos over-risk agregados en el scorecard global.",
)
CARE_TASK_QUALITY_AUDIT_UNDER_RATE_PERCENT = Gauge(
    "care_task_quality_audit_under_rate_percent",
    "Porcentaje global de under-risk sobre auditorias agregadas.",
)
CARE_TASK_QUALITY_AUDIT_OVER_RATE_PERCENT = Gauge(
    "care_task_quality_audit_over_rate_percent",
    "Porcentaje global de over-risk sobre auditorias agregadas.",
)
CARE_TASK_QUALITY_AUDIT_MATCH_RATE_PERCENT = Gauge(
    "care_task_quality_audit_match_rate_percent",
    "Porcentaje global de coincidencia IA vs humano sobre auditorias agregadas.",
)

_REGISTERED = False


def _read_ops_summary_value(key: str) -> float:
    db = SessionLocal()
    try:
        summary = AgentRunService.get_ops_summary(db=db)
        value = summary.get(key, 0)
        return float(value)
    finally:
        db.close()


def _read_workflow_summary_value(workflow_name: str, key: str) -> float:
    db = SessionLocal()
    try:
        summary = AgentRunService.get_ops_summary(db=db, workflow_name=workflow_name)
        value = summary.get(key, 0)
        return float(value)
    finally:
        db.close()


def _read_triage_audit_summary_value(key: str) -> float:
    db = SessionLocal()
    try:
        summary = CareTaskService.get_triage_audit_summary(db=db)
        value = summary.get(key, 0)
        return float(value)
    except SQLAlchemyError:
        # Si la tabla aun no existe en un entorno local, no romper /metrics.
        return 0.0
    finally:
        db.close()


def _read_screening_audit_summary_value(key: str) -> float:
    db = SessionLocal()
    try:
        summary = CareTaskService.get_screening_audit_summary(db=db)
        value = summary.get(key, 0)
        return float(value)
    except SQLAlchemyError:
        return 0.0
    finally:
        db.close()


def _read_medicolegal_audit_summary_value(key: str) -> float:
    db = SessionLocal()
    try:
        summary = CareTaskService.get_medicolegal_audit_summary(db=db)
        value = summary.get(key, 0)
        return float(value)
    except SQLAlchemyError:
        return 0.0
    finally:
        db.close()


def _read_scasest_audit_summary_value(key: str) -> float:
    db = SessionLocal()
    try:
        summary = CareTaskService.get_scasest_audit_summary(db=db)
        value = summary.get(key, 0)
        return float(value)
    except SQLAlchemyError:
        return 0.0
    finally:
        db.close()


def _read_cardio_risk_audit_summary_value(key: str) -> float:
    db = SessionLocal()
    try:
        summary = CareTaskService.get_cardio_risk_audit_summary(db=db)
        value = summary.get(key, 0)
        return float(value)
    except SQLAlchemyError:
        return 0.0
    finally:
        db.close()


def _read_resuscitation_audit_summary_value(key: str) -> float:
    db = SessionLocal()
    try:
        summary = CareTaskService.get_resuscitation_audit_summary(db=db)
        value = summary.get(key, 0)
        return float(value)
    except SQLAlchemyError:
        return 0.0
    finally:
        db.close()


def _read_quality_scorecard_value(key: str) -> float:
    db = SessionLocal()
    try:
        summary = CareTaskService.get_quality_scorecard(db=db)
        value = summary.get(key, 0)
        return float(value)
    except SQLAlchemyError:
        return 0.0
    finally:
        db.close()


def _read_workflow_output_sum(workflow_name: str, output_key: str) -> float:
    db = SessionLocal()
    try:
        rows = (
            db.query(AgentRun)
            .filter(AgentRun.workflow_name == workflow_name, AgentRun.status == "completed")
            .all()
        )
        total = 0.0
        for row in rows:
            if not isinstance(row.run_output, dict):
                continue
            output = row.run_output.get("advanced_screening")
            if isinstance(output, dict):
                value = output.get(output_key, 0)
                if isinstance(value, (int, float)):
                    total += float(value)
        return total
    finally:
        db.close()


def _read_workflow_list_length_sum(
    workflow_name: str,
    output_root_key: str,
    output_key: str,
) -> float:
    db = SessionLocal()
    try:
        rows = (
            db.query(AgentRun)
            .filter(AgentRun.workflow_name == workflow_name, AgentRun.status == "completed")
            .all()
        )
        total = 0.0
        for row in rows:
            if not isinstance(row.run_output, dict):
                continue
            output = row.run_output.get(output_root_key)
            if isinstance(output, dict):
                value = output.get(output_key, [])
                if isinstance(value, list):
                    total += float(len(value))
        return total
    finally:
        db.close()


def register_agent_metrics() -> None:
    """Conecta callbacks dinamicos para que Prometheus refleje el estado real de BD."""
    global _REGISTERED
    if _REGISTERED:
        return

    AGENT_RUNS_TOTAL.set_function(lambda: _read_ops_summary_value("total_runs"))
    AGENT_RUNS_COMPLETED_TOTAL.set_function(lambda: _read_ops_summary_value("completed_runs"))
    AGENT_RUNS_FAILED_TOTAL.set_function(lambda: _read_ops_summary_value("failed_runs"))
    AGENT_STEPS_FALLBACK_TOTAL.set_function(lambda: _read_ops_summary_value("fallback_steps"))
    AGENT_FALLBACK_RATE_PERCENT.set_function(
        lambda: _read_ops_summary_value("fallback_rate_percent")
    )
    RESPIRATORY_PROTOCOL_RUNS_TOTAL.set_function(
        lambda: _read_workflow_summary_value("respiratory_protocol_v1", "total_runs")
    )
    RESPIRATORY_PROTOCOL_RUNS_COMPLETED_TOTAL.set_function(
        lambda: _read_workflow_summary_value("respiratory_protocol_v1", "completed_runs")
    )
    PEDIATRIC_HUMANIZATION_RUNS_TOTAL.set_function(
        lambda: _read_workflow_summary_value("pediatric_neuro_onco_support_v1", "total_runs")
    )
    PEDIATRIC_HUMANIZATION_RUNS_COMPLETED_TOTAL.set_function(
        lambda: _read_workflow_summary_value("pediatric_neuro_onco_support_v1", "completed_runs")
    )
    ADVANCED_SCREENING_RUNS_TOTAL.set_function(
        lambda: _read_workflow_summary_value("advanced_screening_support_v1", "total_runs")
    )
    ADVANCED_SCREENING_RUNS_COMPLETED_TOTAL.set_function(
        lambda: _read_workflow_summary_value("advanced_screening_support_v1", "completed_runs")
    )
    ADVANCED_SCREENING_ALERTS_GENERATED_TOTAL.set_function(
        lambda: _read_workflow_output_sum("advanced_screening_support_v1", "alerts_generated_total")
    )
    ADVANCED_SCREENING_ALERTS_SUPPRESSED_TOTAL.set_function(
        lambda: _read_workflow_output_sum(
            "advanced_screening_support_v1", "alerts_suppressed_total"
        )
    )
    ACNE_ROSACEA_DIFFERENTIAL_RUNS_TOTAL.set_function(
        lambda: _read_workflow_summary_value("acne_rosacea_differential_support_v1", "total_runs")
    )
    ACNE_ROSACEA_DIFFERENTIAL_RUNS_COMPLETED_TOTAL.set_function(
        lambda: _read_workflow_summary_value(
            "acne_rosacea_differential_support_v1",
            "completed_runs",
        )
    )
    ACNE_ROSACEA_DIFFERENTIAL_RED_FLAGS_TOTAL.set_function(
        lambda: _read_workflow_list_length_sum(
            "acne_rosacea_differential_support_v1",
            "acne_rosacea_differential",
            "urgent_red_flags",
        )
    )
    CRITICAL_OPS_SUPPORT_RUNS_TOTAL.set_function(
        lambda: _read_workflow_summary_value("critical_ops_support_v1", "total_runs")
    )
    CRITICAL_OPS_SUPPORT_RUNS_COMPLETED_TOTAL.set_function(
        lambda: _read_workflow_summary_value("critical_ops_support_v1", "completed_runs")
    )
    CRITICAL_OPS_SUPPORT_CRITICAL_ALERTS_TOTAL.set_function(
        lambda: _read_workflow_list_length_sum(
            "critical_ops_support_v1",
            "critical_ops",
            "critical_alerts",
        )
    )
    NEUROLOGY_SUPPORT_RUNS_TOTAL.set_function(
        lambda: _read_workflow_summary_value("neurology_support_v1", "total_runs")
    )
    NEUROLOGY_SUPPORT_RUNS_COMPLETED_TOTAL.set_function(
        lambda: _read_workflow_summary_value("neurology_support_v1", "completed_runs")
    )
    NEUROLOGY_SUPPORT_CRITICAL_ALERTS_TOTAL.set_function(
        lambda: _read_workflow_list_length_sum(
            "neurology_support_v1",
            "neurology_support",
            "vascular_life_threat_alerts",
        )
    )
    GASTRO_HEPATO_SUPPORT_RUNS_TOTAL.set_function(
        lambda: _read_workflow_summary_value("gastro_hepato_support_v1", "total_runs")
    )
    GASTRO_HEPATO_SUPPORT_RUNS_COMPLETED_TOTAL.set_function(
        lambda: _read_workflow_summary_value("gastro_hepato_support_v1", "completed_runs")
    )
    GASTRO_HEPATO_SUPPORT_CRITICAL_ALERTS_TOTAL.set_function(
        lambda: _read_workflow_list_length_sum(
            "gastro_hepato_support_v1",
            "gastro_hepato_support",
            "critical_alerts",
        )
    )
    RHEUM_IMMUNO_SUPPORT_RUNS_TOTAL.set_function(
        lambda: _read_workflow_summary_value("rheum_immuno_support_v1", "total_runs")
    )
    RHEUM_IMMUNO_SUPPORT_RUNS_COMPLETED_TOTAL.set_function(
        lambda: _read_workflow_summary_value("rheum_immuno_support_v1", "completed_runs")
    )
    RHEUM_IMMUNO_SUPPORT_CRITICAL_ALERTS_TOTAL.set_function(
        lambda: _read_workflow_list_length_sum(
            "rheum_immuno_support_v1",
            "rheum_immuno_support",
            "critical_alerts",
        )
    )
    PSYCHIATRY_SUPPORT_RUNS_TOTAL.set_function(
        lambda: _read_workflow_summary_value("psychiatry_support_v1", "total_runs")
    )
    PSYCHIATRY_SUPPORT_RUNS_COMPLETED_TOTAL.set_function(
        lambda: _read_workflow_summary_value("psychiatry_support_v1", "completed_runs")
    )
    PSYCHIATRY_SUPPORT_CRITICAL_ALERTS_TOTAL.set_function(
        lambda: _read_workflow_list_length_sum(
            "psychiatry_support_v1",
            "psychiatry_support",
            "critical_alerts",
        )
    )
    HEMATOLOGY_SUPPORT_RUNS_TOTAL.set_function(
        lambda: _read_workflow_summary_value("hematology_support_v1", "total_runs")
    )
    HEMATOLOGY_SUPPORT_RUNS_COMPLETED_TOTAL.set_function(
        lambda: _read_workflow_summary_value("hematology_support_v1", "completed_runs")
    )
    HEMATOLOGY_SUPPORT_CRITICAL_ALERTS_TOTAL.set_function(
        lambda: _read_workflow_list_length_sum(
            "hematology_support_v1",
            "hematology_support",
            "critical_alerts",
        )
    )
    ENDOCRINOLOGY_SUPPORT_RUNS_TOTAL.set_function(
        lambda: _read_workflow_summary_value("endocrinology_support_v1", "total_runs")
    )
    ENDOCRINOLOGY_SUPPORT_RUNS_COMPLETED_TOTAL.set_function(
        lambda: _read_workflow_summary_value("endocrinology_support_v1", "completed_runs")
    )
    ENDOCRINOLOGY_SUPPORT_CRITICAL_ALERTS_TOTAL.set_function(
        lambda: _read_workflow_list_length_sum(
            "endocrinology_support_v1",
            "endocrinology_support",
            "critical_alerts",
        )
    )
    NEPHROLOGY_SUPPORT_RUNS_TOTAL.set_function(
        lambda: _read_workflow_summary_value("nephrology_support_v1", "total_runs")
    )
    NEPHROLOGY_SUPPORT_RUNS_COMPLETED_TOTAL.set_function(
        lambda: _read_workflow_summary_value("nephrology_support_v1", "completed_runs")
    )
    NEPHROLOGY_SUPPORT_CRITICAL_ALERTS_TOTAL.set_function(
        lambda: _read_workflow_list_length_sum(
            "nephrology_support_v1",
            "nephrology_support",
            "critical_alerts",
        )
    )
    PNEUMOLOGY_SUPPORT_RUNS_TOTAL.set_function(
        lambda: _read_workflow_summary_value("pneumology_support_v1", "total_runs")
    )
    PNEUMOLOGY_SUPPORT_RUNS_COMPLETED_TOTAL.set_function(
        lambda: _read_workflow_summary_value("pneumology_support_v1", "completed_runs")
    )
    PNEUMOLOGY_SUPPORT_CRITICAL_ALERTS_TOTAL.set_function(
        lambda: _read_workflow_list_length_sum(
            "pneumology_support_v1",
            "pneumology_support",
            "critical_alerts",
        )
    )
    GERIATRICS_SUPPORT_RUNS_TOTAL.set_function(
        lambda: _read_workflow_summary_value("geriatrics_support_v1", "total_runs")
    )
    GERIATRICS_SUPPORT_RUNS_COMPLETED_TOTAL.set_function(
        lambda: _read_workflow_summary_value("geriatrics_support_v1", "completed_runs")
    )
    GERIATRICS_SUPPORT_CRITICAL_ALERTS_TOTAL.set_function(
        lambda: _read_workflow_list_length_sum(
            "geriatrics_support_v1",
            "geriatrics_support",
            "critical_alerts",
        )
    )
    ONCOLOGY_SUPPORT_RUNS_TOTAL.set_function(
        lambda: _read_workflow_summary_value("oncology_support_v1", "total_runs")
    )
    ONCOLOGY_SUPPORT_RUNS_COMPLETED_TOTAL.set_function(
        lambda: _read_workflow_summary_value("oncology_support_v1", "completed_runs")
    )
    ONCOLOGY_SUPPORT_CRITICAL_ALERTS_TOTAL.set_function(
        lambda: _read_workflow_list_length_sum(
            "oncology_support_v1",
            "oncology_support",
            "critical_alerts",
        )
    )
    ANESTHESIOLOGY_SUPPORT_RUNS_TOTAL.set_function(
        lambda: _read_workflow_summary_value("anesthesiology_support_v1", "total_runs")
    )
    ANESTHESIOLOGY_SUPPORT_RUNS_COMPLETED_TOTAL.set_function(
        lambda: _read_workflow_summary_value("anesthesiology_support_v1", "completed_runs")
    )
    ANESTHESIOLOGY_SUPPORT_CRITICAL_ALERTS_TOTAL.set_function(
        lambda: _read_workflow_list_length_sum(
            "anesthesiology_support_v1",
            "anesthesiology_support",
            "critical_alerts",
        )
    )
    PALLIATIVE_SUPPORT_RUNS_TOTAL.set_function(
        lambda: _read_workflow_summary_value("palliative_support_v1", "total_runs")
    )
    PALLIATIVE_SUPPORT_RUNS_COMPLETED_TOTAL.set_function(
        lambda: _read_workflow_summary_value("palliative_support_v1", "completed_runs")
    )
    PALLIATIVE_SUPPORT_CRITICAL_ALERTS_TOTAL.set_function(
        lambda: _read_workflow_list_length_sum(
            "palliative_support_v1",
            "palliative_support",
            "critical_alerts",
        )
    )
    OPHTHALMOLOGY_SUPPORT_RUNS_TOTAL.set_function(
        lambda: _read_workflow_summary_value("ophthalmology_support_v1", "total_runs")
    )
    OPHTHALMOLOGY_SUPPORT_RUNS_COMPLETED_TOTAL.set_function(
        lambda: _read_workflow_summary_value("ophthalmology_support_v1", "completed_runs")
    )
    OPHTHALMOLOGY_SUPPORT_CRITICAL_ALERTS_TOTAL.set_function(
        lambda: _read_workflow_list_length_sum(
            "ophthalmology_support_v1",
            "ophthalmology_support",
            "critical_alerts",
        )
    )
    IMMUNOLOGY_SUPPORT_RUNS_TOTAL.set_function(
        lambda: _read_workflow_summary_value("immunology_support_v1", "total_runs")
    )
    IMMUNOLOGY_SUPPORT_RUNS_COMPLETED_TOTAL.set_function(
        lambda: _read_workflow_summary_value("immunology_support_v1", "completed_runs")
    )
    IMMUNOLOGY_SUPPORT_CRITICAL_ALERTS_TOTAL.set_function(
        lambda: _read_workflow_list_length_sum(
            "immunology_support_v1",
            "immunology_support",
            "critical_alerts",
        )
    )
    GENETIC_RECURRENCE_SUPPORT_RUNS_TOTAL.set_function(
        lambda: _read_workflow_summary_value(
            "genetic_recurrence_support_v1",
            "total_runs",
        )
    )
    GENETIC_RECURRENCE_SUPPORT_RUNS_COMPLETED_TOTAL.set_function(
        lambda: _read_workflow_summary_value(
            "genetic_recurrence_support_v1",
            "completed_runs",
        )
    )
    GENETIC_RECURRENCE_SUPPORT_CRITICAL_ALERTS_TOTAL.set_function(
        lambda: _read_workflow_list_length_sum(
            "genetic_recurrence_support_v1",
            "genetic_recurrence_support",
            "critical_alerts",
        )
    )
    GYNECOLOGY_OBSTETRICS_SUPPORT_RUNS_TOTAL.set_function(
        lambda: _read_workflow_summary_value(
            "gynecology_obstetrics_support_v1",
            "total_runs",
        )
    )
    GYNECOLOGY_OBSTETRICS_SUPPORT_RUNS_COMPLETED_TOTAL.set_function(
        lambda: _read_workflow_summary_value(
            "gynecology_obstetrics_support_v1",
            "completed_runs",
        )
    )
    GYNECOLOGY_OBSTETRICS_SUPPORT_CRITICAL_ALERTS_TOTAL.set_function(
        lambda: _read_workflow_list_length_sum(
            "gynecology_obstetrics_support_v1",
            "gynecology_obstetrics_support",
            "critical_alerts",
        )
    )
    PEDIATRICS_NEONATOLOGY_SUPPORT_RUNS_TOTAL.set_function(
        lambda: _read_workflow_summary_value(
            "pediatrics_neonatology_support_v1",
            "total_runs",
        )
    )
    PEDIATRICS_NEONATOLOGY_SUPPORT_RUNS_COMPLETED_TOTAL.set_function(
        lambda: _read_workflow_summary_value(
            "pediatrics_neonatology_support_v1",
            "completed_runs",
        )
    )
    PEDIATRICS_NEONATOLOGY_SUPPORT_CRITICAL_ALERTS_TOTAL.set_function(
        lambda: _read_workflow_list_length_sum(
            "pediatrics_neonatology_support_v1",
            "pediatrics_neonatology_support",
            "critical_alerts",
        )
    )
    UROLOGY_SUPPORT_RUNS_TOTAL.set_function(
        lambda: _read_workflow_summary_value("urology_support_v1", "total_runs")
    )
    UROLOGY_SUPPORT_RUNS_COMPLETED_TOTAL.set_function(
        lambda: _read_workflow_summary_value("urology_support_v1", "completed_runs")
    )
    UROLOGY_SUPPORT_CRITICAL_ALERTS_TOTAL.set_function(
        lambda: _read_workflow_list_length_sum(
            "urology_support_v1",
            "urology_support",
            "critical_alerts",
        )
    )
    EPIDEMIOLOGY_SUPPORT_RUNS_TOTAL.set_function(
        lambda: _read_workflow_summary_value("epidemiology_support_v1", "total_runs")
    )
    EPIDEMIOLOGY_SUPPORT_RUNS_COMPLETED_TOTAL.set_function(
        lambda: _read_workflow_summary_value("epidemiology_support_v1", "completed_runs")
    )
    EPIDEMIOLOGY_SUPPORT_CRITICAL_ALERTS_TOTAL.set_function(
        lambda: _read_workflow_list_length_sum(
            "epidemiology_support_v1",
            "epidemiology_support",
            "critical_alerts",
        )
    )
    ANISAKIS_SUPPORT_RUNS_TOTAL.set_function(
        lambda: _read_workflow_summary_value("anisakis_support_v1", "total_runs")
    )
    ANISAKIS_SUPPORT_RUNS_COMPLETED_TOTAL.set_function(
        lambda: _read_workflow_summary_value("anisakis_support_v1", "completed_runs")
    )
    ANISAKIS_SUPPORT_CRITICAL_ALERTS_TOTAL.set_function(
        lambda: _read_workflow_list_length_sum(
            "anisakis_support_v1",
            "anisakis_support",
            "critical_alerts",
        )
    )
    TRAUMA_SUPPORT_RUNS_TOTAL.set_function(
        lambda: _read_workflow_summary_value("trauma_support_v1", "total_runs")
    )
    TRAUMA_SUPPORT_RUNS_COMPLETED_TOTAL.set_function(
        lambda: _read_workflow_summary_value("trauma_support_v1", "completed_runs")
    )
    TRAUMA_SUPPORT_CRITICAL_ALERTS_TOTAL.set_function(
        lambda: _read_workflow_list_length_sum(
            "trauma_support_v1",
            "trauma_support",
            "alerts",
        )
    )
    CHEST_XRAY_SUPPORT_RUNS_TOTAL.set_function(
        lambda: _read_workflow_summary_value("chest_xray_support_v1", "total_runs")
    )
    CHEST_XRAY_SUPPORT_RUNS_COMPLETED_TOTAL.set_function(
        lambda: _read_workflow_summary_value("chest_xray_support_v1", "completed_runs")
    )
    CHEST_XRAY_SUPPORT_CRITICAL_ALERTS_TOTAL.set_function(
        lambda: _read_workflow_list_length_sum(
            "chest_xray_support_v1",
            "chest_xray_support",
            "urgent_red_flags",
        )
    )
    PITYRIASIS_DIFFERENTIAL_RUNS_TOTAL.set_function(
        lambda: _read_workflow_summary_value("pityriasis_differential_support_v1", "total_runs")
    )
    PITYRIASIS_DIFFERENTIAL_RUNS_COMPLETED_TOTAL.set_function(
        lambda: _read_workflow_summary_value(
            "pityriasis_differential_support_v1",
            "completed_runs",
        )
    )
    PITYRIASIS_DIFFERENTIAL_RED_FLAGS_TOTAL.set_function(
        lambda: _read_workflow_list_length_sum(
            "pityriasis_differential_support_v1",
            "pityriasis_differential",
            "urgent_red_flags",
        )
    )
    MEDICOLEGAL_OPS_RUNS_TOTAL.set_function(
        lambda: _read_workflow_summary_value("medicolegal_ops_support_v1", "total_runs")
    )
    MEDICOLEGAL_OPS_RUNS_COMPLETED_TOTAL.set_function(
        lambda: _read_workflow_summary_value("medicolegal_ops_support_v1", "completed_runs")
    )
    MEDICOLEGAL_OPS_CRITICAL_ALERTS_TOTAL.set_function(
        lambda: _read_workflow_list_length_sum(
            "medicolegal_ops_support_v1",
            "medicolegal_ops",
            "critical_legal_alerts",
        )
    )
    SEPSIS_PROTOCOL_RUNS_TOTAL.set_function(
        lambda: _read_workflow_summary_value("sepsis_protocol_support_v1", "total_runs")
    )
    SEPSIS_PROTOCOL_RUNS_COMPLETED_TOTAL.set_function(
        lambda: _read_workflow_summary_value("sepsis_protocol_support_v1", "completed_runs")
    )
    SEPSIS_PROTOCOL_CRITICAL_ALERTS_TOTAL.set_function(
        lambda: _read_workflow_list_length_sum(
            "sepsis_protocol_support_v1",
            "sepsis_protocol",
            "alerts",
        )
    )
    SCASEST_PROTOCOL_RUNS_TOTAL.set_function(
        lambda: _read_workflow_summary_value("scasest_protocol_support_v1", "total_runs")
    )
    SCASEST_PROTOCOL_RUNS_COMPLETED_TOTAL.set_function(
        lambda: _read_workflow_summary_value("scasest_protocol_support_v1", "completed_runs")
    )
    SCASEST_PROTOCOL_CRITICAL_ALERTS_TOTAL.set_function(
        lambda: _read_workflow_list_length_sum(
            "scasest_protocol_support_v1",
            "scasest_protocol",
            "alerts",
        )
    )
    CARDIO_RISK_SUPPORT_RUNS_TOTAL.set_function(
        lambda: _read_workflow_summary_value("cardio_risk_support_v1", "total_runs")
    )
    CARDIO_RISK_SUPPORT_RUNS_COMPLETED_TOTAL.set_function(
        lambda: _read_workflow_summary_value("cardio_risk_support_v1", "completed_runs")
    )
    CARDIO_RISK_SUPPORT_ALERTS_TOTAL.set_function(
        lambda: _read_workflow_list_length_sum(
            "cardio_risk_support_v1",
            "cardio_risk_support",
            "alerts",
        )
    )
    RESUSCITATION_PROTOCOL_RUNS_TOTAL.set_function(
        lambda: _read_workflow_summary_value("resuscitation_protocol_support_v1", "total_runs")
    )
    RESUSCITATION_PROTOCOL_RUNS_COMPLETED_TOTAL.set_function(
        lambda: _read_workflow_summary_value("resuscitation_protocol_support_v1", "completed_runs")
    )
    RESUSCITATION_PROTOCOL_ALERTS_TOTAL.set_function(
        lambda: _read_workflow_list_length_sum(
            "resuscitation_protocol_support_v1",
            "resuscitation_protocol",
            "alerts",
        )
    )
    TRIAGE_AUDIT_TOTAL.set_function(lambda: _read_triage_audit_summary_value("total_audits"))
    TRIAGE_AUDIT_MATCH_TOTAL.set_function(lambda: _read_triage_audit_summary_value("matches"))
    TRIAGE_AUDIT_UNDER_TOTAL.set_function(lambda: _read_triage_audit_summary_value("under_triage"))
    TRIAGE_AUDIT_OVER_TOTAL.set_function(lambda: _read_triage_audit_summary_value("over_triage"))
    TRIAGE_AUDIT_UNDER_RATE_PERCENT.set_function(
        lambda: _read_triage_audit_summary_value("under_triage_rate_percent")
    )
    TRIAGE_AUDIT_OVER_RATE_PERCENT.set_function(
        lambda: _read_triage_audit_summary_value("over_triage_rate_percent")
    )
    SCREENING_AUDIT_TOTAL.set_function(lambda: _read_screening_audit_summary_value("total_audits"))
    SCREENING_AUDIT_MATCH_TOTAL.set_function(lambda: _read_screening_audit_summary_value("matches"))
    SCREENING_AUDIT_UNDER_TOTAL.set_function(
        lambda: _read_screening_audit_summary_value("under_screening")
    )
    SCREENING_AUDIT_OVER_TOTAL.set_function(
        lambda: _read_screening_audit_summary_value("over_screening")
    )
    SCREENING_AUDIT_UNDER_RATE_PERCENT.set_function(
        lambda: _read_screening_audit_summary_value("under_screening_rate_percent")
    )
    SCREENING_AUDIT_OVER_RATE_PERCENT.set_function(
        lambda: _read_screening_audit_summary_value("over_screening_rate_percent")
    )
    SCREENING_RULE_HIV_MATCH_RATE_PERCENT.set_function(
        lambda: _read_screening_audit_summary_value("hiv_screening_match_rate_percent")
    )
    SCREENING_RULE_SEPSIS_MATCH_RATE_PERCENT.set_function(
        lambda: _read_screening_audit_summary_value("sepsis_route_match_rate_percent")
    )
    SCREENING_RULE_PERSISTENT_COVID_MATCH_RATE_PERCENT.set_function(
        lambda: _read_screening_audit_summary_value("persistent_covid_match_rate_percent")
    )
    SCREENING_RULE_LONG_ACTING_MATCH_RATE_PERCENT.set_function(
        lambda: _read_screening_audit_summary_value("long_acting_match_rate_percent")
    )
    MEDICOLEGAL_AUDIT_TOTAL.set_function(
        lambda: _read_medicolegal_audit_summary_value("total_audits")
    )
    MEDICOLEGAL_AUDIT_MATCH_TOTAL.set_function(
        lambda: _read_medicolegal_audit_summary_value("matches")
    )
    MEDICOLEGAL_AUDIT_UNDER_TOTAL.set_function(
        lambda: _read_medicolegal_audit_summary_value("under_legal_risk")
    )
    MEDICOLEGAL_AUDIT_OVER_TOTAL.set_function(
        lambda: _read_medicolegal_audit_summary_value("over_legal_risk")
    )
    MEDICOLEGAL_AUDIT_UNDER_RATE_PERCENT.set_function(
        lambda: _read_medicolegal_audit_summary_value("under_legal_risk_rate_percent")
    )
    MEDICOLEGAL_AUDIT_OVER_RATE_PERCENT.set_function(
        lambda: _read_medicolegal_audit_summary_value("over_legal_risk_rate_percent")
    )
    MEDICOLEGAL_RULE_CONSENT_MATCH_RATE_PERCENT.set_function(
        lambda: _read_medicolegal_audit_summary_value("consent_required_match_rate_percent")
    )
    MEDICOLEGAL_RULE_JUDICIAL_NOTIFICATION_MATCH_RATE_PERCENT.set_function(
        lambda: _read_medicolegal_audit_summary_value("judicial_notification_match_rate_percent")
    )
    MEDICOLEGAL_RULE_CHAIN_OF_CUSTODY_MATCH_RATE_PERCENT.set_function(
        lambda: _read_medicolegal_audit_summary_value("chain_of_custody_match_rate_percent")
    )
    SCASEST_AUDIT_TOTAL.set_function(lambda: _read_scasest_audit_summary_value("total_audits"))
    SCASEST_AUDIT_MATCH_TOTAL.set_function(lambda: _read_scasest_audit_summary_value("matches"))
    SCASEST_AUDIT_UNDER_TOTAL.set_function(
        lambda: _read_scasest_audit_summary_value("under_scasest_risk")
    )
    SCASEST_AUDIT_OVER_TOTAL.set_function(
        lambda: _read_scasest_audit_summary_value("over_scasest_risk")
    )
    SCASEST_AUDIT_UNDER_RATE_PERCENT.set_function(
        lambda: _read_scasest_audit_summary_value("under_scasest_risk_rate_percent")
    )
    SCASEST_AUDIT_OVER_RATE_PERCENT.set_function(
        lambda: _read_scasest_audit_summary_value("over_scasest_risk_rate_percent")
    )
    SCASEST_RULE_ESCALATION_MATCH_RATE_PERCENT.set_function(
        lambda: _read_scasest_audit_summary_value("escalation_required_match_rate_percent")
    )
    SCASEST_RULE_IMMEDIATE_ANTIISCHEMIC_MATCH_RATE_PERCENT.set_function(
        lambda: _read_scasest_audit_summary_value(
            "immediate_antiischemic_strategy_match_rate_percent"
        )
    )
    CARDIO_RISK_AUDIT_TOTAL.set_function(
        lambda: _read_cardio_risk_audit_summary_value("total_audits")
    )
    CARDIO_RISK_AUDIT_MATCH_TOTAL.set_function(
        lambda: _read_cardio_risk_audit_summary_value("matches")
    )
    CARDIO_RISK_AUDIT_UNDER_TOTAL.set_function(
        lambda: _read_cardio_risk_audit_summary_value("under_cardio_risk")
    )
    CARDIO_RISK_AUDIT_OVER_TOTAL.set_function(
        lambda: _read_cardio_risk_audit_summary_value("over_cardio_risk")
    )
    CARDIO_RISK_AUDIT_UNDER_RATE_PERCENT.set_function(
        lambda: _read_cardio_risk_audit_summary_value("under_cardio_risk_rate_percent")
    )
    CARDIO_RISK_AUDIT_OVER_RATE_PERCENT.set_function(
        lambda: _read_cardio_risk_audit_summary_value("over_cardio_risk_rate_percent")
    )
    CARDIO_RISK_RULE_NON_HDL_TARGET_MATCH_RATE_PERCENT.set_function(
        lambda: _read_cardio_risk_audit_summary_value("non_hdl_target_required_match_rate_percent")
    )
    CARDIO_RISK_RULE_PHARMACOLOGIC_STRATEGY_MATCH_RATE_PERCENT.set_function(
        lambda: _read_cardio_risk_audit_summary_value("pharmacologic_strategy_match_rate_percent")
    )
    CARDIO_RISK_RULE_INTENSIVE_LIFESTYLE_MATCH_RATE_PERCENT.set_function(
        lambda: _read_cardio_risk_audit_summary_value("intensive_lifestyle_match_rate_percent")
    )
    RESUSCITATION_AUDIT_TOTAL.set_function(
        lambda: _read_resuscitation_audit_summary_value("total_audits")
    )
    RESUSCITATION_AUDIT_MATCH_TOTAL.set_function(
        lambda: _read_resuscitation_audit_summary_value("matches")
    )
    RESUSCITATION_AUDIT_UNDER_TOTAL.set_function(
        lambda: _read_resuscitation_audit_summary_value("under_resuscitation_risk")
    )
    RESUSCITATION_AUDIT_OVER_TOTAL.set_function(
        lambda: _read_resuscitation_audit_summary_value("over_resuscitation_risk")
    )
    RESUSCITATION_AUDIT_UNDER_RATE_PERCENT.set_function(
        lambda: _read_resuscitation_audit_summary_value("under_resuscitation_risk_rate_percent")
    )
    RESUSCITATION_AUDIT_OVER_RATE_PERCENT.set_function(
        lambda: _read_resuscitation_audit_summary_value("over_resuscitation_risk_rate_percent")
    )
    RESUSCITATION_RULE_SHOCK_MATCH_RATE_PERCENT.set_function(
        lambda: _read_resuscitation_audit_summary_value("shock_recommended_match_rate_percent")
    )
    RESUSCITATION_RULE_REVERSIBLE_CAUSES_MATCH_RATE_PERCENT.set_function(
        lambda: _read_resuscitation_audit_summary_value("reversible_causes_match_rate_percent")
    )
    RESUSCITATION_RULE_AIRWAY_PLAN_MATCH_RATE_PERCENT.set_function(
        lambda: _read_resuscitation_audit_summary_value("airway_plan_match_rate_percent")
    )
    CARE_TASK_QUALITY_AUDIT_TOTAL.set_function(
        lambda: _read_quality_scorecard_value("total_audits")
    )
    CARE_TASK_QUALITY_AUDIT_MATCH_TOTAL.set_function(
        lambda: _read_quality_scorecard_value("matches")
    )
    CARE_TASK_QUALITY_AUDIT_UNDER_TOTAL.set_function(
        lambda: _read_quality_scorecard_value("under_events")
    )
    CARE_TASK_QUALITY_AUDIT_OVER_TOTAL.set_function(
        lambda: _read_quality_scorecard_value("over_events")
    )
    CARE_TASK_QUALITY_AUDIT_UNDER_RATE_PERCENT.set_function(
        lambda: _read_quality_scorecard_value("under_rate_percent")
    )
    CARE_TASK_QUALITY_AUDIT_OVER_RATE_PERCENT.set_function(
        lambda: _read_quality_scorecard_value("over_rate_percent")
    )
    CARE_TASK_QUALITY_AUDIT_MATCH_RATE_PERCENT.set_function(
        lambda: _read_quality_scorecard_value("match_rate_percent")
    )
    _REGISTERED = True
