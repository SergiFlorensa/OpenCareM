# Playbook Operativo: Curacion y Sellado de Fuentes Clinicas

## Objetivo

Definir un proceso unico para que la evidencia usada por el chat clinico sea:

- fiable,
- trazable,
- y mantenida en el tiempo sin deriva de calidad.

## Roles

- **Autor Clinico**: propone fuente y contexto de uso.
- **Revisor Especialista**: valida rigor tecnico y aplicabilidad clinica.
- **Admin Clinico (superuser)**: ejecuta sellado final en plataforma.
- **Responsable de Seguridad**: mantiene whitelist de dominios.

## Regla de oro

- Ninguna fuente se usa como evidencia interna hasta estado `validated`.
- Fuentes fuera de whitelist no entran en sistema.
- YouTube se usa solo como descubrimiento; la evidencia final debe venir de
  fuente primaria en whitelist (guia, paper, sociedad cientifica).

## Flujo E2E

1. **Alta de fuente (`pending_review`)**
   - `POST /api/v1/knowledge-sources/`
   - Datos minimos:
     - `specialty`
     - `title`
     - `source_type`
     - (`content` o `source_url` o `source_path`)
2. **Pre-filtro automatico**
   - dominio permitido (`trusted-domains`),
   - normalizacion de etiquetas,
   - rechazo inmediato de URL no autorizada.
3. **Revision profesional**
   - consistencia cientifica,
   - actualidad (fecha/version),
   - utilidad operativa en urgencias.
4. **Sellado**
   - `POST /api/v1/knowledge-sources/{id}/seal`
   - decisiones:
     - `approve` -> `validated`
     - `reject` -> `rejected`
     - `expire` -> `expired`
5. **Publicacion efectiva**
   - el chat solo prioriza fuentes `validated` y no expiradas.

## Checklist de sellado (obligatorio)

- Fuente primaria identificable.
- Dominio en whitelist.
- Contenido coherente con guias/protocolos vigentes.
- Fecha/version o criterio de vigencia definido.
- Nota de validacion profesional registrada.

## Politica de vigencia

- Fuentes con `expires_at` vencida pasan a no recomendadas hasta revalidacion.
- Revalidacion recomendada:
  - alta criticidad: cada 90 dias,
  - resto: cada 180 dias.

## Gestion de incidentes

Si una fuente validada queda cuestionada (retractacion, guia sustituida, etc.):

1. Sellar inmediatamente como `expire` o `reject`.
2. Registrar nota de incidente.
3. Sustituir por fuente actualizada.
4. Revisar consultas recientes impactadas.

## KPIs operativos sugeridos

- `% fuentes validadas` por especialidad.
- `tiempo medio de sellado` (alta -> `validated`).
- `% fuentes expiradas` pendientes de revision.
- `% respuestas de chat sin fuente validada`.

## Ejemplo rapido de operacion

1. Alta por profesional:
   - `POST /api/v1/knowledge-sources/`
2. Revisor consulta y confirma:
   - `GET /api/v1/knowledge-sources/?validated_only=false`
3. Sellado admin:
   - `POST /api/v1/knowledge-sources/{id}/seal` con `decision=approve`
4. Ver trazabilidad:
   - `GET /api/v1/knowledge-sources/{id}/validations`
