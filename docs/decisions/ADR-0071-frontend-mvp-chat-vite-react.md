# ADR-0071: Frontend MVP de Chat Clinico con Vite + React

- Fecha: 2026-02-15
- Estado: Aprobado

## Contexto

Se requiere una interfaz moderna para simular interaccion profesional con el
chat clinico y validar experiencia de uso en urgencias, con minima complejidad
de despliegue y mantenimiento.

## Decision

Implementar un frontend MVP en `frontend/` con:

- `Vite + React + TypeScript`
- UI dark/minimal tipo chat moderno
- consumo directo de endpoints ya existentes (`auth`, `care-tasks`, `chat`)

No se modifica contrato de API en esta fase.

## Consecuencias

### Positivas

- Arranque rapido y bajo coste operativo.
- Menor friccion para pruebas de producto con profesionales.
- Base reutilizable para evolucion posterior a tablero completo.

### Riesgos

- Feature set acotado (sin streaming, sin paneles avanzados).
- Necesidad de mantener CORS coherente con origen del frontend.

## Mitigaciones

- Documentar ejecucion local y CORS.
- Mantener UI enfocada a flujo clinico esencial.
- Evolucionar por iteraciones sobre feedback de uso real.

## Validacion

- `cd frontend && npm install`
- `cd frontend && npm run build`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_settings_security.py`
