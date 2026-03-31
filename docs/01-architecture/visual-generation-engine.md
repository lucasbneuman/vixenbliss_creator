# Visual Generation Engine

## Objetivo

Definir la primera capa ejecutable del motor visual sobre `ComfyUI` para generacion de imagen con consistencia facial y correccion regional trazable, separada por etapa operativa.

## Contrato operativo

El motor visual expone un request/response estable bajo `src/vixenbliss_creator/visual_pipeline/`.

## Mapa S1 y S2

- `S1` cubre generacion de imagenes de identidad para dataset y entrenamiento LoRA.
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

El contrato del motor visual admite dos despliegues validos y ambos pueden exponerse por etapa.

### `ComfyUI` HTTP directo

Se usa cuando el backend habla contra `COMFYUI_BASE_URL` y el runtime expone `ComfyUI` por HTTP.

Configuracion manual esperada:

1. desplegar una imagen con `ComfyUI`, `IPAdapter Plus` y `Impact Pack` instalados
2. publicar un endpoint HTTP estable para `COMFYUI_BASE_URL`
3. cargar workflows JSON separados para `identity_image`, `content_image` y, cuando exista, `video`
4. mapear `COMFYUI_IP_ADAPTER_NODE_ID`, `COMFYUI_FACE_DETECTOR_NODE_ID` y `COMFYUI_FACE_DETAILER_NODE_ID` a nodos reales del workflow
5. garantizar acceso del runtime a la imagen de referencia facial o resolverla antes de inyectarla al workflow

### `Runpod Serverless`

Se usa cuando el backend habla contra endpoints separados por etapa y el worker encapsula a `ComfyUI` como motor interno.

Configuracion manual esperada:

1. publicar la imagen del worker de `infra/runpod-s1-image-serverless/` para `DEV-8` o la del runtime correspondiente para cada etapa
2. crear un template `serverless` en `Runpod` apuntando a esa imagen
3. configurar en el template las variables `COMFYUI_*` necesarias para el runtime interno
4. configurar `FLUX_DIFFUSION_MODEL_URL`, `FLUX_AE_URL`, `FLUX_CLIP_L_URL`, `FLUX_T5XXL_URL` e `IPADAPTER_FLUX_URL` si el worker debe bootstrapear modelos al arrancar
5. crear endpoints queue-based separados para `S1 image`, `S2 image`, `lora training` y `video`, con workers min/max explicitos
6. consumir los endpoints desde el backend via `VISUAL_EXECUTION_PROVIDER=runpod`, `RUNPOD_API_KEY`, `RUNPOD_ENDPOINT_IMAGE_IDENTITY`, `RUNPOD_ENDPOINT_IMAGE_CONTENT`, `RUNPOD_ENDPOINT_LORA_TRAIN` y `RUNPOD_ENDPOINT_VIDEO_GEN`
7. mantener `COMFYUI_BASE_URL` como detalle interno del worker, no como contrato de consumo externo

## Runtime deployable recomendado

Los runtimes productivos iniciales pueden versionarse en el repo como una familia comun y desplegarse como endpoints separados.

La familia de bundles debe cubrir:

- imagen `Docker` reproducible
- bootstrap de `ComfyUI`
- instalacion de `ComfyUI-IPAdapter-Flux` e `Impact Pack`
- workflows versionados por etapa
- scripts de arranque y healthcheck
- handlers `Runpod Serverless` compatibles con `identity_image_generation`, `content_image_generation`, `lora_training`, `video_generation`, `base_render`, `face_detail` y `healthcheck` segun el runtime

El backend puede consumir ese runtime de dos maneras:

- via `ComfyUIExecutionHTTPClient` cuando el proveedor real es `comfyui`
- via `RunpodServerlessExecutionClient` cuando el proveedor real es `runpod`

### Bundle actual de `DEV-8`

- el bundle operativo actual para cerrar `DEV-8` es `infra/runpod-s1-image-serverless`
- este runtime esta acotado a `identity_image`
- `S1 train` queda previsto como runtime futuro separado y no forma parte del cierre de `DEV-8`

## Direccion futura de orquestacion

- dentro de `EPIC-3`, el front debera operar mediante un chatbot soportado por `LangGraph`
- ese chatbot podra solicitar acciones de `S1` y `S2` usando el orquestador como capa de coordinacion
- la comunicacion de progreso con la UI debera evolucionar hacia `WebSockets`
- los serverless seguiran actuando como workers asincronos, mientras el orquestador centraliza estado, eventos y resultados

## Variables de entorno

- `VISUAL_EXECUTION_PROVIDER`
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

## Nota FLUX

`Supabase` no es bloqueante para levantar este runtime. El bloqueante real son las URLs accesibles para los assets pesados y para `reference_face_image_url`.

Para `FLUX.1-schnell`, el runtime ya no debe asumir un unico `checkpoint`. El deploy debe proveer assets separados para:

- `models/diffusion_models/flux1-schnell.safetensors`
- `models/text_encoders/clip_l.safetensors`
- `models/text_encoders/t5xxl_fp8_e4m3fn.safetensors`
- `models/vae/ae.safetensors`

Como los pesos oficiales de `FLUX.1-schnell` en Hugging Face son gated, la expectativa operativa es espejarlos primero a storage propio antes del deploy.
