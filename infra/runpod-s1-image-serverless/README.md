# Runpod S1 Image Serverless Runtime

## Objetivo

Esta carpeta define el worker serverless de `S1 image` para `DEV-8`: generacion de imagenes base de identidad para dataset sobre `Runpod Serverless`, con consistencia facial via `IP Adapter Plus`, correccion regional via `Impact Pack FaceDetailer` y cache de iteracion para resume.

## Alcance operativo

- produce imagenes base consistentes para dataset
- usa `runtime_stage=identity_image`
- no consume `LoRA`
- ejecuta `base_render` y, si `face_detection_confidence < 0.8`, dispara `face_detail`
- conserva estado intermedio suficiente para reanudar desde el ultimo nodo exitoso sin recomputar el render inicial completo

`S1 train` no forma parte de este bundle. Queda previsto como runtime separado futuro dentro de `S1`.

## Que incluye

- imagen `Docker` reproducible para `Runpod Serverless`
- `ComfyUI` horneado en la imagen
- `ComfyUI-IPAdapter-Flux` horneado en la imagen
- `ComfyUI-Impact-Pack` horneado en la imagen
- workflow versionado para `base_render` y `face_detail`
- handler serverless compatible con `Runpod /run`
- fail-fast para `REFERENCE_IMAGE_NOT_FOUND`, `FACE_CONFIDENCE_UNAVAILABLE`, `RESUME_STATE_INCOMPLETE` y `COMFYUI_EXECUTION_FAILED`

## Contrato FLUX del runtime

El bootstrap del worker requiere estos assets reales en storage accesible por el contenedor:

- `FLUX_DIFFUSION_MODEL_URL` -> `models/diffusion_models/flux1-schnell.safetensors`
- `FLUX_AE_URL` -> `models/vae/ae.safetensors`
- `FLUX_CLIP_L_URL` -> `models/text_encoders/clip_l.safetensors`
- `FLUX_T5XXL_URL` -> `models/text_encoders/t5xxl_fp8_e4m3fn.safetensors`
- `IPADAPTER_FLUX_URL` -> `models/ipadapter-flux/flux-ipadapter-face.safetensors`

`Supabase` no es requisito para levantar este worker. La opcion preferida para destrabar el deploy es montar un `Runpod Network Volume` y guardar ahi los modelos. Los assets gated de `FLUX.1-schnell` tambien pueden espejarse a storage propio como fallback.

## Variables importantes

### Runpod

- `RUNPOD_API_KEY`
- `RUNPOD_ENDPOINT_IMAGE_IDENTITY`
- `RUNPOD_POLL_INTERVAL_SECONDS`
- `RUNPOD_JOB_TIMEOUT_SECONDS`
- `RUNPOD_USE_RUNSYNC`

### Runtime interno

- `COMFYUI_BASE_URL`
- `COMFYUI_PORT`
- `COMFYUI_LISTEN`
- `COMFYUI_HOME`
- `COMFYUI_CUSTOM_NODES_DIR`
- `COMFYUI_MODELS_DIR`
- `COMFYUI_USER_DIR`
- `COMFYUI_INPUT_DIR`
- `RUNPOD_VOLUME_PATH`
- `RUNPOD_MODELS_ROOT`

### Contrato S1 image

- `COMFYUI_WORKFLOW_IDENTITY_ID`
- `COMFYUI_WORKFLOW_IDENTITY_VERSION`
- `COMFYUI_IP_ADAPTER_MODEL`
- `COMFYUI_IP_ADAPTER_CLIP_VISION_MODEL`
- `COMFYUI_IP_ADAPTER_NODE_ID`
- `COMFYUI_FACE_DETECTOR_NODE_ID`
- `COMFYUI_FACE_DETAILER_NODE_ID`
- `COMFYUI_FACE_CONFIDENCE_THRESHOLD`
- `COMFYUI_FLUX_DIFFUSION_MODEL_NAME`
- `COMFYUI_FLUX_AE_NAME`
- `COMFYUI_FLUX_CLIP_L_NAME`
- `COMFYUI_FLUX_T5XXL_NAME`
- `COMFYUI_FLUX_UNET_WEIGHT_DTYPE`

### Paths preferidos en `Runpod Network Volume`

- `RUNPOD_FLUX_DIFFUSION_MODEL_PATH`
- `RUNPOD_FLUX_AE_PATH`
- `RUNPOD_FLUX_CLIP_L_PATH`
- `RUNPOD_FLUX_T5XXL_PATH`
- `RUNPOD_IPADAPTER_FLUX_PATH`

## Nota sobre `plus_face`

`DEV-8` pide `IP Adapter Plus` con modelo logico `plus_face`. En este bundle:

- `COMFYUI_IP_ADAPTER_MODEL=plus_face` es el nombre operativo esperado para configuracion y docs
- internamente el worker lo resuelve al asset real `flux-ipadapter-face.safetensors`

Esto evita ambiguedad entre el nombre de negocio/documentacion y el archivo real usado por el runtime FLUX.

## Build y push de imagen publica

1. Publicar el repo en `GitHub`.
2. Ejecutar [runpod-s1-image-serverless-image.yml](/C:/Users/AVALITH/Desktop/Proyectos/vixenbliss_creator/.github/workflows/runpod-s1-image-serverless-image.yml).
3. Verificar que la imagen quede publicada en `ghcr.io/<owner>/vixenbliss-runpod-s1-image-serverless:<tag>`.
4. Usar un tag trazable por commit, preferentemente `sha-<commit>`.

