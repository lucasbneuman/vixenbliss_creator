# Branching and Commits

## Objetivo

Reducir conflictos entre dos desarrolladores y mantener trazabilidad entre tarea, commit y PR con una politica minima de ramas.

## Politica actual de ramas

- `staging` es la rama de trabajo diaria.
- `main` es la rama estable de integracion.
- No crear ramas nuevas salvo pedido explicito.
- Si se autoriza una rama excepcional, debe estar asociada a una tarea concreta y usarse solo para ese objetivo.

## Convenciones para ramas excepcionales

Formato recomendado cuando se pida una rama nueva:

```text
<tipo>/<tracker-id>-<slug-corto>
```

Ejemplos:

```text
feature/DEV-123-identity-schema
fix/DEV-214-job-timeout
docs/DEV-305-agents-router
chore/DEV-410-ci-bootstrap
codex/DEV-512-lora-registry
```

## Reglas para ramas excepcionales

- crearla solo si fue pedida explicitamente
- asociarla a una sola tarea concreta
- no compartirla entre desarrolladores
- no reutilizarla para otra tarea
- no mezclar trabajo experimental con trabajo listo para revision

## Convenciones de commits

Formato recomendado:

```text
<tipo>(<scope opcional>): <tracker-id> <resumen>
```

Ejemplos:

```text
feat(identity): DEV-123 add identity master schema
fix(worker): DEV-214 enforce timeout handling
docs(process): DEV-305 define task lifecycle
chore(ci): DEV-410 add repo structure checks
```

## Pull Requests

Toda PR debe:

- referenciar la tarea o issue
- indicar alcance y riesgo
- listar validaciones ejecutadas
- aclarar documentacion actualizada
- ser pequena y facil de revisar

## Merge strategy

Preferencia inicial:

- `Squash and merge` para tareas pequenas
- mantener titulo de PR alineado a la tarea

Cambiar la estrategia solo si el volumen o el tipo de trabajo lo requiere.
