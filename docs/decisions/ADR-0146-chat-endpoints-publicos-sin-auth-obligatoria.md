# ADR-0146: Chat Endpoints Publicos sin Auth Obligatoria

## Estado

Aprobado

## Contexto

El flujo de pruebas de chat en frontend requiere iteracion rapida y el login obligatorio
estaba bloqueando el uso operativo diario. El servicio de chat ya soportaba
`authenticated_user=None` en flujo sincrono, pero la cola asincrona imponia usuario.

## Decision

- Los endpoints de chat en `care-tasks` pasan a modo publico:
  - `POST /care-tasks/{id}/chat/messages`
  - `POST /care-tasks/{id}/chat/messages/async`
  - `GET /care-tasks/{id}/chat/messages`
  - `GET /care-tasks/{id}/chat/memory`
  - `GET /care-tasks/{id}/chat/messages/async/{job_id}`
- Se introduce dependencia de autenticacion opcional:
  - si hay bearer valido, se adjunta usuario;
  - si no hay token o es invalido, se procesa como anonimo.
- La cola asincrona guarda `user_id` nullable y ejecuta el worker con usuario opcional.

## Consecuencias

- Mejora de UX para pruebas y uso interno inmediato del chat.
- Se mantiene compatibilidad con trazas por usuario cuando exista token.
- Riesgo: endpoints publicos pueden aumentar superficie de abuso; mitigable con rate limit
  en capa perimetral o feature flag futura.
