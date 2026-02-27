# ADR-0087: Ciclo de reparacion `draft->verify->rewrite` en chat clinico

- Fecha: 2026-02-20
- Estado: Aprobado

## Contexto

En entorno local (Ollama + hardware limitado), algunas respuestas clinicas del
LLM se devolvian con:

- rechazo generico no operativo ("no puedo proporcionar asesoramiento..."),
- truncado de salida,
- baja profesionalidad estructural.

Aunque existia fallback rule-based, el objetivo operativo requiere una respuesta
mas estable, estructurada y con trazabilidad de fuentes.

## Decision

Se incorpora un ciclo de calidad previo al fallback final:

1. Generar borrador LLM.
2. Validar borrador con quality gates (accionable + grounded).
3. Si falla, ejecutar reescritura guiada con verificacion de fuentes internas
   (`rewrite_clinical_answer_with_verification`).
4. Volver a validar.
5. Si persiste fallo, usar fallback estructurado interno.

Adicionalmente, se endurece el gate para rechazar:

- respuestas de rechazo generico,
- respuestas clinicas truncadas.

## Consecuencias

Positivas:

- mayor consistencia profesional del formato clinico,
- menor fuga de respuestas no operativas,
- mejor alineacion con fuentes internas y trazabilidad.

Trade-offs:

- posible incremento de latencia en casos que activan reescritura,
- mayor dependencia de que el modelo local responda en ventana de timeout.

## Evidencia tecnica

- `app/services/llm_chat_provider.py`
- `app/services/clinical_chat_service.py`
- `app/tests/test_clinical_chat_operational.py`
- `agents/shared/test_plan.md`
