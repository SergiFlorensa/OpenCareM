# Repositorio interno de conocimiento clinico

Este directorio almacena material interno por especialidad para referencia operacional.

## Estructura sugerida

- `app/knowledge/specialties/<especialidad>/`
  - documentos markdown o JSON de apoyo.

## Regla de uso en produccion

- El chat clinico prioriza siempre fuentes selladas en BD (`clinical_knowledge_sources`).
- Los archivos locales pueden usarse como material de trabajo, pero deben registrarse y
  sellarse por flujo profesional antes de ser considerados evidencia validada.
