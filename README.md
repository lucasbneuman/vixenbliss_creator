# VixenBliss Creator

Base documental y operativa para construir `VixenBliss Creator` desde cero con un flujo pensado para dos desarrolladores y agentes como `Codex`.

## Que contiene este repositorio

- arquitectura y base tecnica del sistema
- roadmap maestro y epicas ejecutables
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

- Trabajo operativo: `YouTrack`
- Codigo, PRs y releases: `GitHub`

No duplicar el estado de tareas y bugs dentro del repo.

## Flujo recomendado por tarea

1. Seleccionar tarea en `YouTrack`.
2. Pedir plan a Codex.
3. Aprobar con `PLAN OK`.
4. Implementar sobre `staging`, salvo pedido explicito de crear una rama nueva.
5. Ejecutar validaciones.
6. Abrir PR con evidencia.
7. Revisar y aprobar con `MERGE OK`.
8. Hacer merge y cerrar tarea.

## Politica actual de ramas

- `staging` es la rama de trabajo diaria.
- `main` es la rama estable de integracion.
- No se crean ramas nuevas salvo pedido explicito.
- Si se pide una rama nueva de forma excepcional, debe quedar asociada a una tarea concreta.

## Documentos clave

- Vision: `docs/00-product/vision.md`
- Base tecnica: `docs/01-architecture/technical-base.md`
- Arquitectura operativa: `docs/01-architecture/operational-architecture.md`
- Roadmap maestro: `docs/02-roadmap/roadmap-master.md`
- Reglas de trabajo: `docs/03-process/working-agreement.md`
- Ciclo de tarea: `docs/03-process/task-lifecycle.md`
- Ramas y commits: `docs/03-process/branching-and-commits.md`
- Contrato operativo de agentes: `docs/03-process/agent-ops-contract.md`
- Onboarding de tooling: `docs/03-process/developer-tooling-onboarding.md`
- Secretos y accesos: `docs/03-process/secrets-and-access.md`
- Checklist agent-ready: `docs/03-process/agent-ready-task-checklist.md`
- QA: `docs/05-qa/test-strategy.md`

## Baseline compartido de tooling

El repositorio versiona contrato y plantillas compartibles para trabajo con multiples desarrolladores y multiples tipos de agentes.

- Entorno local base: `.env.example`
- Dependencias Python runtime: `requirements.txt`
- Dependencias Python desarrollo: `requirements-dev.txt`
- MCPs versionables: `templates/agent-tooling/mcp.servers.example.json`
- Skills por workspace: `templates/agent-tooling/skills.manifest.example.yaml`

Los secretos reales y configuraciones personales no se versionan. Cada desarrollador conecta sus propias credenciales siguiendo `docs/03-process/developer-tooling-onboarding.md`.

## Bootstrap local de Python

Flujo operativo recomendado para este repo:

1. Crear entorno virtual: `python -m venv .venv`
2. Activarlo en PowerShell: `.\.venv\Scripts\Activate.ps1`
3. Actualizar `pip`: `python -m pip install --upgrade pip`
4. Instalar dependencias de desarrollo: `python -m pip install -r requirements-dev.txt`
5. Ejecutar validacion base: `python -m pytest -q`

`pyproject.toml` se conserva para metadata y configuracion del paquete. La instalacion local de dependencias se hace desde `requirements*.txt`.

## Estado actual

Este repositorio hoy esta preparado como base de proyecto y como baseline operativo compartido para onboarding de developers y agentes. La implementacion tecnica de aplicacion y la CI productiva pueden crecer sobre este contrato comun.
