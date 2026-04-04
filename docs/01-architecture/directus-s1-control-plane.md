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
- upload de imagenes a `Directus Files`
- schema manager para colecciones base de `S1`
- bootstrap CLI: `python -m vixenbliss_creator.s1_control.bootstrap`
- posibilidad de registrar jobs de runtimes `S1` sobre `run_id` existentes cuando el orquestador ya conozca el correlativo en Directus
- persistencia mixta de artifacts materializados de `S1 image` en filas de control y storage persistente solo para imagenes
- snapshot tecnico reutilizable del avatar en `s1_identities`

No se adopta el flujo viejo de orquestacion remota como fuente principal de `S1`.

## Colecciones S1 previstas

- `s1_identities`
- `s1_prompt_requests`
- `s1_generation_runs`
- `s1_artifacts`
- `s1_model_assets`
- `s1_model_registry`
- `s1_events`

## Rol recomendado para artifacts de `S1 image`

Para el flujo `S1 image -> S1 lora train`, `Directus` debe operar como catalogo y punto de acceso persistente de artifacts tecnicos, pero `Directus Files` queda reservado para binarios visuales:

- `base_image`
- futuras imagenes de entrenamiento derivadas
- evidencia de QA visual del dataset cuando aplique

Direccion recomendada:

- `Modal` retiene pesos, caches y staging efimero
- `Directus Files` backed por storage `S3-compatible` conserva solo imagenes y binarios visuales
- `s1_generation_runs.result_json`, `s1_artifacts.metadata_json` y `s1_identities` conservan `dataset_manifest`, `dataset_package_path`, `seed_bundle` y metadata tecnica asociada al personaje
- el orquestador en `Coolify` registra en `s1_artifacts` los metadatos y paths persistentes antes de lanzar `S1 lora train`

Estado implementado en el repo:

- `S1 image` sube a `Directus Files` solamente artifacts de imagen como `base_image`
- `dataset_manifest` y `dataset_package` quedan registrados como filas en `s1_artifacts`, con `file=null` y `uri`/`metadata_json` como fuente de verdad tecnica
- `s1_artifacts.file` guarda el UUID del file persistido solo cuando el artifact vive en storage visual
- `s1_artifacts.uri` conserva el locator final del artifact, ya sea asset en `Directus` o path/uri tecnico del handoff
- `metadata_json` conserva la trazabilidad entre `identity_id`, `character_id`, `seed_bundle`, path local y modo de persistencia
- la respuesta del runtime de `S1 image` expone `metadata.directus_run_id`, `metadata.dataset_storage_mode` y `metadata.persisted_artifacts`
- el snapshot de `s1_identities` replica `dataset_storage_mode` y el resumen de `persisted_artifacts` dentro de `latest_visual_config_json`

## Persistencia canonica de identidad creada

`s1_identities` ahora tambien puede guardar la entidad durable `Identity` creada al cerrar el generador estructurado.

Campos canonicos persistidos:

- `identity_schema_version`
- `alias`
- `status`
- `pipeline_state`
- `allowed_content_modes`
- `reference_face_image_url`
- `base_image_urls`
- `dataset_storage_path`
- `dataset_status`
- `base_model_id`
- `lora_model_path`
- `lora_version`
- `technical_sheet_json`
- `created_at`
- `updated_at`

Uso recomendado:

- crear la `Identity` canonica desde `LangGraph` usando `src/vixenbliss_creator/s1_control/identity_service.py`
- persistirla con `src/vixenbliss_creator/s1_control/identity_store.py`
- consultar por `avatar_id = Identity.id` para rehidratar la entidad completa sin reconstrucciones manuales

Estado inicial esperado:

- `pipeline_state = identity_created`
- `latest_base_model_id` se inicializa con `base_model_id` para dejar listo el handoff hacia jobs y artifacts futuros

## Catalogo canonico de modelos base

`s1_model_registry` conserva el catalogo versionado de `ModelRegistry` para que las identidades no dependan de strings sueltos sin control de compatibilidad.

Estado inicial seed:

- `flux-schnell-v1` como modelo base de imagen activo
- `future-video-placeholder-v1` como placeholder de video activo

Compatibilidades declaradas:

- `flux-schnell-v1`: `ComfyUI`, `LoRA`, `IP-Adapter`, `ControlNet`
- placeholder de video: contrato preparado para `S2 video` sin binario persistido todavia

## Snapshot tecnico canonico por avatar

`s1_identities` pasa a funcionar tambien como snapshot tecnico reutilizable del avatar para consistency downstream.

Campos relevantes:

- `reference_face_image_id`
- `latest_base_image_file_id`
- `latest_generation_manifest_json`
- `latest_dataset_manifest_json`
- `latest_seed_bundle_json`
- `latest_visual_config_json`
- `latest_base_model_id`
- `latest_workflow_id`
- `latest_workflow_version`
- `latest_dataset_package_uri`
- `latest_dataset_manifest_file_id`
- `latest_dataset_package_file_id`

Objetivo operativo:

- permitir que `S1 Training` y futuros `S2 Image` resuelvan `character_id`, seeds, prompts, workflow, modelo base y artifacts persistidos leyendo una sola identidad
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

Check complementario para readiness previo a `S1 Training`:

- `python -m vixenbliss_creator.s1_control.readiness_check --idea "Quiero una modelo morocha para contenido NSFW, el resto completalo de manera automatica"`

Ese check:

- corre `LangGraph` con LLM real cuando hay credencial disponible
- genera el `generation_manifest` via `S1 llm`
- prioriza el worker GPU real de `S1 Image` en `Modal` cuando existen `MODAL_TOKEN_ID` y `MODAL_TOKEN_SECRET`
- solo usa fallback local de `S1 image` si la corrida real de `Modal` no esta disponible
- descarga el `base_image` desde `Directus` con autenticacion
- valida `dataset_manifest` y `dataset_package` desde la fuente real registrada en `s1_artifacts`
- usa un PNG fixture tecnico valido para wiring, pero no lo considera evidencia suficiente de calidad entrenable

Limpieza operativa recomendada entre tandas de prueba:

- `python -m vixenbliss_creator.s1_control.cleanup_directus`

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
- la necesidad de QA humana sobre imagenes reales antes de habilitar `S1 Training`
