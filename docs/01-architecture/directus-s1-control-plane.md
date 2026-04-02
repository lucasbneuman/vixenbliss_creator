# Directus S1 Control Plane

## Objetivo

Definir como `Directus` opera como control plane opcional de `Sistema 1` sin absorber la logica pesada de IA ni reemplazar a `LangGraph`.

## Principios

- `Directus` es la fuente de verdad operativa de intake, estados, snapshots, approvals y artifacts cuando el equipo decide habilitarlo
- `PostgreSQL` sigue siendo la base subyacente administrada por `Directus`
- la logica de expansion, validacion y orquestacion agentica vive en Python
- el runtime del repo puede sobrevivir sin `Directus`; la integracion no se convierte en dependencia dura

## Uso actual en este repo

La integracion viva que se incorpora ahora es la capa de conexion y bootstrap:

- settings de `Directus`
- cliente HTTP autenticado para `items`
- schema manager para colecciones base de `S1`

No se adopta el flujo viejo de orquestacion remota como fuente principal de `S1`.

## Colecciones S1 previstas

- `s1_identities`
- `s1_prompt_requests`
- `s1_generation_runs`
- `s1_artifacts`
- `s1_model_assets`
- `s1_events`

## Variables requeridas

- `DIRECTUS_BASE_URL`
- `DIRECTUS_API_TOKEN`
- `DIRECTUS_TIMEOUT_SECONDS`
- `DIRECTUS_WEBHOOK_SECRET`
- `DIRECTUS_ASSETS_STORAGE`
- `S1_CONTROL_BIND_HOST`
- `S1_CONTROL_PORT`
- `S1_CONTROL_PUBLIC_BASE_URL`

## Limite deliberado

La integracion actual prepara el acceso a DB/control plane y el bootstrap de esquema, pero no sustituye ni redesena:

- `LangGraph` como orquestador
- `S1 llm`, `S1 image` y `S1 lora train` como servicios principales
- la persistencia intermedia por manifests JSON mientras la DB todavia no este completamente integrada al flujo operativo
