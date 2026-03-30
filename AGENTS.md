# AGENTS.md

## Objetivo del repositorio

Este repositorio es la base operativa de `VixenBliss Creator`. Su funcion es concentrar:

- contexto minimo para agentes y desarrolladores
- documentacion viva del producto y la arquitectura
- contexto estrategico y operativo reusable
- reglas operativas de trabajo
- evidencia reusable de decisiones y validaciones

No es un tablero de tareas manual. El estado transaccional de trabajo vive fuera del repo.

## Fuentes de verdad por prioridad

1. `docs/03-process/working-agreement.md`
2. `docs/03-process/task-lifecycle.md`
3. `docs/03-process/agent-ops-contract.md`
4. `docs/03-process/developer-tooling-onboarding.md`
5. `docs/03-process/secrets-and-access.md`
6. `docs/01-architecture/technical-base.md`
7. `docs/01-architecture/operational-architecture.md`
8. `docs/02-roadmap/roadmap-master.md`
9. `docs/02-roadmap/epic-01.md`
10. `docs/02-roadmap/epic-02.md`
11. `docs/02-roadmap/epic-03.md`
12. `docs/03-process/youtrack-structure.md`
13. `README.md`

Si hay contradicciones, prevalece el documento de mayor prioridad o la ADR mas reciente.

## Stack autorizado inicial

- `Python`
- `Docker`
- `Supabase/Postgres`
- `Supabase Storage` o `S3-compatible`
- `ComfyUI`
- `FluxSchnell`
- `OpenTelemetry`
- `Modal` o `Runpod`
- `GitHub`
- `YouTrack`

No introducir nuevas dependencias, servicios o patrones de arquitectura sin tarea asociada y, si aplica, ADR.

## Regla de trabajo obligatoria por tarea

1. Tomar una tarea desde `YouTrack`.
2. Pedir plan en modo plan usando el contexto de este repo.
3. Esperar aprobacion explicita con `IMPLEMENTAR PLAN` o `PLAN OK`.
4. Implementar sobre `develop`, salvo pedido explicito de crear una rama nueva.
5. Ejecutar validaciones minimas.
6. Actualizar documentacion impactada.
7. Hacer al menos un commit trazable por tarea o cambio cerrado.
8. Abrir PR con evidencia y checklist.
9. Esperar aprobacion explicita con `MERGE OK`.
10. Hacer merge y cerrar la tarea con evidencia enlazada.

No avanzar a una nueva tarea mientras la actual no tenga cierre operativo claro o handoff explicito.

## Politica de aprobacion

- `IMPLEMENTAR PLAN`: habilita implementacion de la tarea.
- `PLAN OK`: tambien habilita implementacion de la tarea.
- `MERGE OK`: habilita merge luego de checks y revision.
- `CLOSE OK`: habilita cierre administrativo cuando haga falta validacion externa.

No interpretar palabras ambiguas como aprobacion implicita.

## Reglas de edicion

- Hacer cambios pequenos, verificables y trazables.
- No mezclar feature, refactor y cambios cosméticos en la misma PR.
- No reescribir decisiones ya tomadas sin ADR o issue asociada.
- No convertir este repo en un registro manual de bugs o tareas.
- No duplicar el tracking entre `YouTrack` y archivos `.md`.
- Permitir trabajo ad hoc o mejoras extraoficiales solo si no contradicen el faro operativo de `YouTrack` y dejan evidencia trazable.

## Politica de ramas y commits

- Trabajo diario por defecto en `develop`.
- `main` queda reservado para integracion estable.
- No crear ramas nuevas salvo pedido explicito.
- Si excepcionalmente se pide una rama nueva, debe estar ligada a una tarea concreta.
- Cada tarea o cambio cerrado debe dejar al menos un commit actualizado y trazable.
- Cada commit debe referenciar la tarea o issue cuando exista.
- Cada PR debe enlazar una tarea o issue.

Ver detalle en `docs/03-process/branching-and-commits.md`.

## Politica de pruebas

Toda implementacion debe, como minimo:

- compilar o levantar correctamente
- pasar pruebas relevantes
- no romper contratos existentes
- actualizar documentacion afectada
- dejar evidencia minima en la PR

Ver detalle en `docs/05-qa/test-strategy.md`.

## Politica de documentacion

- `docs/02-roadmap/` aporta vision flexible, contexto estrategico y contratos de alto nivel.
- `docs/01-architecture/` define el como.
- `docs/03-process/` define el modo de trabajo.
- `docs/04-decisions/` registra decisiones estables.
- `docs/05-qa/` define validacion y cierre.
- `docs/06-prompts/` estandariza pedidos a agentes.

Si una tarea cambia contratos, interfaces o decisiones de arquitectura, actualizar la documentacion correspondiente en el mismo cambio.
La documentacion tecnica debe registrar tanto el objetivo futuro como el camino recorrido: que se hizo, como quedo y que aprendizaje o decision lo explica.

El baseline de tooling compartido para developers y agentes vive en:

- `.env.example`
- `templates/agent-tooling/mcp.servers.example.json`
- `templates/agent-tooling/skills.manifest.example.yaml`
- `docs/03-process/agent-ops-contract.md`
- `docs/03-process/developer-tooling-onboarding.md`
- `docs/03-process/secrets-and-access.md`
- `docs/03-process/agent-ready-task-checklist.md`
- `docs/03-process/technical-documentation-policy.md`

## Instrucciones para agentes

- Antes de implementar, leer este archivo y luego solo las fuentes minimas necesarias.
- Priorizar cambios pequenos y con superficie acotada.
- Si una tarea excede una sola superficie de cambio clara, proponer dividirla.
- Si una decision afecta interfaces o comportamiento transversal, exigir ADR.
- Si falta contexto operativo, consultar primero `working-agreement.md` y `task-lifecycle.md`.
- Si la tarea depende de tooling, MCPs, skills o credenciales, consultar tambien `agent-ops-contract.md`, `developer-tooling-onboarding.md`, `secrets-and-access.md` y `agent-ready-task-checklist.md`.
