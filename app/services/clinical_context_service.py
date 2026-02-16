"""
Servicio de catalogo clinico-operativo.

Concentra contexto de urgencias basado en escenarios reales para usarlo
en agentes, reglas y frontend sin acoplarse todavia a una DB dedicada.
"""
from app.schemas.clinical_context import (
    AreaUrgenciasResponse,
    CircuitoTriageResponse,
    ContextoClinicoResumenResponse,
    EstandarOperativoResponse,
    ProcedimientoChecklistResponse,
    RolOperativoResponse,
    TriageLevelResponse,
)

AREAS_URGENCIAS: list[AreaUrgenciasResponse] = [
    AreaUrgenciasResponse(
        codigo="consultas_intermedios",
        nombre="Area de Consultas / Intermedios",
        tipo="consultas",
        capacidad_total=14,
        capacidad_aislamiento=0,
        monitorizada=False,
        estancia_objetivo_horas_max=None,
        zona_seguridad="verde",
        descripcion="Consultas de valoracion inicial y reevaluacion clinica.",
    ),
    AreaUrgenciasResponse(
        codigo="camas_monitorizadas",
        nombre="Area de Camas Monitorizadas",
        tipo="camas",
        capacidad_total=31,
        capacidad_aislamiento=4,
        monitorizada=True,
        estancia_objetivo_horas_max=None,
        zona_seguridad="mixta",
        descripcion="Camas para pacientes que requieren monitorizacion continua.",
    ),
    AreaUrgenciasResponse(
        codigo="observacion_24_36h",
        nombre="Area de Observacion",
        tipo="observacion",
        capacidad_total=18,
        capacidad_aislamiento=0,
        monitorizada=True,
        estancia_objetivo_horas_max=36,
        zona_seguridad="verde",
        descripcion="Estancias de corta evolucion clinica (24-36 horas).",
    ),
    AreaUrgenciasResponse(
        codigo="sillones_tratamiento",
        nombre="Area de Sillones",
        tipo="sillones",
        capacidad_total=16,
        capacidad_aislamiento=0,
        monitorizada=False,
        estancia_objetivo_horas_max=24,
        zona_seguridad="verde",
        descripcion="Tratamientos y cuidados sin necesidad de cama.",
    ),
    AreaUrgenciasResponse(
        codigo="zona_roja_contaminada",
        nombre="Zona Roja / Contaminada",
        tipo="seguridad",
        capacidad_total=0,
        capacidad_aislamiento=0,
        monitorizada=False,
        estancia_objetivo_horas_max=None,
        zona_seguridad="roja",
        descripcion="Zona de alto riesgo biologico con EPI obligatorio.",
    ),
    AreaUrgenciasResponse(
        codigo="zona_verde_limpia",
        nombre="Zona Verde / Limpia",
        tipo="seguridad",
        capacidad_total=0,
        capacidad_aislamiento=0,
        monitorizada=False,
        estancia_objetivo_horas_max=None,
        zona_seguridad="verde",
        descripcion="Zona limpia con circuitos no contaminados.",
    ),
]

CIRCUITOS_TRIAGE: list[CircuitoTriageResponse] = [
    CircuitoTriageResponse(
        codigo="circuito_1_ambulantes",
        nombre="Circuito 1 - Ambulantes",
        criterio_entrada="Paciente deambula por si mismo.",
        acciones_tempranas=[
            "Registrar motivo de consulta y constantes iniciales.",
            "Si hay fiebre o sintomas respiratorios, activar mascarilla e higiene precoz.",
        ],
        destino_recomendado="Consultas / Intermedios",
    ),
    CircuitoTriageResponse(
        codigo="circuito_2_encamados",
        nombre="Circuito 2 - Encamados",
        criterio_entrada="Paciente requiere camilla, monitorizacion o es inmunodeprimido.",
        acciones_tempranas=[
            "Priorizar traslado directo sin demoras.",
            "Preparar monitorizacion y circuito de seguridad.",
        ],
        destino_recomendado="Observacion o Camas monitorizadas",
    ),
]

ROLES_OPERATIVOS: list[RolOperativoResponse] = [
    RolOperativoResponse(
        nombre="celador",
        descripcion="Gestiona traslados internos y soporte logistico.",
        responsabilidades=[
            "Traslado seguro entre areas.",
            "Priorizar rutas segun circuito asignado.",
        ],
        permisos_aplicacion=["care_tasks:read", "care_tasks:update_logistica"],
    ),
    RolOperativoResponse(
        nombre="enfermeria_tcae",
        descripcion="Ejecuta triaje operativo, cuidados y seguimiento inicial.",
        responsabilidades=[
            "Captura de constantes y motivo de consulta.",
            "Aplicar medidas tempranas de seguridad.",
        ],
        permisos_aplicacion=["care_tasks:read", "care_tasks:update_clinical_context"],
    ),
    RolOperativoResponse(
        nombre="medico_apoyo",
        descripcion="Apoya priorizacion asistencial y decisiones de destino.",
        responsabilidades=[
            "Validar complejidad del caso.",
            "Confirmar necesidad de observacion o ingreso.",
        ],
        permisos_aplicacion=["care_tasks:read", "care_tasks:triage", "care_tasks:approve_triage"],
    ),
    RolOperativoResponse(
        nombre="admision",
        descripcion="Registra entrada/salida y datos administrativos del episodio.",
        responsabilidades=[
            "Registrar tiempos de proceso.",
            "Asegurar trazabilidad documental del episodio.",
        ],
        permisos_aplicacion=["care_tasks:read", "care_tasks:update_admission"],
    ),
]

