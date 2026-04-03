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
- upload de archivos a `Directus Files`
- schema manager para colecciones base de `S1`
- bootstrap CLI: `python -m vixenbliss_creator.s1_control.bootstrap`
- posibilidad de registrar jobs de runtimes `S1` sobre `run_id` existentes cuando el orquestador ya conozca el correlativo en Directus
- persistencia de artifacts materializados de `S1 image` en storage persistente
- snapshot tecnico reutilizable del avatar en `s1_identities`

No se adopta el flujo viejo de orquestacion remota como fuente principal de `S1`.

## Colecciones S1 previstas

- `s1_identities`
- `s1_prompt_requests`
- `s1_generation_runs`
- `s1_artifacts`
- `s1_model_assets`
- `s1_events`

## Rol recomendado para artifacts de `S1 image`

Para el flujo `S1 image -> S1 lora train`, `Directus` debe operar como catalogo y punto de acceso persistente de artifacts tecnicos:

- `dataset_manifest`
- `dataset_package`
- evidencia de QA del dataset cuando aplique

Direccion recomendada:

- `Modal` retiene pesos, caches y staging efimero
- `Directus Files` backed por storage `S3-compatible` conserva los artifacts compartidos entre servicios
- el orquestador en `Coolify` registra en `s1_artifacts` los metadatos y paths persistentes antes de lanzar `S1 lora train`

Estado implementado en el repo:

- `S1 image` sube `base_image`, `dataset_manifest` y `dataset_package` a `Directus Files` cuando los artifacts existen en disco local
- `s1_artifacts.file` guarda el UUID del file persistido
- `s1_artifacts.uri` pasa a privilegiar el locator persistente del asset en `Directus`
- `metadata_json` conserva la trazabilidad entre path local y file persistido
- la respuesta del runtime de `S1 image` expone `metadata.directus_run_id`, `metadata.dataset_storage_mode` y `metadata.persisted_artifacts`
- el snapshot de `s1_identities` replica `dataset_storage_mode` y el resumen de `persisted_artifacts` dentro de `latest_visual_config_json`

## Snapshot tecnico canonico por avatar

`s1_identities` pasa a funcionar tambien como snapshot tecnico reutilizable del avatar para consistency downstream.

Campos relevantes:

- `reference_face_image_id`
- `latest_generation_manifest_json`
- `latest_seed_bundle_json`
- `latest_visual_config_json`
- `latest_base_model_id`
- `latest_workflow_id`
- `latest_workflow_version`
- `latest_dataset_manifest_file_id`
- `latest_dataset_package_file_id`

Objetivo operativo:

- permitir que `S1 Training` y futuros `S2 Image` resuelvan seeds, prompts, workflow, modelo base y artifacts persistidos leyendo una sola identidad
- evitar que servicios futuros dependan de reconstruir estado tecnico a partir de runs historicas o manifests locales

Esto evita acoplar el handoff de negocio al storage interno de `Modal`.

## Smoke operativa recomendada

Para validar la conexion end-to-end `S1 image -> Directus` sin depender de GPU ni de una instancia viva de `ComfyUI`, el repo incorpora una smoke reproducible:

- bootstrap de schema: `python -m vixenbliss_creator.s1_control.bootstrap`
- smoke de persistencia real: `python -m vixenbliss_creator.s1_control.live_smoke`

La smoke carga el runtime de `S1 image`, stubbea la ejecucion visual de forma determinista, ejecuta un job minimo con `identity_id` real y verifica en `Directus`:

- `s1_generation_runs`
- `s1_artifacts`
- `s1_events`
- `s1_identities`

Esta validacion confirma persistencia y trazabilidad end-to-end. No valida todavia batching con `BatchingNodes` ni bootstrap determinista de modelos con `ComfyPack`.

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
- la persistencia intermedia por manifests JSON mientras `S1 lora train` y `S2 image` todavia no consuman directamente el snapshot canonico en `Directus`
