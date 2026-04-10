# Roadmap Maestro MVP Reforzado - VixenBliss Creator

## Audiencia

- developers
- agentes
- stakeholders tecnicos

## Vigencia

- `transicional`

## Proposito

Este roadmap maestro consolida el brief ejecutivo, los contratos tecnicos minimos y la direccion general del MVP reforzado de VixenBliss Creator.
Funciona como vision flexible y contexto tecnico, no como orden rigido de ejecucion ni como reflejo automatico del estado implementado.

Por tamano y mantenibilidad, el detalle operativo y el orden vivo de ejecucion no se gobiernan desde archivos de epica dentro del repo.
Ese movimiento vive en `YouTrack`, mientras este documento conserva contexto tecnico y estrategico reusable.

## Regla de lectura

- usar este documento para entender direccion y alcance futuro
- usar `docs/01-architecture/technical-base.md` para entender el estado tecnico vigente
- no asumir que una fase descrita aqui ya esta implementada si no existe respaldo en `src/`, `infra/` o `tests/`

## BRIEF

### 1. Que es VixenBliss Creator

VixenBliss Creator es una infraestructura industrial para crear identidades digitales sinteticas persistentes y producir contenido NSFW automatizado con trazabilidad completa. No es solo un generador de imagenes: es una arquitectura modular para operar identidades, datasets, modelos, prompts, outputs y metadatos reutilizables.

La arquitectura global contempla cinco sistemas:

1. Sistema 1 - Generacion de Identidades Digitales Sinteticas
2. Sistema 2 - Produccion Automatizada de Contenido
3. Sistema 3 - Distribucion Automatizada
4. Sistema 4 - Monetizacion en Capas
5. Sistema 5 - Engagement y Conversational AI

Este roadmap cubre el MVP reforzado de los Sistemas 1 y 2. No implementa aun los Sistemas 3, 4 y 5, pero deja sus contratos tecnicos minimos preparados en datos, APIs, estados, artefactos y arquitectura.

### 2. Problema que resuelve este roadmap

El roadmap anterior absorbia gran parte de la vision tecnica, pero varias tareas seguian demasiado generales para ejecutarse sin reinterpretacion. Este documento convierte la base tecnica en contexto operativo reusable, con:

- resultado esperado verificable
- implementacion paso a paso
- decisiones tecnicas por defecto
- validaciones fail-fast
- artefactos tecnicos concretos
- criterio de done
- evidencia minima

### 3. Objetivo del MVP reforzado

El MVP reforzado debe permitir:

1. Crear una identidad digital persistente con vertical, personalidad, narrativa, perfil visual, limites operacionales y ficha tecnica estructurada.
2. Generar y almacenar imagenes base de identidad con trazabilidad.
3. Preparar un dataset balanceado con y sin ropa, apto para entrenamiento.
4. Registrar el modelo base y entrenar o integrar un LoRA por identidad con metadata versionada.
5. Generar contenido de imagen en volumen usando un motor visual modular sobre `ComfyUI`.
6. Dejar preparado el contrato tecnico para generar video corto mediante interfaz desacoplada `text-to-video` o `image-to-video`.
7. Almacenar outputs, prompts, seeds, jobs, artefactos y versiones de modelo con trazabilidad completa.
8. Exponer el sistema mediante API interna, workers y dashboard operativo minimo.
9. Incorporar observabilidad, timeouts, reintentos y validaciones fail-fast.
10. Dejar preparados los puntos de entrada para el futuro Sistema 5 sin implementarlo.

### 3.1 Mapa operativo entre S1 y S2

- `S1` incluye generacion de imagenes de identidad para dataset y entrenamiento LoRA.
- `S2` incluye generacion de contenido y generacion de video.
- a nivel tecnico se recomienda mantener runtimes separados para `S1 image`, `S2 image`, `lora training` y `video`, aunque `training` pertenezca al negocio de `S1` y `video` al de `S2`
- `S1` y `S2` deben compartir la misma familia `Flux` para preservar compatibilidad entre dataset, entrenamiento e inferencia con LoRA
- en `DEV-8`, el runtime a cerrar es `S1 image`; `S1 train` queda como runtime futuro separado

### 4. Principios tecnicos obligatorios

- `Modularidad`
- `Reemplazabilidad`
- `Fail-fast`
- `Automatizacion por defecto`
- `Data-driven`
- `Trazabilidad total`

