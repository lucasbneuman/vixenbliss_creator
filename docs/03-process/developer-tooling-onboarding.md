# Developer Tooling Onboarding

## Objetivo

Permitir que cualquier desarrollador configure el mismo baseline de herramientas y pueda trabajar con sus propias credenciales sin depender de contexto informal.

## Prerequisitos locales

- `Git`
- shell local
- editor compatible con el workflow del equipo
- acceso a este repositorio
- acceso personal a `GitHub` y `YouTrack`
- credenciales personales o de proyecto para los proveedores que la tarea requiera

## Orden de bootstrap

1. Clonar el repositorio.
2. Leer `AGENTS.md`.
3. Leer `docs/03-process/working-agreement.md` y `docs/03-process/task-lifecycle.md`.
4. Copiar `.env.example` a `.env` y completar solo las variables necesarias para la tarea activa.
5. Configurar MCPs locales usando `templates/agent-tooling/mcp.servers.example.json` como base.
6. Instalar o declarar las skills locales usando `templates/agent-tooling/skills.manifest.example.yaml` como referencia.
7. Validar accesos a `GitHub`, `YouTrack` y proveedores requeridos.
8. Confirmar estado `ready to work`.

## Donde vive cada cosa

### Repo versionado

- contratos operativos
- roadmap y arquitectura
- plantillas de entorno
- ejemplos de MCP
- manifiesto de skills compartidas

### Configuracion local

- `.env`
- archivos locales reales de MCP
- instalacion local de skills
- rutas locales
- tokens y secretos

## Configuracion de MCPs

- usar `templates/agent-tooling/mcp.servers.example.json` como plantilla
- reemplazar placeholders por valores locales
- no commitear archivos reales con secretos
- nombrar servidores segun proveedor y entorno cuando aplique

## Skills por workspace

- usar `templates/agent-tooling/skills.manifest.example.yaml` como baseline
- declarar skills obligatorias, opcionales y futuras
- documentar dependencias locales o variables requeridas si una skill sale del baseline minimo

## Credenciales personales

- cada developer conecta sus propias credenciales cuando el proveedor lo permita
- si una credencial es compartida a nivel proyecto, su distribucion debe ocurrir fuera del repo
- no copiar tokens de otro developer
- revocar y regenerar credenciales comprometidas antes de continuar

## Ready to work para humanos

Un developer esta listo si puede:

- leer el contexto minimo del repo
- abrir y actualizar una tarea en `YouTrack` con su acceso
- operar sobre `GitHub`
- completar `.env` sin variables ambiguas
- identificar que MCPs y skills necesita para su tarea

## Ready to work para agentes

Un agente esta listo si puede:

- identificar fuentes de verdad y limites operativos
- determinar si la tarea es agent-ready
- saber que secretos no debe pedir ni versionar
- ubicar plantillas de entorno, MCPs y skills
- dejar evidencia compatible con el workflow del repo

## Smoke checks minimos

### Generales

- `git status` funciona
- el repo contiene los documentos criticos
- `.env` existe localmente y no se versiona

### Integraciones base

- `GitHub`: acceso a repo y PRs segun rol
- `YouTrack`: lectura de tareas y campos esperados
- `MCPs`: cada servidor configurado responde a una lectura o listado simple
- `skills`: cada skill declarada puede localizarse o instalarse segun su mecanismo

## Si algo falla

- si falta documentacion, corregir el repo antes de normalizar el workaround
- si falta acceso real, pedirlo fuera del repo y dejar trazabilidad en la tarea
- si una integracion requiere pasos que no estan aqui, actualizar esta guia en el mismo cambio que introduzca esa necesidad
