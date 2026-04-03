# Developer Tooling Onboarding

## Objetivo

Permitir que cualquier desarrollador configure el mismo baseline de herramientas y pueda trabajar con sus propias credenciales sin depender de contexto informal.

## Prerequisitos locales

- `Git`
- `Python 3.11+`
- shell local
- editor compatible con el workflow del equipo
- acceso a este repositorio
- acceso personal a `GitHub` y `YouTrack`
- credenciales personales o de proyecto para los proveedores que la tarea requiera

## Orden de bootstrap

1. Clonar el repositorio.
2. Leer `AGENTS.md`.
3. Leer `docs/03-process/working-agreement.md` y `docs/03-process/task-lifecycle.md`.
4. Crear entorno virtual local con `python -m venv .venv`.
5. Activar `.venv` en el shell local.
6. Ejecutar `python -m pip install --upgrade pip`.
7. Instalar dependencias con `python -m pip install -r requirements.txt`.
8. Copiar `.env.example` a `.env` y completar solo las variables necesarias para la tarea activa.
9. Configurar MCPs locales usando `templates/agent-tooling/mcp.servers.example.json` como base.
10. Instalar o declarar las skills locales usando `templates/agent-tooling/skills.manifest.example.yaml` como referencia.
11. Validar accesos a `GitHub`, `YouTrack` y proveedores requeridos.
12. Ejecutar `python -m pytest -q` como smoke check base.
13. Confirmar estado `ready to work`.

Para tareas del cerebro agentico (`DEV-7` o derivadas), completar tambien solo si aplica:

- `LLM_SERVERLESS_BASE_URL`
- `LLM_SERVERLESS_API_KEY`
- `LLM_SERVERLESS_MODEL`
- `COMFYUI_COPILOT_BASE_URL`
- `COMFYUI_COPILOT_API_KEY`
- `COMFYUI_COPILOT_PATH`

Si ejecutas modulos del repo fuera de `pytest`, exporta tambien `PYTHONPATH` apuntando a `src` porque este workspace usa layout `src/`:

```powershell
$env:PYTHONPATH = (Resolve-Path .\src)
```

## Bootstrap Python

### Comandos recomendados en PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pytest -q
```

### Fuente de verdad para dependencias

- `requirements.txt`: unica fuente de verdad de dependencias de Python

## Donde vive cada cosa

### Repo versionado

- contratos operativos
- roadmap y arquitectura
- plantillas de entorno
- `requirements.txt`
- ejemplos de MCP
- manifiesto de skills compartidas

### Configuracion local

- `.env`
- `.venv`
- archivos locales reales de MCP
- instalacion local de skills
- rutas locales
- tokens y secretos

## Configuracion de MCPs

- usar `templates/agent-tooling/mcp.servers.example.json` como plantilla
- reemplazar placeholders por valores locales
- no commitear archivos reales con secretos
- nombrar servidores segun proveedor y entorno cuando aplique
- para MCPs remotos, usar `url` con el endpoint documentado en vez de `command` y `args`
- baseline actual: `directus` se configura como MCP remoto por `http` usando `DIRECTUS_MCP_URL`
- baseline actual: `supabase` se configura como MCP remoto por `http` usando `SUPABASE_MCP_URL`
- baseline actual: `runpod` se configura como MCP local por `stdio` usando `npx -y @runpod/mcp-server@latest`
- `runpod` requiere `RUNPOD_API_KEY` en el entorno local y sirve para inspeccionar endpoints, workers, requests y despliegues sin pegar curls manuales
- mantener el archivo real de MCP fuera del repo y derivarlo desde la plantilla compartida

### Baseline sugerido para `Directus MCP`

Usar este bloque en el archivo local derivado desde la plantilla:

```json
{
  "mcpServers": {
    "directus": {
      "transport": "http",
      "url": "${DIRECTUS_MCP_URL}",
      "headers": {
        "Authorization": "Bearer ${DIRECTUS_API_TOKEN}"
      }
    }
  }
}
```

Notas operativas:

- definir `DIRECTUS_MCP_URL` como la URL base de `Directus` terminada en `/mcp`
- reutilizar `DIRECTUS_API_TOKEN` si el mismo token tiene permisos suficientes para la superficie MCP
- si el entorno de `Directus` separa token operativo y token MCP, documentarlo fuera del repo y no hardcodearlo en la plantilla
- usar este MCP cuando la tarea requiera inspeccionar o administrar colecciones, files, schema o configuracion de `S1` sin salir del flujo del agente

### Baseline sugerido para `Runpod MCP`

Usar este bloque en el archivo local derivado desde la plantilla:

```json
{
  "mcpServers": {
    "runpod": {
      "transport": "stdio",
      "command": "npx",
      "args": ["-y", "@runpod/mcp-server@latest"],
      "env": {
        "RUNPOD_API_KEY": "${RUNPOD_API_KEY}"
      }
    }
  }
}
```

Notas operativas:

- reemplazar `${RUNPOD_API_KEY}` por resolucion desde entorno local, no por un token hardcodeado
- si `npx` no esta disponible, instalar `Node.js` localmente antes de declarar este MCP
- en Windows, si PowerShell bloquea `npx.ps1`, usar `C:\\Program Files\\nodejs\\npx.cmd` como `command`
- usar este MCP cuando la tarea requiera depurar `Runpod Serverless`, validar workers o inspeccionar releases sin salir del flujo del agente

## Skills por workspace

- usar `templates/agent-tooling/skills.manifest.example.yaml` como baseline
- declarar skills obligatorias, opcionales y futuras
- documentar dependencias locales o variables requeridas si una skill sale del baseline minimo

### Skill compartida sugerida para `Runpod CLI`

Para tareas que requieran operar la CLI oficial de `Runpod`, instalar tambien la skill `runpodctl` desde `https://github.com/runpod/skills`.

