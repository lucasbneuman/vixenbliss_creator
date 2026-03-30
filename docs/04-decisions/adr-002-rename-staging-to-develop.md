# ADR-002: Renombrar la rama operativa de `staging` a `develop`

## Estado

Aprobada

## Contexto

La rama diaria del repositorio venia documentada como `staging`, pero el equipo decidio unificar la convencion operativa alrededor de `develop` para reducir ambiguedad entre trabajo diario, integracion temprana y lenguaje usado en tareas y handoffs.

Este cambio impacta reglas de trabajo, referencias en documentacion y configuracion Git del repositorio.

## Decision

Se adopta `develop` como rama operativa por defecto.

- `develop` reemplaza a `staging` en reglas de trabajo, QA y handoff
- `main` sigue reservado para integracion estable
- el rename debe reflejarse tanto en Git como en la documentacion viva del repo

## Consecuencias

Positivas:

- una unica convencion visible para trabajo diario
- menos friccion al abrir PRs, dejar evidencia y coordinar handoffs
- menos contradicciones entre proceso documentado y operacion real

Costos:

- requiere actualizar referencias documentales existentes
- requiere coordinar tracking remoto y retiro de la rama anterior

## Revision futura

Revisar esta ADR si el flujo de release incorpora ambientes adicionales o si `develop` deja de ser la rama de integracion diaria.
