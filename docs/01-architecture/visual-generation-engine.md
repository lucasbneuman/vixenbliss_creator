# Visual Generation Engine

## Objetivo

Definir la primera capa ejecutable del motor visual sobre `ComfyUI` para generacion de imagen con consistencia facial y correccion regional trazable, separada por etapa operativa.

## Contrato operativo

El motor visual expone un request/response estable bajo `src/vixenbliss_creator/visual_pipeline/`.

## Mapa S1 y S2

- `S1` cubre generacion de imagenes de identidad para dataset y entrenamiento LoRA.
- `S1 llm` actua como preparador de manifiestos de generacion para `LangGraph`; no reemplaza la orquestacion.
- el mismo runtime puede exponer un endpoint OpenAI-compatible en `/v1/chat/completions` para que `LangGraph` consuma el modelo sin cambiar su adapter
- `S2` cubre generacion de contenido y generacion de video.
- la separacion por runtime sigue siendo recomendada aunque `training` pertenezca al negocio de `S1` y `video` pertenezca al negocio de `S2`
- `S1` y `S2` deben permanecer en la misma familia `Flux` para preservar compatibilidad del LoRA
- dentro de `DEV-8`, el runtime objetivo es especificamente `S1 image`

### Request

- `workflow_id` y `workflow_version` identifican el workflow operativo.
- `model_family` fija la familia compatible del runtime; la implementacion actual solo admite `flux`.
- `runtime_stage` distingue `identity_image`, `content_image` y `video`.
- `base_model_id`, `prompt`, `negative_prompt`, `seed`, `width` y `height` describen la corrida reproducible.
- `reference_face_image_url` habilita la rama opcional de `IP Adapter Plus`.
- `lora_version` y `lora_validated` permiten habilitar inferencia de contenido solo sobre LoRAs validados.
- `ip_adapter` registra `model_name`, `weight` y `node_id` opcional.
- `face_detailer` registra `confidence_threshold`, `inpaint_strength` y nodos opcionales del detector y del `FaceDetailer`.
- `resume_policy` y `resume_checkpoint` definen si la corrida debe retomarse desde el ultimo nodo exitoso.

### Response

- `artifacts` devuelve los archivos finales recuperables.
- `intermediate_state` serializa el checkpoint util para resume.
- `model_family` y `runtime_stage` dejan persistido que runtime resolvio la corrida.
- `face_detection_confidence` registra la confianza facial usada para decidir si hay correccion regional.
- `ip_adapter_used` y `regional_inpaint_triggered` dejan trazabilidad explicita del camino ejecutado.
- `error_code` y `error_message` normalizan fallos del pipeline visual.

## Fail-fast canonico

- si `IP-Adapter` se activa sin `reference_face_image_url`, la request es invalida
- si `runtime_stage=identity_image`, la request no puede consumir `lora_version`
- si `runtime_stage=content_image` con `lora_version`, la request exige `lora_validated=true`
- si `model_family` no pertenece a `flux`, la request se rechaza
- si la referencia facial no puede resolverse, el pipeline falla con `REFERENCE_IMAGE_NOT_FOUND`
- si el detector facial no devuelve una confianza util, el pipeline falla con `FACE_CONFIDENCE_UNAVAILABLE`
- si el checkpoint no contiene artefactos suficientes para retomar, la request se rechaza con `RESUME_STATE_INCOMPLETE`
- si `ComfyUI` no devuelve artefactos o falla la ejecucion HTTP, el error se normaliza como `COMFYUI_EXECUTION_FAILED`

## Politica de resume

- el checkpoint minimo de `base_render` debe incluir `workflow_id`, `workflow_version`, `base_model_id`, `seed`, `provider_job_id` y un artefacto `base_image`
- el checkpoint completado debe incluir al menos un artefacto `final_image`
- la implementacion actual serializa metadata y rutas de artefactos intermedios; no almacena tensores crudos en el repo

## Modos de ejecucion

El contrato del motor visual ahora prioriza proveedores neutrales y portables por etapa. En el estado operativo actual, la implementacion activa usa `Coolify` como host del orquestador HTTP y `Modal` como worker GPU.

### `ComfyUI` HTTP directo

