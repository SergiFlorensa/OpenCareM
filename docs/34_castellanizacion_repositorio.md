# Estrategia de Castellanizacion del Repositorio (es-ES)

## Objetivo

Traducir progresivamente el repositorio a espanol de Espana sin romper API, tests ni compatibilidad operativa.

## Regla principal

Primero se traduce lo visible para personas:

1. Documentacion.
2. Mensajes de error y textos de respuesta.
3. Comentarios y docstrings.

Despues, en fases separadas, se estudia traducir nombres internos (clases, variables, rutas) cuando sea seguro.

## Fases recomendadas

### Fase A - Textos visibles (actual)

- Mensajes HTTP (`detail`) en espanol.
- Documentacion de flujos y contratos en espanol.
- Comentarios/docstrings en espanol.
- Estado actual: completada en TM-039.

### Fase B - Contratos externos

- Mantener endpoints actuales.
- Si se quiere endpoint en espanol, agregar alias sin romper el endpoint existente.
- Marcar deprecaciones con fechas.

### Fase C - Nombres internos

- Renombrar modulos/servicios en cambios pequenos.
- Ejecutar regresion completa en cada lote.
- Evitar renombres masivos de una sola vez.

## Criterios de calidad

- Cada lote debe incluir:
  - Cambio de codigo.
  - Cambio de documentacion.
  - Prueba automatizada en verde.
  - Riesgos pendientes anotados.

## Riesgos conocidos

- Ruptura de clientes por cambio de rutas o payload.
- Mezcla de idiomas durante la transicion.
- Aumento temporal de complejidad por coexistencia de terminos.


