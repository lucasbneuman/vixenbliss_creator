# Secrets and Access

## Objetivo

Definir el contrato minimo de secretos, accesos y ownership para que el equipo comparta tooling sin compartir credenciales en el repositorio.

## Reglas generales

- nunca versionar secretos reales
- usar `.env.example` como contrato comun
- preferir credenciales personales cuando el proveedor lo permita
- distinguir credenciales de persona, de proyecto y de despliegue
- toda credencial debe tener owner claro y via de revocacion conocida

## Convencion de naming

- variables locales y de CI en mayusculas con `_`
- prefijos por proveedor cuando aplique: `SUPABASE_`, `AWS_`, `RUNPOD_`, `MODAL_`, `LANGFUSE_`
- endpoints y buckets con nombres explicitos
- defaults no sensibles permitidos en `.env.example`
- secretos reales solo en `.env`, secret manager o configuracion del proveedor

## Tipos de credenciales

### Personales

Usadas por un developer especifico para operar herramientas del equipo.

Ejemplos:

- `GITHUB_TOKEN`
- `YOUTRACK_API_TOKEN`
- tokens personales de `Modal` o `Runpod`

### De proyecto

Usadas por el sistema o por un entorno compartido.

Ejemplos:

- `SUPABASE_SERVICE_ROLE_KEY`
- buckets compartidos
- claves de `Langfuse`

### De despliegue

Usadas por CI, hosting o entornos operativos.

Ejemplos:

- secretos en `GitHub Actions`
- credenciales de `Coolify`
- tokens de runtime en ambientes cloud

## Matriz minima por proveedor

| Proveedor | Variables base | Tipo de credencial | Owner inicial | Donde vive |
| --- | --- | --- | --- | --- |
| `GitHub` | `GITHUB_TOKEN` | personal o CI | developer / admin | local o CI |
| `YouTrack` | `YOUTRACK_BASE_URL`, `YOUTRACK_API_TOKEN` | personal | developer | local |
| `Supabase` | `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_DB_URL` | proyecto | backend / admin | local o secret manager |
| `Supabase MCP` | `SUPABASE_MCP_URL` | endpoint compartido no sensible | backend / admin | repo y local |
| `Supabase Storage` | buckets `SUPABASE_STORAGE_BUCKET_*` | proyecto | backend / admin | local o CI |
| `S3-compatible` | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `S3_BUCKET_*` | proyecto o despliegue | infra | local o secret manager |
| `Modal` | `MODAL_TOKEN_ID`, `MODAL_TOKEN_SECRET` | personal o proyecto | ML / infra | local o secret manager |
| `Runpod` | `RUNPOD_API_KEY`, `RUNPOD_ENDPOINT_*` | personal o proyecto | ML / infra | local or secret manager |
| `ComfyUI` | `COMFYUI_BASE_URL`, `COMFYUI_WORKFLOW_*` | endpoint + ids de proyecto | pipeline visual | local o despliegue |
| `LLM Serverless` | `LLM_SERVERLESS_BASE_URL`, `LLM_SERVERLESS_API_KEY`, `LLM_SERVERLESS_MODEL` | personal o proyecto | LLM / platform | local o secret manager |
| `ComfyUI Copilot` | `COMFYUI_COPILOT_BASE_URL`, `COMFYUI_COPILOT_API_KEY`, `COMFYUI_COPILOT_PATH` | endpoint + token | pipeline visual | local o despliegue |
| `FluxSchnell` | `FLUXSCHNELL_ENDPOINT`, `LORA_TRAINER_PROVIDER` | proyecto | ML | local o despliegue |
| `Langfuse` | `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` | proyecto | observabilidad | local o secret manager |
| `Llama.cpp` | `LLAMA_CPP_BASE_URL` | endpoint local o compartido | platform | local o despliegue |

## Politica de rotacion

- rotar secretos compartidos ante sospecha de exposicion
- rotar accesos personales cuando un developer deja de participar
- actualizar `.env.example` si cambia el contrato, no si cambia el valor
- documentar cambios de ownership en la tarea o ADR si impactan el proceso

## Politica de revocacion

- la revocacion la ejecuta el owner de la credencial o un admin del proveedor
- si una credencial fue expuesta, invalidarla antes de seguir operando
- no usar el repo para distribuir secretos nuevos

## Diferencia entre repo, local y CI

### Repo

- contrato de variables
- ejemplos y placeholders
- ownership y reglas

### Local

- valores reales del developer
- configuracion de MCPs
- rutas locales y overrides

### CI y despliegue

- secretos de automatizacion
- variables de entorno del runtime
- credenciales no interactivas

## Criterio de suficiencia

La capa de secretos y accesos esta suficientemente documentada si un developer puede:

- saber que variables necesita
- distinguir cuales son personales y cuales compartidas
- saber donde obtenerlas
- saber que nunca debe commitear
- detectar cuando una falta de acceso es operativa y no tecnica
