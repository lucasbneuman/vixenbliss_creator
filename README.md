# VixenBliss Creator

Base documental y operativa para construir `VixenBliss Creator` desde cero con un flujo pensado para dos desarrolladores y agentes como `Codex`.

## Que contiene este repositorio

- arquitectura y base tecnica del sistema
- contexto estrategico, arquitectura y proceso operativo
- reglas operativas de trabajo
- contrato operativo para agentes, MCPs, skills y credenciales
- onboarding reproducible para desarrolladores y agentes
- plantillas para pedir plan, implementacion y review a agentes
- configuracion minima de GitHub para PRs, issues y CI

## Principios de trabajo

- fuente de verdad unica por tema
- tareas chicas, verificables y trazables
- plan antes de implementar
- aprobacion explicita antes de avanzar
- PR obligatoria para merge
- documentacion viva junto con el codigo

## Estructura

```text
.
|-- AGENTS.md
|-- README.md
|-- docs/
|   |-- 00-product/
|   |-- 01-architecture/
|   |-- 02-roadmap/
|   |-- 03-process/
|   |-- 04-decisions/
|   |-- 05-qa/
|   `-- 06-prompts/
`-- .github/
```

## Fuente de verdad recomendada

- Trabajo operativo, backlog, prioridades y evolucion de tareas: `YouTrack`
- Codigo, PRs y releases: `GitHub`
- Proceso, arquitectura, contratos, decisiones y documentacion tecnica: repo `docs/`

No duplicar el estado de tareas y bugs dentro del repo.
El roadmap del repo existe como vision flexible y contexto tecnico, no como agenda rigida de ejecucion.

## Flujo recomendado por tarea

1. Seleccionar tarea en `YouTrack`.
2. Pasarla a `In Progress`.
3. Pedir plan a Codex.
4. Aprobar con `IMPLEMENTAR PLAN` o `PLAN OK`.
5. Implementar sobre `develop`, salvo pedido explicito de crear una rama nueva.
6. Ejecutar validaciones.
7. Dejar comentario en la tarea con evidencia, dependencias, errores o inquietudes si aplica.
8. Cerrar la tarea.
9. Dejar al menos un commit trazable por tarea o cambio cerrado.
10. Abrir PR con evidencia si corresponde.
11. Revisar y aprobar con `MERGE OK`.
12. Hacer merge.

## Politica actual de ramas

- `develop` es la rama de trabajo diaria.
- `main` es la rama estable de integracion.
- No se crean ramas nuevas salvo pedido explicito.
- Si se pide una rama nueva de forma excepcional, debe quedar asociada a una tarea concreta.

## Documentos clave

- Vision: `docs/00-product/vision.md`
- Base tecnica: `docs/01-architecture/technical-base.md`
- Arquitectura operativa: `docs/01-architecture/operational-architecture.md`
- Motor visual: `docs/01-architecture/visual-generation-engine.md`
- Roadmap maestro flexible: `docs/02-roadmap/roadmap-master.md`
- Reglas de trabajo: `docs/03-process/working-agreement.md`
- Ciclo de tarea: `docs/03-process/task-lifecycle.md`
- Ramas y commits: `docs/03-process/branching-and-commits.md`
- Contrato operativo de agentes: `docs/03-process/agent-ops-contract.md`
- Onboarding de tooling: `docs/03-process/developer-tooling-onboarding.md`
- Secretos y accesos: `docs/03-process/secrets-and-access.md`
- Checklist agent-ready: `docs/03-process/agent-ready-task-checklist.md`
- Politica de documentacion tecnica: `docs/03-process/technical-documentation-policy.md`
- QA: `docs/05-qa/test-strategy.md`

## Baseline compartido de tooling

El repositorio versiona contrato y plantillas compartibles para trabajo con multiples desarrolladores y multiples tipos de agentes.

- Entorno local base: `.env.example`
- Dependencias Python: `requirements.txt`
- MCPs versionables: `templates/agent-tooling/mcp.servers.example.json`
- Skills por workspace: `templates/agent-tooling/skills.manifest.example.yaml`

La plantilla de MCPs ya incluye baseline para `youtrack`, `github` y `supabase`. Los secretos reales y overrides locales siguen fuera del repo.

Los secretos reales y configuraciones personales no se versionan. Cada desarrollador conecta sus propias credenciales siguiendo `docs/03-process/developer-tooling-onboarding.md`.

## Bootstrap local de Python

Flujo operativo recomendado para este repo:

1. Crear entorno virtual: `python -m venv .venv`
2. Activarlo en PowerShell: `.\.venv\Scripts\Activate.ps1`
3. Actualizar `pip`: `python -m pip install --upgrade pip`
4. Instalar dependencias: `python -m pip install -r requirements.txt`
5. Ejecutar validacion base: `python -m pytest -q`

`requirements.txt` es la unica fuente de verdad para dependencias de Python en este repo.

## Estado actual

Este repositorio hoy esta preparado como base de proyecto y como baseline operativo compartido para onboarding de developers y agentes. La implementacion tecnica de aplicacion y la CI productiva pueden crecer sobre este contrato comun.

## Cerebro agentico

`DEV-7` incorpora un modulo inicial de orquestacion agentica en `LangGraph` bajo `src/vixenbliss_creator/agentic/`.

- entrada: idea en lenguaje natural
- salida: `GraphState` final con `TechnicalSheet` validado y recomendacion tecnica de `Copilot`
- integraciones: adapter `LLM serverless` compatible con OpenAI y adapter HTTP para `ComfyUI Copilot`
- soporte local: fakes deterministas para tests y smoke

Smoke demo:

```powershell
$env:PYTHONPATH = (Resolve-Path .\src)
python -m vixenbliss_creator.agentic.runner --idea "performer glam nocturna con tono seguro y premium"
```

Detalle tecnico y contrato de variables en `docs/01-architecture/agentic-brain.md`.

## Motor visual

`DEV-8` agrega una primera capa de motor visual real en `src/vixenbliss_creator/visual_pipeline/`.

- contrato estable de request/response para generacion sobre `ComfyUI`
- rama opcional de `IP Adapter Plus` para consistencia facial
- disparo de `Impact Pack FaceDetailer` cuando la confianza facial cae por debajo del umbral configurado
- checkpoint serializable para retomar desde el ultimo nodo exitoso

El detalle tecnico y las variables nuevas viven en `docs/01-architecture/visual-generation-engine.md`.

## Runtime deployable de ComfyUI

El repo incluye una unidad deployable para `Runpod` en `infra/runpod-visual-serverless/`.

- imagen productiva basada en `Docker`
- bootstrap de `ComfyUI` con `IPAdapter Plus` e `Impact Pack`
- workflow base versionado para imagen
- scripts de arranque y healthcheck

La carpeta esta pensada para publicarse en `GitHub` y usarse como base reproducible del runtime de imagen.
