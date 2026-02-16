# ADR-0006: Proteccion de login contra brute force

## Contexto

El endpoint de login aceptaba intentos ilimitados, lo que dejaba abierta la puerta
a ataques de fuerza bruta sobre usuarios conocidos.

## Decision

Implementar rate limit de autenticacion por combinacion `username + IP` con estado persistente:

- contador de fallos en ventana temporal
- bloqueo temporal al superar umbral
- reseteo de estado tras login exitoso

## Consecuencias

Beneficios:

- Menor superficie de ataque en autenticacion.
- Comportamiento reproducible y auditable en base de datos.

Costes:

- Escrituras adicionales en DB para intentos fallidos.
- Necesidad de ajustar umbrales por entorno.

## Validacion

- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_auth_api.py`
- Comprobar respuestas `401`, `429` y desbloqueo por login valido.



