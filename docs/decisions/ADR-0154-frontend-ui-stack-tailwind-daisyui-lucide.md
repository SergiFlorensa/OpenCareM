# ADR-0154: UI Stack Frontend con Tailwind + daisyUI + Lucide

## Estado

Aprobado

## Contexto

La interfaz del chat estaba basada en CSS manual. Se requeria una capa visual mas moderna
con componentes reutilizables, mejor consistencia y menor coste de mantenimiento.

## Decision

1. Adoptar TailwindCSS como base utilitaria de estilos.
2. Incorporar daisyUI para componentes preconstruidos (botones, badges, inputs, toasts, etc.).
3. Usar `lucide-react` para iconografia coherente y liviana.
4. Mantener arquitectura React/Vite existente sin introducir framework UI propietario.

## Consecuencias

- Entrega visual mas moderna sin romper el flujo funcional del chat.
- Aceleracion de iteraciones futuras de UI.
- Incremento moderado del CSS generado (controlable con purga de Tailwind).
