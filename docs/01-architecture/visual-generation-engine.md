# Visual Generation Engine

## Objetivo

Definir la primera capa ejecutable del motor visual sobre `ComfyUI` para generacion de imagen base con consistencia facial y correccion regional trazable.

## Contrato operativo

El motor visual expone un request/response estable bajo `src/vixenbliss_creator/visual_pipeline/`.

### Request

- `workflow_id` y `workflow_version` identifican el workflow operativo.
- `base_model_id`, `prompt`, `negative_prompt`, `seed`, `width` y `height` describen la corrida reproducible.
- `reference_face_image_url` habilita la rama opcional de `IP Adapter Plus`.
- `ip_adapter` registra `model_name`, `weight` y `node_id` opcional.
- `face_detailer` registra `confidence_threshold`, `inpaint_strength` y nodos opcionales del detector y del `FaceDetailer`.
- `resume_policy` y `resume_checkpoint` definen si la corrida debe retomarse desde el ultimo nodo exitoso.

### Response

- `artifacts` devuelve los archivos finales recuperables.
- `intermediate_state` serializa el checkpoint util para resume.
- `face_detection_confidence` registra la confianza facial usada para decidir si hay correccion regional.
- `ip_adapter_used` y `regional_inpaint_triggered` dejan trazabilidad explicita del camino ejecutado.
- `error_code` y `error_message` normalizan fallos del pipeline visual.

## Fail-fast canonico

- si `IP-Adapter` se activa sin `reference_face_image_url`, la request es invalida
- si la referencia facial no puede resolverse, el pipeline falla con `REFERENCE_IMAGE_NOT_FOUND`
- si el detector facial no devuelve una confianza util, el pipeline falla con `FACE_CONFIDENCE_UNAVAILABLE`
- si el checkpoint no contiene artefactos suficientes para retomar, la request se rechaza con `RESUME_STATE_INCOMPLETE`
- si `ComfyUI` no devuelve artefactos o falla la ejecucion HTTP, el error se normaliza como `COMFYUI_EXECUTION_FAILED`

## Politica de resume

- el checkpoint minimo de `base_render` debe incluir `workflow_id`, `workflow_version`, `base_model_id`, `seed`, `provider_job_id` y un artefacto `base_image`
- el checkpoint completado debe incluir al menos un artefacto `final_image`
- la implementacion actual serializa metadata y rutas de artefactos intermedios; no almacena tensores crudos en el repo

## Modos de ejecucion

El contrato del motor visual admite dos despliegues validos.

### `ComfyUI` HTTP directo

Se usa cuando el backend habla contra un runtime que expone `ComfyUI` por HTTP via `COMFYUI_BASE_URL`.

Configuracion manual esperada:

1. desplegar una imagen con `ComfyUI`, `IPAdapter Plus` y `Impact Pack` instalados
2. publicar un endpoint HTTP estable para `COMFYUI_BASE_URL`
3. cargar un workflow JSON compatible con `COMFYUI_WORKFLOW_IMAGE_ID`
4. mapear `COMFYUI_IP_ADAPTER_NODE_ID`, `COMFYUI_FACE_DETECTOR_NODE_ID` y `COMFYUI_FACE_DETAILER_NODE_ID` a nodos reales del workflow
5. garantizar acceso del runtime a la imagen de referencia facial o resolverla antes de inyectarla al workflow

### `Runpod Serverless`

Se usa cuando el backend habla contra `RUNPOD_ENDPOINT_IMAGE_GEN` y el worker encapsula a `ComfyUI` como motor interno.

Configuracion manual esperada:

1. publicar la imagen del worker de `infra/runpod-visual-serverless/` en un registry publico
2. crear un template `serverless` en `Runpod` apuntando a esa imagen
3. configurar en el template las variables `COMFYUI_*` necesarias para el runtime interno
4. configurar `IPADAPTER_PLUS_FACE_URL`, `CHECKPOINT_MODEL_URL` y `VAE_MODEL_URL` si el worker debe bootstrapear modelos al arrancar
5. crear el endpoint queue-based desde ese template con workers min/max explicitos
6. consumir el endpoint desde el backend via `VISUAL_EXECUTION_PROVIDER=runpod`, `RUNPOD_API_KEY` y `RUNPOD_ENDPOINT_IMAGE_GEN`
7. mantener `COMFYUI_BASE_URL` como detalle interno del worker, no como contrato de consumo externo

## Runtime deployable recomendado

El runtime productivo inicial para imagen puede versionarse en el repo bajo `infra/runpod-visual-serverless/`.

Ese paquete debe cubrir:

- imagen `Docker` reproducible
- bootstrap de `ComfyUI`
- instalacion de `IPAdapter Plus` e `Impact Pack`
- workflow base versionado en repo
- scripts de arranque y healthcheck
- handler `Runpod Serverless` compatible con jobs `base_render`, `face_detail` y `healthcheck`

El backend puede consumir ese runtime de dos maneras:

- via `ComfyUIExecutionHTTPClient` cuando el proveedor real es `comfyui`
- via `RunpodServerlessExecutionClient` cuando el proveedor real es `runpod`

## Variables de entorno

- `VISUAL_EXECUTION_PROVIDER`
- `RUNPOD_API_KEY`
- `RUNPOD_ENDPOINT_IMAGE_GEN`
- `RUNPOD_POLL_INTERVAL_SECONDS`
- `RUNPOD_JOB_TIMEOUT_SECONDS`
- `RUNPOD_USE_RUNSYNC`
- `COMFYUI_BASE_URL`
- `COMFYUI_WORKFLOW_IMAGE_ID`
- `COMFYUI_WORKFLOW_IMAGE_VERSION`
- `COMFYUI_IP_ADAPTER_MODEL`
- `COMFYUI_IP_ADAPTER_NODE_ID`
- `COMFYUI_FACE_DETECTOR_NODE_ID`
- `COMFYUI_FACE_DETAILER_NODE_ID`
- `COMFYUI_FACE_CONFIDENCE_THRESHOLD`
- `COMFYUI_RESUME_CACHE_MODE`
- `COMFYUI_HTTP_TIMEOUT_SECONDS`