PROCEDIMIENTOS_CHECKLIST: list[ProcedimientoChecklistResponse] = [
    ProcedimientoChecklistResponse(
        clave="montaje_lucas",
        nombre="Montaje del sistema LUCAS",
        pasos=[
            "Encender equipo y esperar autochequeo.",
            "Colocar soporte dorsal minimizando interrupcion de RCP manual.",
            "Fijar compresor hasta confirmar clic de seguridad.",
            "Ajustar ventosa sobre esternon en posicion correcta.",
        ],
        objetivo_operativo="Estandarizar despliegue rapido en soporte circulatorio.",
        advertencia_seguridad=(
            "Uso exclusivo por personal entrenado y protocolos vigentes del centro."
        ),
    ),
    ProcedimientoChecklistResponse(
        clave="test_elevacion_pasiva_piernas",
        nombre="Test de elevacion pasiva de piernas (PRL)",
        pasos=[
            "Elevar piernas a 45 grados.",
            "Descender tronco a 0 grados.",
            "Mantener posicion al menos un minuto.",
            "Registrar respuesta hemodinamica observada.",
        ],
        objetivo_operativo="Apoyo a evaluacion dinamica de respuesta a fluidos.",
        advertencia_seguridad="No sustituye criterio medico ni protocolos de manejo hemodinamico.",
    ),
]

ESTANDARES_OPERATIVOS: list[EstandarOperativoResponse] = [
    EstandarOperativoResponse(
        codigo="tiempo_total_urgencias_objetivo",
        nombre="Tiempo maximo objetivo de episodio",
        descripcion="Tiempo desde admision hasta resolucion/derivacion.",
        valor_objetivo="4",
        unidad="horas",
    ),
    EstandarOperativoResponse(
        codigo="estancia_observacion_maxima",
        nombre="Estancia maxima en observacion",
        descripcion="Tiempo maximo esperado en area de observacion.",
        valor_objetivo="36",
        unidad="horas",
    ),
    EstandarOperativoResponse(
        codigo="variables_modelo_ingreso",
        nombre="Variables minimas para modelo predictivo de ingreso",
        descripcion="Conjunto de variables operativas-clinicas para analitica predictiva.",
        valor_objetivo="14",
        unidad="variables",
    ),
]

TRIAGE_LEVELS_MANCHESTER: list[TriageLevelResponse] = [
    TriageLevelResponse(
        sistema="manchester",
        nivel=1,
        color="rojo",
        etiqueta="Inmediato",
        descripcion="Riesgo vital actual; requiere atencion inmediata.",
        sla_objetivo_minutos=0,
    ),
    TriageLevelResponse(
        sistema="manchester",
        nivel=2,
        color="naranja",
        etiqueta="Emergencia",
        descripcion="Alto riesgo de deterioro; prioridad maxima tras nivel 1.",
        sla_objetivo_minutos=10,
    ),
    TriageLevelResponse(
        sistema="manchester",
        nivel=3,
        color="amarillo",
        etiqueta="Urgencia",
        descripcion="Precisa valoracion preferente en ventana corta.",
        sla_objetivo_minutos=30,
    ),
    TriageLevelResponse(
        sistema="manchester",
        nivel=4,
        color="verde",
        etiqueta="Menor urgencia",
        descripcion="Puede requerir pruebas diagnosticas sin riesgo inmediato.",
        sla_objetivo_minutos=120,
    ),
    TriageLevelResponse(
        sistema="manchester",
        nivel=5,
        color="azul",
        etiqueta="No urgente",
        descripcion="Caso no urgente y estable; sin prioridad asistencial inmediata.",
        sla_objetivo_minutos=240,
    ),
]


class ClinicalContextService:
    """Proveedor de contexto clinico-operativo versionado para el sistema."""

    VERSION_CONTEXTO = "urgencias_es_v1"
    ADVERTENCIA_USO = (
        "Contexto orientado a operaciones y entrenamiento. "
        "No usar para diagnostico ni decision clinica autonoma."
    )

    @staticmethod
    def list_areas() -> list[AreaUrgenciasResponse]:
        return AREAS_URGENCIAS

    @staticmethod
    def list_circuitos() -> list[CircuitoTriageResponse]:
        return CIRCUITOS_TRIAGE

    @staticmethod
    def list_roles() -> list[RolOperativoResponse]:
        return ROLES_OPERATIVOS

    @staticmethod
    def list_procedimientos() -> list[ProcedimientoChecklistResponse]:
        return PROCEDIMIENTOS_CHECKLIST

    @staticmethod
    def get_procedimiento(clave: str) -> ProcedimientoChecklistResponse | None:
        normalized = clave.strip().lower()
        return next((item for item in PROCEDIMIENTOS_CHECKLIST if item.clave == normalized), None)

    @staticmethod
    def list_estandares() -> list[EstandarOperativoResponse]:
        return ESTANDARES_OPERATIVOS

    @staticmethod
    def get_resumen() -> ContextoClinicoResumenResponse:
        return ContextoClinicoResumenResponse(
            version_contexto=ClinicalContextService.VERSION_CONTEXTO,
            total_areas=len(AREAS_URGENCIAS),
            total_circuitos=len(CIRCUITOS_TRIAGE),
            total_roles=len(ROLES_OPERATIVOS),
            total_procedimientos=len(PROCEDIMIENTOS_CHECKLIST),
            total_estandares=len(ESTANDARES_OPERATIVOS),
            advertencia_uso=ClinicalContextService.ADVERTENCIA_USO,
        )

    @staticmethod
    def list_triage_levels_manchester() -> list[TriageLevelResponse]:
        """Lista niveles de triaje Manchester con color y SLA objetivo."""
        return TRIAGE_LEVELS_MANCHESTER