Comando recomendado en Windows:

```powershell
& 'C:\Program Files\nodejs\npx.cmd' skills add https://github.com/runpod/skills --skill runpodctl --agent codex --global --yes
```

Notas operativas:

- reiniciar `Codex` despues de instalar la skill para que quede disponible en nuevas sesiones
- la instalacion global actual de la CLI `skills` para `Codex` copia la skill en `~/.agents/skills/runpodctl`
- usar esta skill como apoyo para comandos `runpodctl` sobre pods, serverless, templates, network volumes, registry, billing y transferencias
- `runpodctl` sigue requiriendo autenticacion propia de `Runpod`; validar `RUNPOD_API_KEY` o el login que corresponda fuera del repo
- la version upstream instalada hoy declara `compatibility: Linux, macOS` y `allowed-tools: Bash(runpodctl:*)`; en Windows puede servir como referencia documental, pero para operaciones nativas del agente conviene priorizar el `Runpod MCP` ya documentado en esta guia

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
- `.venv` existe localmente y no se versiona
- `.env` existe localmente y no se versiona
- `python -m pytest -q` pasa dentro del entorno virtual

### Integraciones base

- `GitHub`: acceso a repo y PRs segun rol
- `YouTrack`: lectura de tareas y campos esperados
- `MCPs`: cada servidor configurado responde a una lectura o listado simple
- `skills`: cada skill declarada puede localizarse o instalarse segun su mecanismo

### Smoke check sugerido para `Supabase MCP`

- confirmar que `SUPABASE_MCP_URL` apunta al endpoint `/mcp` esperado
- validar que el cliente MCP pueda conectarse y listar herramientas o recursos
- si el endpoint requiere autenticacion adicional o whitelist de red, resolverlo fuera del repo y dejar evidencia en la tarea

### Smoke check sugerido para `Directus MCP`

- confirmar que `DIRECTUS_MCP_URL` apunta al endpoint `/mcp` de la instancia activa
- validar que el token usado por `Authorization: Bearer ...` tenga permisos sobre la superficie que se quiere administrar
- si el MCP responde pero las operaciones de files o schema fallan, revisar la configuracion interna de `Directus` antes de culpar al cliente MCP

## Si algo falla

- si falta documentacion, corregir el repo antes de normalizar el workaround
- si falta acceso real, pedirlo fuera del repo y dejar trazabilidad en la tarea
- si una integracion requiere pasos que no estan aqui, actualizar esta guia en el mismo cambio que introduzca esa necesidad