## Template serverless en Runpod

### Path del repo

- `path`: `infra/runpod-s1-image-serverless`
- `dockerfile path`: `infra/runpod-s1-image-serverless/Dockerfile`

Si el formulario de Runpod toma el `Dockerfile` relativo al `path`, usar simplemente `Dockerfile`.

### Env minimo sugerido

```env
COMFYUI_BASE_URL=http://127.0.0.1:8188
COMFYUI_PORT=8188
COMFYUI_LISTEN=0.0.0.0
COMFYUI_HOME=/opt/comfyui
COMFYUI_CUSTOM_NODES_DIR=/opt/comfyui/custom_nodes
COMFYUI_MODELS_DIR=/opt/comfyui/models
COMFYUI_USER_DIR=/opt/comfyui/user/default
COMFYUI_INPUT_DIR=/opt/comfyui/input
RUNPOD_VOLUME_PATH=/runpod-volume
RUNPOD_MODELS_ROOT=/runpod-volume/models

COMFYUI_WORKFLOW_IDENTITY_ID=base-image-ipadapter-impact
COMFYUI_WORKFLOW_IDENTITY_VERSION=2026-03-31
COMFYUI_IP_ADAPTER_MODEL=plus_face
COMFYUI_IP_ADAPTER_CLIP_VISION_MODEL=google/siglip-so400m-patch14-384
COMFYUI_FACE_CONFIDENCE_THRESHOLD=0.8

RUNPOD_FLUX_DIFFUSION_MODEL_PATH=/runpod-volume/models/diffusion_models/flux1-schnell.safetensors
RUNPOD_FLUX_AE_PATH=/runpod-volume/models/vae/ae.safetensors
RUNPOD_FLUX_CLIP_L_PATH=/runpod-volume/models/text_encoders/clip_l.safetensors
RUNPOD_FLUX_T5XXL_PATH=/runpod-volume/models/text_encoders/t5xxl_fp8_e4m3fn.safetensors
RUNPOD_IPADAPTER_FLUX_PATH=/runpod-volume/models/ipadapter-flux/flux-ipadapter-face.safetensors

FLUX_DIFFUSION_MODEL_URL=CHANGEME
FLUX_AE_URL=CHANGEME
FLUX_CLIP_L_URL=CHANGEME
FLUX_T5XXL_URL=CHANGEME
IPADAPTER_FLUX_URL=CHANGEME
```

### Layout del volumen

Dentro del `Network Volume` monta estos archivos:

```text
/runpod-volume/models/diffusion_models/flux1-schnell.safetensors
/runpod-volume/models/vae/ae.safetensors
/runpod-volume/models/text_encoders/clip_l.safetensors
/runpod-volume/models/text_encoders/t5xxl_fp8_e4m3fn.safetensors
/runpod-volume/models/ipadapter-flux/flux-ipadapter-face.safetensors
```

El worker primero intenta enlazar/copiar desde el volumen y solo si faltan archivos cae al bootstrap por URL.

### Volume creado para destrabar `DEV-8`

- `Volume ID`: `kl6ru4hrmh`
- `Bucket name`: `kl6ru4hrmh`
- `Endpoint URL`: `https://s3api-us-ga-2.runpod.io`
- `Data center`: `US-GA-2`

Este volumen puede usarse como storage transitorio de modelos de IA para `S1 image`. No es el storage principal recomendado para dataset ni artifacts de negocio.

## Endpoint serverless

1. Crear un endpoint `Queue based Serverless` especifico para `S1 image`.
2. Definir `workersMin` y `workersMax` explicitos para evitar jobs eternamente en `IN_QUEUE`.
3. Registrar la URL real en `RUNPOD_ENDPOINT_IMAGE_IDENTITY`.
4. Validar por logs que el worker arranca via `handler.py` y no via `main.py`.

## Smoke test

Request:

```json
{"input":{"action":"healthcheck"}}
```

Esperado:

- `ok=true`
- `runtime_contract.model_family=flux`
- `runtime_contract.runtime_stage=identity_image`
- `runtime_contract.workflow_scope=s1_image`
- `runtime_contract.lora_supported=false`
- `runtime_checks.flux_diffusion_model_present=true`
- `runtime_checks.ip_adapter_present=true`

## Prueba funcional

1. Correr `base_render` con `runtime_stage=identity_image` y `reference_face_image_url` real.
2. Confirmar que devuelve `artifacts`, `face_detection_confidence` y `regional_inpaint_triggered=false` cuando la confianza es `>= 0.8`.
3. Si `face_detection_confidence < 0.8`, correr `face_detail` con el `resume_checkpoint`.
4. Confirmar que devuelve `artifacts` finales y `regional_inpaint_triggered=true`.
5. Guardar `provider_job_id`, logs y evidencia de artifacts recuperables.

## Resume y cache de iteracion

- `base_render` debe devolver suficiente estado para retomar
- el checkpoint minimo incluye `workflow_id`, `workflow_version`, `base_model_id`, `seed`, `provider_job_id` y un artefacto `base_image`
- `face_detail` rehidrata la imagen base desde ese checkpoint
- si el checkpoint no alcanza, el runtime falla con `RESUME_STATE_INCOMPLETE`

## Extension futura

`S1` a nivel negocio tambien incluye entrenamiento LoRA, pero eso debera vivir en un runtime separado, por ejemplo `infra/runpod-s1-lora-train`, compartiendo la misma familia `Flux` sin mezclarse con este worker visual.
