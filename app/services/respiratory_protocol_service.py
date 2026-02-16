"""
Reglas operativas de infecciones respiratorias viricas en urgencias.

No realiza diagnostico: propone acciones tempranas para mejorar tiempos
y seguridad en pacientes vulnerables.
"""
from app.schemas.respiratory_protocol import (
    RespiratoryProtocolRecommendation,
    RespiratoryProtocolRequest,
)


class RespiratoryProtocolService:
    """Motor de recomendaciones tempranas para COVID/Gripe/VRS."""

    @staticmethod
    def _is_vulnerable(payload: RespiratoryProtocolRequest) -> bool:
        return bool(
            payload.age_years >= 65
            or payload.immunosuppressed
            or len(payload.comorbidities) > 0
            or payload.vaccination_updated_last_12_months is False
        )

    @staticmethod
    def _has_relative_shock(payload: RespiratoryProtocolRequest) -> bool:
        if payload.current_systolic_bp is None or payload.baseline_systolic_bp is None:
            return False
        return payload.baseline_systolic_bp >= 140 and payload.current_systolic_bp <= 110

    @staticmethod
    def _build_diagnostic_plan(payload: RespiratoryProtocolRequest, vulnerable: bool) -> list[str]:
        plan: list[str] = []
        if payload.antigen_result == "no_realizado":
            plan.append("Realizar test de antigeno respiratorio en triaje.")

        need_pcr = (
            payload.antigen_result == "negativo"
            and (vulnerable or payload.immunosuppressed or payload.needs_oxygen)
        )
        if need_pcr:
            plan.append("Escalar a PCR / tecnica molecular multiple por alto riesgo.")

        if payload.pathogen_suspected == "vrs" and payload.antigen_result == "negativo":
            plan.append(
                "Para VRS en adulto: usar muestra combinada (saliva + exudado nasofaringeo)."
            )
        return plan

    @staticmethod
    def _build_antiviral_plan(payload: RespiratoryProtocolRequest, vulnerable: bool) -> list[str]:
        plan: list[str] = []
        onset_hours = payload.symptom_onset_hours
        if payload.pathogen_suspected == "covid":
            if payload.needs_oxygen:
                plan.append("Valorar Remdesivir IV 5-10 dias por cuadro grave.")
            elif vulnerable and onset_hours is not None and onset_hours <= 5 * 24:
                if payload.oral_antiviral_contraindicated:
                    plan.append(
                        "Valorar Remdesivir IV 3 dias por contraindicación de antiviral oral."
                    )
                else:
                    plan.append(
                        "Valorar Nirmatrelvir/Ritonavir VO 5 dias (<5 dias de inicio)."
                    )
            elif vulnerable and onset_hours is not None and onset_hours <= 7 * 24:
                plan.append("Valorar Remdesivir IV 3 dias (<7 dias de inicio).")

        if payload.pathogen_suspected == "gripe":
            if payload.needs_oxygen:
                plan.append(
                    "Iniciar Oseltamivir precozmente; objetivo operativo ideal <6h desde llegada."
                )
            elif vulnerable and onset_hours is not None and onset_hours <= 48:
                plan.append("Iniciar Oseltamivir en ventana <48h.")

        if payload.pathogen_suspected == "vrs":
            plan.append(
                "No hay antiviral estandar de urgencias; priorizar soporte y vigilancia estrecha."
            )
        return plan

    @staticmethod
    def _build_isolation_plan(payload: RespiratoryProtocolRequest) -> list[str]:
        plan: list[str] = []
        if payload.pathogen_suspected == "covid":
            plan.append("Aplicar control de aerosoles estricto y mascarilla.")
            plan.append("Minimizar estancia en zonas congestionadas y reforzar ventilacion.")
        if payload.pathogen_suspected == "gripe":
            plan.append("Aplicar aislamiento respiratorio segun protocolo local.")
        if payload.pathogen_suspected == "vrs":
            plan.append("Aislar de forma activa para prevenir transmision nosocomial en mayores.")
        return plan

    @staticmethod
    def _build_alerts(
        payload: RespiratoryProtocolRequest,
        vulnerable: bool,
        shock_relative: bool,
    ) -> list[str]:
        alerts: list[str] = []
        if vulnerable:
            alerts.append("Paciente vulnerable: priorizar evaluacion y circuito rapido.")
        if shock_relative:
            alerts.append("Sospecha de shock relativo en paciente con basal hipertensa.")
        if payload.immunosuppressed and payload.pathogen_suspected == "covid":
            alerts.append("Inmunosupresion: vigilar posible replicacion viral persistente.")
        if payload.pathogen_suspected == "gripe" and payload.hours_since_er_arrival is not None:
            if payload.hours_since_er_arrival > 6:
                alerts.append("Ventana operativa >6h para gripe grave: revisar demora terapeutica.")
        return alerts

    @staticmethod
    def build_recommendation(
        payload: RespiratoryProtocolRequest,
    ) -> RespiratoryProtocolRecommendation:
        """Construye recomendacion respiratoria trazable para urgencias."""
        vulnerable = RespiratoryProtocolService._is_vulnerable(payload)
        shock_relative = RespiratoryProtocolService._has_relative_shock(payload)
        return RespiratoryProtocolRecommendation(
            vulnerable_patient=vulnerable,
            shock_relative_suspected=shock_relative,
            diagnostic_plan=RespiratoryProtocolService._build_diagnostic_plan(payload, vulnerable),
            antiviral_plan=RespiratoryProtocolService._build_antiviral_plan(payload, vulnerable),
            isolation_plan=RespiratoryProtocolService._build_isolation_plan(payload),
            alerts=RespiratoryProtocolService._build_alerts(payload, vulnerable, shock_relative),
            non_clinical_warning=(
                "Soporte operativo no diagnostico. Requiere validacion clinica humana."
            ),
        )