### 5. Alcance del MVP reforzado

#### Dentro del alcance

- Modelo de datos de identidades, contenidos, jobs, artefactos, modelos y estados.
- Persistencia en `Supabase/Postgres`.
- Storage en `Supabase Storage` o `S3-compatible`.
- Backend Python containerizado con `Docker`.
- Servicios, workers y ejecucion asincrona minima.
- Integracion con GPU externa mediante `Modal` o `Runpod`.
- Preparacion de workflows sobre `ComfyUI`.
- Preparacion de entrenamiento LoRA automatizable compatible con `FluxSchnell`.
- Generacion de imagenes base de identidad.
- Preparacion de dataset balanceado para entrenamiento.
- Registro del catalogo de modelos base y versiones LoRA.
- Generacion masiva de imagenes con soporte de metadata extensible a video.
- Integracion tecnica inicial de `IP-Adapter` y `ControlNet`.
- Preparacion contractual para `Wan2.2`, `AnimateDiff` o `SVD`.
- API interna operativa para identidades, jobs, artefactos, generacion y metricas.
- Dashboard interno simple.
- Observabilidad con `OpenTelemetry` y readiness para `Langfuse`.
- Pruebas end-to-end del flujo principal.
- Preparacion de slots y contratos internos para futura orquestacion con Sistema 5.

#### Fuera del alcance

- Distribucion automatica en redes sociales o canales de pago.
- Monetizacion, facturacion o pricing.
- Chatbot conversacional operativo.
- Memoria de usuario, WebSocket de chat o UX conversacional final.
- Plataforma SaaS multi-tenant o white-label.
- Escalado comercial avanzado con multiples clientes.

#### Direccion futura ya decidida para `EPIC-3`

- el front debera interactuar con el backend mediante un chatbot orquestado con `LangGraph`
- ese chatbot podra disparar operaciones de `S1` y `S2`
- la comunicacion en tiempo real entre orquestador, serverless y front debera apoyarse en `WebSockets`
- esta direccion queda documentada ahora como decision de arquitectura futura, pero no se vuelve requisito de implementacion inmediata del MVP actual

### 6. Stack tecnico base

- `Python`
- `Docker`
- `Supabase/Postgres`
- `Supabase Storage` o `S3-compatible`
- `ComfyUI`
- `FluxSchnell`
- variante `Flux` especializada o cuantizada para inferencia NSFW compatible con el modelo base canonico
- `IP-Adapter`
- `ControlNet`
- `Wan2.2`, `AnimateDiff` o `SVD`
- `Modal` o `Runpod`
- `OpenTelemetry`
- `Langfuse` como integracion preparada
- `LangGraph` como opcion de evolucion arquitectonica, no como dependencia obligatoria del MVP
- `Llama.cpp` como dependencia futura
- `Coolify`

## Interfaces y contratos minimos

### Contrato `Identity`

- `id`
- `alias`
- `status`
- `vertical`
- `personality_profile`
- `voice_tone`
- `base_narrative`
- `visual_profile`
- `operational_limits`
- `allowed_content_modes`
- `base_image_urls`
- `reference_face_image_url`
- `dataset_storage_path`
- `dataset_status`
- `lora_model_path`
- `lora_version`
- `base_model_id`
- `technical_sheet_json`
- `pipeline_state`
- `created_at`
- `updated_at`

### Contrato `Content`

- `id`
- `identity_id`
- `content_type`
- `media_modality`
- `hook_variant`
- `prompt_used`
- `negative_prompt_used`
- `seed`
- `model_version_used`
- `workflow_id`
- `provider`
- `storage_url`
- `thumbnail_url`
- `generation_status`
- `qa_status`
- `job_id`
- `duration_seconds` opcional para video
- `frame_count` opcional para video
- `frame_rate` opcional para video
- `created_at`

### Contrato `ModelRegistry`

- `id`
- `model_family`
- `model_role`
- `provider`
- `version_name`
- `display_name`
- `base_model_id`
- `storage_path`
- `quantization`
- `compatibility_notes`
- `is_active`
- `created_at`

### Contrato `Job`

- `id`
- `job_type`
- `identity_id`
- `requested_by`
- `payload_json`
- `status`
- `attempt_count`
- `timeout_seconds`
- `started_at`
- `finished_at`
- `error_code`
- `error_message`

