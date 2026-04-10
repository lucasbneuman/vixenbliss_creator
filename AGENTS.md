# AGENTS.md

## Objetivo del repositorio

Este repositorio es la base operativa de `VixenBliss Creator`. Su funcion es concentrar:

- contexto minimo para agentes y developers
- documentacion viva del producto, la arquitectura y el estado tecnico actual
- reglas operativas de trabajo
- evidencia reusable de decisiones y validaciones

No es un tablero de tareas manual. El estado transaccional del trabajo vive fuera del repo.

## Fuentes de verdad por prioridad

### Contexto compartido

1. `docs/03-process/working-agreement.md`
2. `docs/03-process/task-lifecycle.md`
3. `docs/03-process/README.md`
4. `docs/03-process/technical-documentation-policy.md`
5. `docs/03-process/branching-and-commits.md`
6. `docs/03-process/secrets-and-access.md`
7. `docs/03-process/youtrack-structure.md`

### Contexto para agentes

8. `docs/07-agents/README.md`
9. `docs/07-agents/agent-ops-contract.md`
10. `docs/07-agents/agent-ready-task-checklist.md`
11. `docs/07-agents/plan-prompt.md`
12. `docs/07-agents/implement-prompt.md`
13. `docs/07-agents/review-prompt.md`

### Contexto para developers

14. `docs/08-developers/README.md`
15. `docs/08-developers/developer-tooling-onboarding.md`

### Arquitectura tecnica vigente

16. `docs/00-product/vision.md`
17. `docs/01-architecture/technical-base.md`
18. `docs/01-architecture/agentic-brain.md`
19. `docs/01-architecture/agentic-brain-system1-implementation-guide.md`
20. `docs/01-architecture/identity-master-schema.md`
21. `docs/01-architecture/traceability-contracts.md`
22. `docs/01-architecture/visual-generation-engine.md`
23. `docs/01-architecture/comfyui-copilot-governance.md`
24. `docs/01-architecture/directus-s1-control-plane.md`
25. `docs/02-roadmap/roadmap-master.md`
26. `README.md`

Si hay contradicciones, prevalece el documento de mayor prioridad o la ADR mas reciente.

Los documentos en `docs/99-archive/` no son fuente de verdad activa. Solo pueden consultarse como contexto historico puntual.

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
2. Pasarla a estado `In Progress`.
3. Pedir plan en modo plan usando el contexto de este repo.
4. Esperar aprobacion explicita con `IMPLEMENTAR PLAN` o `PLAN OK`.
5. Implementar sobre `develop`, salvo pedido explicito de crear una rama nueva.
6. Ejecutar validaciones minimas.
7. Actualizar documentacion impactada.
8. Dejar comentario en la tarea con evidencia, bloqueos, dependencias externas, errores o inquietudes si aplica.
9. Cerrar la tarea cuando el trabajo este efectivamente terminado.
10. Hacer al menos un commit trazable por tarea o cambio cerrado.
11. Abrir PR con evidencia y checklist si corresponde.
12. Esperar aprobacion explicita con `MERGE OK`.
13. Hacer merge y dejar la evidencia enlazada.

No avanzar a una nueva tarea mientras la actual no tenga cierre operativo claro o handoff explicito.

## Politica de aprobacion

- `IMPLEMENTAR PLAN`: habilita implementacion de la tarea.
- `PLAN OK`: tambien habilita implementacion de la tarea.
- `MERGE OK`: habilita merge luego de checks y revision.
- `CLOSE OK`: habilita cierre administrativo cuando haga falta validacion externa.

No interpretar palabras ambiguas como aprobacion implicita.

## Reglas de edicion

- Hacer cambios pequenos, verificables y trazables.
- No mezclar feature, refactor y cambios cosmeticos en la misma PR.
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

- `docs/00-product/` define vision y foco de producto.
- `docs/01-architecture/` describe la arquitectura y contratos tecnicos vigentes.
- `docs/02-roadmap/` conserva direccion y contexto evolutivo sin reemplazar `YouTrack`.
- `docs/03-process/` define reglas de trabajo compartidas.
- `docs/04-decisions/` registra decisiones estables.
- `docs/05-qa/` define validacion y cierre.
- `docs/07-agents/` contiene contratos, prompts y checklists especificos para agentes.
- `docs/08-developers/` contiene onboarding y tooling especifico para developers.
- `docs/99-archive/` conserva material historico fuera de la cadena de fuentes de verdad.

Si una tarea cambia contratos, interfaces o decisiones de arquitectura, actualizar la documentacion correspondiente en el mismo cambio.

## Baseline de tooling compartido

El baseline operativo compartido para developers y agentes vive en:

- `env.example`
- `templates/agent-tooling/mcp.servers.example.json`
- `templates/agent-tooling/skills.manifest.example.yaml`
- `docs/07-agents/agent-ops-contract.md`
- `docs/08-developers/developer-tooling-onboarding.md`
- `docs/03-process/secrets-and-access.md`
- `docs/07-agents/agent-ready-task-checklist.md`
- `docs/03-process/technical-documentation-policy.md`

## Instrucciones para agentes

- Antes de implementar, leer este archivo y luego solo las fuentes minimas necesarias segun la tarea.
- Empezar siempre por `docs/03-process/working-agreement.md` y `docs/03-process/task-lifecycle.md`.
- Leer `docs/07-agents/` solo si la tarea involucra prompts, tooling agentico, MCPs, skills o criterio agent-ready.
- Leer `docs/08-developers/` solo si la tarea requiere bootstrap local, entorno o smoke checks de developer.
- Consultar `docs/01-architecture/` solo en la superficie tecnica que realmente toca el cambio.
- No usar `docs/99-archive/` como fuente de verdad activa salvo consulta historica puntual.
- Priorizar cambios pequenos y con superficie acotada.
- Si una tarea excede una sola superficie de cambio clara, proponer dividirla.
- Si una decision afecta interfaces o comportamiento transversal, exigir ADR.
- Si falta contexto operativo, consultar primero `working-agreement.md` y `task-lifecycle.md`.