Se usa cuando el backend habla contra `COMFYUI_BASE_URL` y el runtime expone `ComfyUI` por HTTP.

Configuracion manual esperada:

1. desplegar una imagen con `ComfyUI`, `IPAdapter Plus` y `Impact Pack` instalados
2. publicar un endpoint HTTP estable para `COMFYUI_BASE_URL`
3. cargar workflows JSON separados para `identity_image`, `content_image` y, cuando exista, `video`
4. mapear `COMFYUI_IP_ADAPTER_NODE_ID`, `COMFYUI_FACE_DETECTOR_NODE_ID` y `COMFYUI_FACE_DETAILER_NODE_ID` a nodos reales del workflow
5. garantizar acceso del runtime a la imagen de referencia facial o resolverla antes de inyectarla al workflow

### `Modal`

Se usa cuando el backend orquestado en `Coolify` necesita despertar un worker GPU para `ComfyUI`, entrenamiento o otra inferencia pesada.

Configuracion manual esperada:

1. publicar solo el worker GPU del servicio, no el HTTP publico
2. usar `Modal Volumes` o `CloudBucketMount` segun la naturaleza del runtime
3. invocarlo desde el runtime `FastAPI` alojado en `Coolify`
4. dejar `WebSocket` y polling HTTP como responsabilidad del runtime/orquestador en `Coolify`
5. consumirlo desde backend via `S1_IMAGE_PROVIDER=modal`, `S1_LORA_TRAIN_PROVIDER=modal`, `S1_LLM_PROVIDER=modal`, `S2_IMAGE_PROVIDER=modal` y `S2_VIDEO_PROVIDER=modal`

Estado aterrizado en el repo:

- `S1 image` publica su `FastAPI` en `Coolify` y delega ejecucion pesada al worker de `Modal`
- el bundle de `S1 image` embebe `ComfyUI`, `ComfyUI-IPAdapter-Flux` y `ComfyUI-Impact-Pack`
- el wrapper de `Modal` usa `Volume` para cache de modelos y no debe exponerse como API publica
- el servicio mantiene `runtime_stage=identity_image`, no consume `LoRA` y devuelve artifacts y errores normalizados compatibles con `visual_pipeline`

### `Beam` futuro

La capa neutral mantiene soporte para `Beam`, pero hoy no forma parte del camino critico por indisponibilidad operativa.

### `Runpod Serverless` legado

Se mantiene solo como referencia historica mientras termina la migracion fuera de `Runpod`.

Configuracion manual esperada:

1. publicar la imagen del worker de `infra/runpod-s1-image-serverless/` para `DEV-8` o la del runtime correspondiente para cada etapa
2. crear un template `serverless` en `Runpod` apuntando a esa imagen
3. configurar en el template las variables `COMFYUI_*` necesarias para el runtime interno
4. configurar `FLUX_DIFFUSION_MODEL_URL`, `FLUX_AE_URL`, `FLUX_CLIP_L_URL`, `FLUX_T5XXL_URL` e `IPADAPTER_FLUX_URL` si el worker debe bootstrapear modelos al arrancar
5. crear endpoints queue-based separados para `S1 image`, `S2 image`, `lora training` y `video`, con workers min/max explicitos
6. consumir los endpoints desde el backend via `VISUAL_EXECUTION_PROVIDER=runpod`, `RUNPOD_API_KEY`, `RUNPOD_ENDPOINT_IMAGE_IDENTITY`, `RUNPOD_ENDPOINT_IMAGE_CONTENT`, `RUNPOD_ENDPOINT_LORA_TRAIN` y `RUNPOD_ENDPOINT_VIDEO_GEN`
7. mantener `COMFYUI_BASE_URL` como detalle interno del worker, no como contrato de consumo externo

## Runtime deployable recomendado

Los runtimes productivos iniciales deben versionarse en el repo como una familia comun por servicio y desplegarse con wrappers por proveedor.

La familia de bundles debe cubrir para cada servicio:

- imagen `Docker` reproducible
- bootstrap de `ComfyUI`
- instalacion de `ComfyUI-IPAdapter-Flux` e `Impact Pack`
- workflows versionados por etapa
- scripts de arranque y healthcheck
- handlers o entrypoints neutrales compatibles con `jobs`, `status`, `result`, `healthcheck`, `base_render` y `face_detail` segun el runtime