### Contrato `Artifact`

- `id`
- `identity_id`
- `artifact_type`
- `artifact_version`
- `source_job_id`
- `storage_path`
- `checksum`
- `metadata_json`
- `created_at`

### Operaciones internas minimas

- `prepare_dataset(identity_id, dataset_rules, source_artifacts)`
- `train_lora(identity_id, dataset_artifact_id, base_model_id, provider_config)`
- `generate_identity_images(identity_id, prompt_payload, workflow_id, generation_options)`
- `generate_content_images(identity_id, prompt_payload, workflow_id, lora_version, generation_options)`
- `generate_video(identity_id, prompt_payload, workflow_id, generation_options)`

### Metadata minima que siempre debe persistirse cuando aplique

- `prompt`
- `negative_prompt`
- `seed`
- `workflow_id`
- `provider`
- `model_version`
- `storage_path`
- `checksum`
- `job_id`
- `qa_status`
- `created_at`
- `updated_at` cuando exista versionado o cambios de estado

### Estados minimos de pipeline

- `draft`
- `identity_created`
- `base_images_generated`
- `base_images_registered`
- `dataset_ready`
- `lora_training_pending`
- `lora_training_running`
- `lora_trained`
- `lora_validated`
- `content_generation_pending`
- `content_generated`
- `video_ready_for_future_integration`
- `failed`

## Variables de entorno esperadas

- `APP_ENV`
- `LOG_LEVEL`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_DB_URL`
- `SUPABASE_STORAGE_BUCKET_IDENTITIES`
- `SUPABASE_STORAGE_BUCKET_CONTENT`
- `SUPABASE_STORAGE_BUCKET_MODELS`
- `SUPABASE_STORAGE_BUCKET_DATASETS`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`
- `S3_BUCKET_IDENTITIES`
- `S3_BUCKET_CONTENT`
- `S3_BUCKET_MODELS`
- `S3_BUCKET_DATASETS`
- `MODAL_TOKEN_ID`
- `MODAL_TOKEN_SECRET`
- `RUNPOD_API_KEY`
- `RUNPOD_ENDPOINT_IMAGE_IDENTITY`
- `RUNPOD_ENDPOINT_IMAGE_CONTENT`
- `RUNPOD_ENDPOINT_IMAGE_GEN`
- `RUNPOD_ENDPOINT_LORA_TRAIN`
- `RUNPOD_ENDPOINT_VIDEO_GEN`
- `COMFYUI_BASE_URL`
- `COMFYUI_WORKFLOW_IMAGE_ID`
- `COMFYUI_WORKFLOW_IDENTITY_ID`
- `COMFYUI_WORKFLOW_IDENTITY_VERSION`
- `COMFYUI_WORKFLOW_CONTENT_ID`
- `COMFYUI_WORKFLOW_CONTENT_VERSION`
- `COMFYUI_WORKFLOW_VIDEO_ID`
- `COMFYUI_WORKFLOW_VIDEO_VERSION`
- `BASE_IMAGE_MODEL_ID`
- `BASE_VIDEO_MODEL_ID`
- `LORA_TRAINER_PROVIDER`
- `FLUXSCHNELL_ENDPOINT`
- `OTEL_EXPORTER_OTLP_ENDPOINT`
- `OTEL_SERVICE_NAME`
- `LANGFUSE_PUBLIC_KEY`
- `LANGFUSE_SECRET_KEY`
- `LLAMA_CPP_BASE_URL`
- `DEFAULT_JOB_TIMEOUT_SECONDS`
- `DEFAULT_JOB_MAX_RETRIES`

## Convencion operativa transversal para todas las tareas

Toda tarea del roadmap debe poder traducirse o actualizarse en `YouTrack` sin perder contexto. Toda tarea debe dejar explicito:

- que estado consume
- que estado produce
- que registros persiste
- que falla bloquea la ejecucion
- que evidencia minima deja para la tarea siguiente

Toda tarea que dispare ejecucion o cree un output debe registrar, segun corresponda, al menos uno de estos objetos:

- `jobs`
- `artifacts`
- `model_registry`
- `contents`

Toda tarea que use ejecucion asincrona debe declarar:

- timeout por defecto
- maximo de reintentos
- error persistido
- criterio de aborto

## Regla de redaccion operativa

Cada tarea que se derive desde este contexto hacia `YouTrack` deberia conservar, como minimo, el siguiente formato:

