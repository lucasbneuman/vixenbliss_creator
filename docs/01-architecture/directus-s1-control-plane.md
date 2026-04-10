# Directus S1 Control Plane

## Audiencia

- developers
- agentes que tocan `Directus` o `s1_control`

## Vigencia

- `vivo`

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
- catalogo persistible de `Content` para outputs visuales catalogables
- snapshot tecnico reutilizable del avatar en `s1_identities`

No se adopta el flujo viejo de orquestacion remota como fuente principal de `S1`.

## Colecciones S1 previstas

- `s1_identities`
- `s1_prompt_requests`
- `s1_generation_runs`
- `s1_artifacts`
- `s1_model_assets`
- `s1_model_registry`
- `content_catalog`
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
- `content_catalog` conserva el output catalogado de negocio con `generation_status`, `qa_status` y snapshot de trazabilidad
- la respuesta del runtime de `S1 image` expone `metadata.directus_run_id`, `metadata.dataset_storage_mode` y `metadata.persisted_artifacts`
- el snapshot de `s1_identities` replica `dataset_storage_mode` y el resumen de `persisted_artifacts` dentro de `latest_visual_config_json`

## Persistencia canonica de `Content`

`content_catalog` agrega la capa faltante entre ejecucion tecnica y output catalogado.

Campos persistidos:

- `content_id`
- `content_schema_version`
- `identity_id`
- `content_mode`
- `video_generation_mode`
- `generation_status`
- `qa_status`
- `job_id`
- `primary_artifact_id`
- `related_artifact_ids`
- `base_model_id`
- `model_version_used`
- `provider`
- `workflow_id`
- `prompt`
- `negative_prompt`
- `seed`
- `source_content_id`
- `source_artifact_id`
- `duration_seconds`
- `frame_count`
- `frame_rate`
- `metadata_json`
- `created_at`
- `updated_at`

Regla operativa:

- `Job` sigue siendo la fuente de verdad de la ejecucion
- `Artifact` sigue siendo la fuente de verdad del archivo
- `Content` pasa a ser la fuente de verdad del output catalogado de negocio

Estado implementado actual:

- el recorder registra `Content` cuando una corrida `s1_image` ya produjo al menos un artifact visual catalogable
- el artifact principal se resuelve con prioridad `generated_image -> base_image -> thumbnail`
- `prompt`, `negative_prompt`, `seed`, `workflow_id`, `provider` y `model_version_used` se persisten directamente en `content_catalog`
- `metadata_json` conserva el rol del artifact, el `run_id` y el resumen del origen runtime
- `video` queda preparado contractualmente en schema, aunque el repo no tenga todavia render productivo de video
- una solicitud `text_to_video` o `image_to_video` ya puede persistirse como `Content` en estado `pending`
- `image_to_video` puede registrar `source_content_id` o `source_artifact_id` para evitar ambiguedad en el handoff hacia el primer proveedor real

## Correspondencia `Content <-> Artifact`

Relaciones recomendadas:

- `content_catalog.primary_artifact_id` referencia la fila principal de `s1_artifacts`
- `content_catalog.related_artifact_ids` lista la corrida visual asociada
- `s1_artifacts` conserva locator, file id, content type y metadata tecnica
- `content_catalog` conserva estados de negocio y snapshot de trazabilidad estable

Esto evita usar `s1_artifacts` como si fuera a la vez registro tecnico y catalogo funcional.

## Relacion con persistencia SQL formal

Para cerrar `DEV-14`, el repo incorpora ademas una migracion SQL versionada de `contents`.

Decision vigente:

- `Directus/content_catalog` sigue siendo la persistencia operativa conectada al runtime
- `migrations/001_initial_relational_persistence.sql` documenta y formaliza la tabla relacional `contents`
- la tabla `contents` replica el contrato `Content` y agrega indices operativos para dashboard/API
- no se reemplaza el recorder ni se agrega sincronizacion bidireccional nueva en esta tarea

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

Chequeo operativo recomendado en DB:

- `s1_identities.technical_sheet_json` es la ficha completa del avatar
- `s1_identities.display_name`, `category`, `vertical`, `style` y `occupation_or_content_basis` exponen el resumen navegable
- `s1_identities.latest_generation_manifest_json` conserva el prompt tecnico final que consumio `S1 image`
- `s1_identities.latest_visual_config_json` resume config visual, artifacts persistidos y estado de validacion

CLI de consulta rapida:

- `python -m vixenbliss_creator.s1_control.avatar_report --latest`
- `python -m vixenbliss_creator.s1_control.avatar_report --identity-id <avatar_id>`

Ese comando devuelve una vista resumida y legible con:

- identidad y perfil comercial
- visual profile
- personality profile
- narrativa minima
- `system5_slots`
- prompt tecnico, seeds y snapshot de revision

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
