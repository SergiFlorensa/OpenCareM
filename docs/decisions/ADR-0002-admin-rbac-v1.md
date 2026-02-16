# ADR-0002: RBAC admin minimo en capa API

## Contexto

Tras incorporar usuarios persistentes y bootstrap del primer admin, faltaba un control real de permisos para endpoints sensibles.

## Decision

Implementar RBAC v1 con una regla simple:

- `is_superuser = True` habilita endpoints admin.
- `is_superuser = False` bloquea con `403`.

La evaluacion del rol se hace en dependencias FastAPI reutilizables (`app/api/deps.py`), no en cada endpoint de forma manual.

## Consecuencias

Impacto positivo:

- Control de acceso claro y centralizado.
- Menor duplicacion de codigo.
- Base lista para crecer a permisos mas granulares.

Costo:

- Modelo de permisos aun binario (admin/no admin).
- No hay auditoria de acciones admin en esta fase.

## Validacion

- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_auth_api.py`
- Verificar casos:
  - sin token -> `401`
  - token usuario normal -> `403`
  - token admin -> `200`