- `Objetivo`
- `Resultado esperado`
- `Implementacion paso a paso`
- `Decisiones tecnicas por defecto`
- `Entradas`
- `Salidas`
- `Dependencias`
- `Herramientas y servicios a usar`
- `Credenciales o accesos requeridos`
- `Validaciones fail-fast`
- `Artefactos tecnicos a producir`
- `Criterio de done`
- `Evidencia minima`
- `Siguiente tarea desbloqueada`
- `Responsable sugerido`

## Relacion con YouTrack

- `YouTrack` define backlog, prioridad, alcance y orden real de ejecucion
- este roadmap maestro preserva vision, contratos minimos y criterios tecnicos de referencia
- si el proyecto cambia de direccion, primero se actualiza `YouTrack` y luego se ajusta este documento si el aprendizaje amerita persistirse

## Rol operativo del roadmap

### 1. Como usar este documento junto con YouTrack

- El `BRIEF` de YouTrack debe representar el contenido ejecutivo de este documento.
- Cada agrupacion grande de trabajo debe convertirse en una `Epica` real si hace falta.
- Cada tarea concreta debe existir y evolucionar en `YouTrack`.
- Si una tarea cambia de alcance, orden o prioridad, `YouTrack` prevalece y el roadmap se actualiza despues para reflejar el aprendizaje.
- Si una tarea requiere implementacion extensa, se permiten subtareas, pero sin perder el contexto tecnico como referencia.

### 2. Que tareas no puede ejecutar Codex por si solo

- provision de credenciales no presentes
- configuraciones manuales en `Supabase`, `S3`, `Modal`, `Runpod`, `ComfyUI` o `Coolify`
- aprobaciones de gasto o infraestructura
- revision visual humana de calidad
- validacion humana de readiness operativa

### 3. Validaciones humanas obligatorias

- Confirmar que el esquema de datos final coincide con los contratos del roadmap.
- Validar que el dataset preparado es razonable para entrenamiento.
- Validar visualmente la consistencia del LoRA entrenado.
- Revisar una muestra de contenido generado antes de dar por cerrado el MVP.
- Confirmar que el entorno desplegado es accesible y seguro para uso interno.

### 4. Convencion de artefactos y persistencia

Todo artefacto relevante debe registrar:

- nombre del artefacto
- identidad asociada
- job de origen
- ubicacion exacta en storage
- version o revision
- checksum o referencia de integridad si aplica
- estado de pipeline que habilita
- siguiente tarea que lo consume

### 5. Politica de errores y fail-fast

- Si falta una variable critica, el proceso debe fallar antes de ejecutar jobs.
- Si falta un modelo base, LoRA, workflow o dataset requerido, no debe lanzarse generacion ni entrenamiento.
- `S2` no debe consumir un `LoRA` que no este validado explicitamente.
- `lora_training` no debe arrancar si el dataset no esta en estado `ready`.
- Todo error relevante debe quedar persistido en job, log o traza correlacionable.
- Los reintentos deben ser explicitos y limitados, nunca silenciosos.
- Toda tarea debe declarar que falla bloquea el paso siguiente.

### 6. Criterio de calidad documental

Cada tarea de este roadmap debe conservar:

- objetivo
- resultado esperado
- implementacion paso a paso
- decisiones tecnicas por defecto
- entradas
- salidas
- dependencias
- herramientas
- credenciales o accesos
- validaciones fail-fast
- artefactos tecnicos a producir
- criterio de done
- evidencia minima
- responsable sugerido

### 7. Criterio de finalizacion del roadmap maestro

Este roadmap se considera cumplido cuando, como minimo:

- una identidad puede crearse y persistirse con ficha tecnica estructurada
- sus imagenes base pueden generarse y registrarse
- su dataset puede prepararse y validarse
- el modelo base utilizado queda catalogado
- su LoRA puede entrenarse, almacenarse y versionarse
- el LoRA puede validarse manualmente
- se puede generar un lote de imagenes con metadata completa
- el contenido queda catalogado y accesible por API y dashboard
- existen jobs, artefactos y trazas suficientes para diagnosticar fallas
- el sistema esta containerizado y desplegable
- la interfaz tecnica de video esta preparada sin volverlo requisito de cierre del MVP
- la preparacion para Sistema 5 queda documentada en contratos y slots sin implementarlo aun