El backend puede consumir ese runtime de dos maneras:

- via `ComfyUIHTTPExecutionClient` cuando el proveedor real es `comfyui_http`
- via `ModalExecutionClient` cuando el proveedor real es `modal`
- via `RoutedVisualExecutionClient` cuando la seleccion del proveedor se hace por etapa
- via `BeamExecutionClient` cuando en el futuro vuelva a haber disponibilidad operativa

### Familia de bundles nueva

- `infra/s1-image/`
- `infra/s1-lora-train/`
- `infra/s1-llm/`
- `infra/s2-image/`
- `infra/s2-video/`

Los bundles `runpod-*` quedan como baseline previo, no como direccion futura.

## Direccion futura de orquestacion

- dentro de `EPIC-3`, el front debera operar mediante un chatbot soportado por `LangGraph`
- ese chatbot podra solicitar acciones de `S1` y `S2` usando el orquestador como capa de coordinacion
- `LangGraph` y `FastAPI` viven en `Coolify`; no deben publicarse desde `Modal`
- la comunicacion de progreso con la UI debera evolucionar hacia `WebSockets`
- los serverless seguiran actuando como workers asincronos, mientras el orquestador centraliza estado, eventos y resultados
- el contrato recomendado para progreso es `HTTP + WebSocket opcional`; el polling HTTP sigue siendo fallback operativo

## Variables de entorno

- `VISUAL_EXECUTION_PROVIDER`
- `S1_IMAGE_PROVIDER`
- `S1_LORA_TRAIN_PROVIDER`
- `S1_LLM_PROVIDER`
- `S2_IMAGE_PROVIDER`
- `S2_VIDEO_PROVIDER`
- `BEAM_API_KEY`
- `BEAM_ENDPOINT_S1_IMAGE`
- `BEAM_ENDPOINT_S1_LORA_TRAIN`
- `BEAM_ENDPOINT_S1_LLM`
- `BEAM_ENDPOINT_S2_IMAGE`
- `BEAM_ENDPOINT_S2_VIDEO`
- `MODAL_TOKEN_ID`
- `MODAL_TOKEN_SECRET`
- `MODAL_ENDPOINT_S1_IMAGE`
- `MODAL_ENDPOINT_S1_LORA_TRAIN`
- `MODAL_ENDPOINT_S1_LLM`
- `MODAL_ENDPOINT_S2_IMAGE`
- `MODAL_ENDPOINT_S2_VIDEO`
- `S1_IMAGE_EXECUTION_BACKEND`
- `S1_IMAGE_MODAL_APP_NAME`
- `S1_IMAGE_MODAL_FUNCTION_NAME`
- `S1_IMAGE_MODAL_HEALTHCHECK_FUNCTION_NAME`
- `S1_LLM_RUNTIME_BASE_URL`
- `S1_LLM_RUNTIME_API_KEY`
- `S1_LLM_RUNTIME_MODEL`
- `S1_LLM_RUNTIME_TIMEOUT_SECONDS`
- `LLM_SERVERLESS_BASE_URL`
- `LLM_SERVERLESS_API_KEY`
- `LLM_SERVERLESS_MODEL`
- `OLLAMA_MODEL`
- `OLLAMA_TIMEOUT_SECONDS`
- `progress_url` derivado desde el endpoint cuando el runtime soporte `WebSocket`
- `PROVIDER_HTTP_TIMEOUT_SECONDS`
- `PROVIDER_POLL_INTERVAL_SECONDS`
- `PROVIDER_JOB_TIMEOUT_SECONDS`
- `RUNPOD_API_KEY`
- `RUNPOD_ENDPOINT_IMAGE_IDENTITY`
- `RUNPOD_ENDPOINT_IMAGE_CONTENT`
- `RUNPOD_ENDPOINT_IMAGE_GEN` como fallback legado
- `RUNPOD_ENDPOINT_LORA_TRAIN`
- `RUNPOD_ENDPOINT_VIDEO_GEN`
- `RUNPOD_POLL_INTERVAL_SECONDS`
- `RUNPOD_JOB_TIMEOUT_SECONDS`
- `RUNPOD_USE_RUNSYNC`
- `COMFYUI_BASE_URL`
- `COMFYUI_WORKFLOW_IMAGE_ID`
- `COMFYUI_WORKFLOW_IMAGE_VERSION`
- `COMFYUI_WORKFLOW_IDENTITY_ID`
- `COMFYUI_WORKFLOW_IDENTITY_VERSION`
- `COMFYUI_WORKFLOW_CONTENT_ID`
- `COMFYUI_WORKFLOW_CONTENT_VERSION`
- `COMFYUI_WORKFLOW_VIDEO_ID`
- `COMFYUI_WORKFLOW_VIDEO_VERSION`
- `COMFYUI_FLUX_DIFFUSION_MODEL_NAME`
- `COMFYUI_FLUX_AE_NAME`
- `COMFYUI_FLUX_CLIP_L_NAME`
- `COMFYUI_FLUX_T5XXL_NAME`
- `COMFYUI_FLUX_UNET_WEIGHT_DTYPE`
- `COMFYUI_IP_ADAPTER_MODEL`
- `COMFYUI_IP_ADAPTER_NODE_ID`
- `COMFYUI_FACE_DETECTOR_NODE_ID`
- `COMFYUI_FACE_DETAILER_NODE_ID`
- `COMFYUI_FACE_CONFIDENCE_THRESHOLD`
- `COMFYUI_RESUME_CACHE_MODE`
- `COMFYUI_HTTP_TIMEOUT_SECONDS`
- `MODEL_CACHE_ROOT`
- `MODEL_CACHE_FLUX_DIFFUSION_PATH`
- `MODEL_CACHE_FLUX_AE_PATH`
- `MODEL_CACHE_FLUX_CLIP_L_PATH`
- `MODEL_CACHE_FLUX_T5XXL_PATH`
- `MODEL_CACHE_IPADAPTER_FLUX_PATH`
- `MODEL_BOOTSTRAP_WAIT_SECONDS`

