# Branching and Commits

## Objetivo

Reducir conflictos entre dos desarrolladores y mantener trazabilidad entre tarea, rama, commit y PR.

## Convenciones de ramas

Formato recomendado:

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

## Reglas de ramas

- una tarea por rama
- no compartir ramas
- no reutilizar una rama para otra tarea
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
