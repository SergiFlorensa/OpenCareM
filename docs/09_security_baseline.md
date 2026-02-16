# Base de Seguridad

Reglas minimas de seguridad aplicadas en configuracion.

## Validaciones activas en Settings

Archivo: `app/core/config.py`

Si `ENVIRONMENT != development`:

- `SECRET_KEY` no puede ser el valor por defecto del proyecto.
- `SECRET_KEY` debe tener al menos 32 caracteres.
- `BACKEND_CORS_ORIGINS` no puede incluir `"*"`.

## Objetivo

- Fallar rapido ante configuraciones inseguras.
- Evitar despliegues con secretos por defecto.
- Evitar CORS global en entornos no locales.

## Como verificar

- Ejecutar tests:
  - `pytest -q`
- Revisar pruebas de seguridad:
  - `app/tests/test_settings_security.py`