## Nota FLUX

`Supabase` no es bloqueante para levantar este runtime. El bloqueante real son las URLs accesibles para los assets pesados y para `reference_face_image_url`.

Mientras la DB no este lista, cada etapa de `S1` debe dejar manifests JSON persistibles fuera del repo:

- `S1 llm`: `generation_manifest`
- `S1 image`: `dataset_manifest` y `dataset_package`
- `S1 lora train`: `training_manifest` y metadata del `lora_model`

Direccion recomendada de persistencia para `S1 image`:

- `Modal Volume`: modelos, caches y staging efimero
- `Directus Files` o storage `S3-compatible`: `dataset_manifest`, `dataset_package` y artifacts de QA

Estado actual implementado:

- `S1 image` sigue materializando localmente el handoff para compatibilidad
- luego persiste `base_image`, `dataset_manifest` y `dataset_package` en `Directus Files`
- el resultado del runtime expone metadata tecnica suficiente para trazabilidad y futuros consumers:
  - seed efectiva
  - `seed_bundle`
  - workflow y version
  - modelo base
  - configuracion visual efectiva de `ip_adapter` y `face_detailer`
  - referencia facial usada
- `s1_identities` conserva el snapshot tecnico canonico por avatar para futuros flujos de `S1 Training` y `S2 Image`

Direccion recomendada del handoff:

1. `S1 image` produce `dataset_manifest`
2. `S1 image` persiste `dataset_package` solo el tiempo necesario para QA o retry
3. en modo `review`, el operador valida calidad antes de disparar training
4. en modo `autopromote`, el orquestador en `Coolify` dispara `S1 lora train` apenas termina la persistencia
5. luego se aplica limpieza de artifacts temporales segun politica

Para `FLUX.1-schnell`, el runtime ya no debe asumir un unico `checkpoint`. El deploy debe proveer assets separados para:

- `models/diffusion_models/flux1-schnell.safetensors`
- `models/text_encoders/clip_l.safetensors`
- `models/text_encoders/t5xxl_fp8_e4m3fn.safetensors`
- `models/vae/ae.safetensors`

Como los pesos oficiales de `FLUX.1-schnell` en Hugging Face son gated, la expectativa operativa es espejarlos primero a storage propio antes del deploy.
