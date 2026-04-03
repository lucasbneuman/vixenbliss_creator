# S1 Image

Servicio neutral de `S1 image` para `DEV-8`, con orquestacion HTTP en `Coolify` y worker GPU activo en `Modal`.

## Objetivo operativo

- generar imagenes base de identidad con `FLUX.1-schnell`
- mantener consistencia facial con `IP Adapter Plus`
- corregir degradaciones faciales con `Impact Pack FaceDetailer`
- exponer un runtime neutral consumible por `runtime_providers`
- dejar explicitamente a `FastAPI` y `LangGraph` fuera de `Modal`

## Contrato del servicio

- `POST /jobs`
- `GET /jobs/{id}`
- `GET /jobs/{id}/result`
- `GET /healthcheck`
- `GET /ws/jobs/{id}`

El runtime devuelve payloads compatibles con el motor visual actual:

- `provider`
- `workflow_id`
- `workflow_version`
- `provider_job_id`
- `artifacts`
- `successful_node_ids`
- `face_detection_confidence`
- `ip_adapter_used`
- `regional_inpaint_triggered`
- `metadata`
- `error_code`
- `error_message`

## Estructura

- `runtime/` contiene el runtime `FastAPI` que debe correr en `Coolify` como orquestador del servicio
- `providers/modal/` contiene el worker GPU activo para deploy en `Modal`
- `providers/beam/` queda como placeholder futuro

## Baseline técnico actual

El runtime nuevo porta el comportamiento útil del bundle legacy `infra/runpod-s1-image-serverless/`, pero deja a `Runpod` fuera del camino crítico:

- `FastAPI` y `LangGraph` corren en `Coolify` como capa de orquestacion
- `Modal` solo despierta el worker GPU con `ComfyUI` embebido
- workflow versionado `base-image-ipadapter-impact.json`
- alias lógico `plus_face` resuelto al asset real `flux-ipadapter-face.safetensors`
- fail-fast para `REFERENCE_IMAGE_NOT_FOUND`, `FACE_CONFIDENCE_UNAVAILABLE`, `RESUME_STATE_INCOMPLETE` y `COMFYUI_EXECUTION_FAILED`
- `runtime_stage=identity_image`
- `lora_supported=false`

## Storage híbrido

- modelos pesados y cache caliente: `Modal Volume`
- artifacts y resultados: preparados para storage externo o persistencia fuera del repo

## Variables relevantes

- `S1_IMAGE_PROVIDER=modal`
- `MODAL_ENDPOINT_S1_IMAGE`
- `COMFYUI_WORKFLOW_IDENTITY_ID`
- `COMFYUI_WORKFLOW_IDENTITY_VERSION`
- `COMFYUI_IP_ADAPTER_MODEL`
- `COMFYUI_FACE_CONFIDENCE_THRESHOLD`
- `COMFYUI_FLUX_DIFFUSION_MODEL_NAME`
- `COMFYUI_FLUX_AE_NAME`
- `COMFYUI_FLUX_CLIP_L_NAME`
- `COMFYUI_FLUX_T5XXL_NAME`
- `MODEL_CACHE_ROOT`
- `FLUX_DIFFUSION_MODEL_URL`
- `FLUX_AE_URL`
- `FLUX_CLIP_L_URL`
- `FLUX_T5XXL_URL`
- `IPADAPTER_FLUX_URL`
- `S1_IMAGE_EXECUTION_BACKEND=modal`
- `S1_IMAGE_MODAL_APP_NAME`
- `S1_IMAGE_MODAL_FUNCTION_NAME`
- `S1_IMAGE_MODAL_HEALTHCHECK_FUNCTION_NAME`

## Topologia operativa obligatoria

- `Coolify` aloja el `FastAPI` publico del servicio y el orquestador que consume `LangGraph`
- `Modal` no debe alojar el HTTP publico de `S1 image`
- `Modal` solo expone funciones GPU privadas para ejecutar `ComfyUI`, entrenamiento o inferencia pesada
- `MODAL_ENDPOINT_S1_IMAGE` debe apuntar al endpoint HTTP publicado por `Coolify`, no a un `modal.run`

## Nota sobre Runpod

`Runpod` queda como referencia histórica de la implementación original y fuente de comparación técnica, pero no como baseline nuevo de `S1 image`.
