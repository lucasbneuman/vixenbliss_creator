# Runpod Visual Serverless Runtime

## Estado

`DEPRECATED`

Este bundle ya no forma parte del baseline operativo del proyecto.

El provider activo actual es `Modal`. Este directorio se conserva solo como referencia historica y no debe usarse como guia de despliegue nueva.

## Objetivo historico

Esta carpeta define el worker serverless para generacion visual con `ComfyUI` encapsulado dentro de `Runpod`.

El runtime ahora esta alineado con `FLUX.1-schnell` y deja de asumir el contrato viejo de `checkpoint + VAE` tipico de SD.

## Que incluye

- imagen `Docker` reproducible para `Runpod Serverless`
- `ComfyUI` horneado en la imagen
- `ComfyUI-IPAdapter-Flux` horneado en la imagen
- `ComfyUI-Impact-Pack` horneado en la imagen
- workflow versionado en repo para `base_render` y `face_detail`
- handler serverless que devuelve `artifacts`, `face_detection_confidence`, `ip_adapter_used`, `regional_inpaint_triggered`, `provider_job_id` y `metadata`

## Contrato FLUX del runtime

El bootstrap del worker requiere estos assets reales en storage accesible por el contenedor:

- `FLUX_DIFFUSION_MODEL_URL` -> `models/diffusion_models/flux1-schnell.safetensors`
- `FLUX_AE_URL` -> `models/vae/ae.safetensors`
- `FLUX_CLIP_L_URL` -> `models/text_encoders/clip_l.safetensors`
- `FLUX_T5XXL_URL` -> `models/text_encoders/t5xxl_fp8_e4m3fn.safetensors`
- `IPADAPTER_FLUX_URL` -> `models/ipadapter-flux/flux-ipadapter-face.safetensors`

`Supabase` no es requisito para levantar este worker. Cualquier storage accesible sirve mientras entregue URLs directas al archivo. Para los assets gated de `FLUX.1-schnell`, la expectativa operativa es espejarlos primero a storage propio y no descargar desde Hugging Face en runtime.

## Estructura relevante de modelos en ComfyUI

- `models/diffusion_models/`
- `models/text_encoders/`
- `models/vae/`
- `models/ipadapter-flux/`

## Variables importantes

### Runpod

- `RUNPOD_API_KEY`
- `RUNPOD_ENDPOINT_IMAGE_IDENTITY`
- `RUNPOD_ENDPOINT_IMAGE_CONTENT`
- `RUNPOD_ENDPOINT_IMAGE_GEN` como fallback legado
- `RUNPOD_ENDPOINT_LORA_TRAIN`
- `RUNPOD_ENDPOINT_VIDEO_GEN`
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

### Contrato FLUX

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
- `COMFYUI_IP_ADAPTER_CLIP_VISION_MODEL`
- `COMFYUI_IP_ADAPTER_NODE_ID`
- `COMFYUI_FACE_DETECTOR_NODE_ID`
- `COMFYUI_FACE_DETAILER_NODE_ID`
- `COMFYUI_FACE_CONFIDENCE_THRESHOLD`

## Build y push de imagen publica

1. Publicar el repo en `GitHub`.
2. Ejecutar [runpod-visual-serverless-image.yml](/C:/Users/AVALITH/Desktop/Proyectos/vixenbliss_creator/.github/workflows/runpod-visual-serverless-image.yml).
3. Verificar que la imagen quede publicada en `ghcr.io/<owner>/vixenbliss-runpod-visual-serverless:<tag>`.
4. Usar un tag trazable por commit, preferentemente `sha-<commit>`.

## Template serverless en Runpod

### Path del repo

- `path`: `infra/runpod-visual-serverless`
- `dockerfile path`: `infra/runpod-visual-serverless/Dockerfile`

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

COMFYUI_WORKFLOW_IMAGE_ID=base-image-ipadapter-impact
COMFYUI_WORKFLOW_IMAGE_VERSION=2026-03-31
COMFYUI_WORKFLOW_IDENTITY_ID=identity-image-flux
COMFYUI_WORKFLOW_IDENTITY_VERSION=2026-03-31
COMFYUI_WORKFLOW_CONTENT_ID=content-image-flux
COMFYUI_WORKFLOW_CONTENT_VERSION=2026-03-31
COMFYUI_WORKFLOW_VIDEO_ID=video-image-placeholder
COMFYUI_WORKFLOW_VIDEO_VERSION=2026-03-31
COMFYUI_FLUX_DIFFUSION_MODEL_NAME=flux1-schnell.safetensors
COMFYUI_FLUX_AE_NAME=ae.safetensors
COMFYUI_FLUX_CLIP_L_NAME=clip_l.safetensors
COMFYUI_FLUX_T5XXL_NAME=t5xxl_fp8_e4m3fn.safetensors
COMFYUI_FLUX_UNET_WEIGHT_DTYPE=default
COMFYUI_IP_ADAPTER_MODEL=flux-ipadapter-face.safetensors
COMFYUI_IP_ADAPTER_CLIP_VISION_MODEL=google/siglip-so400m-patch14-384
COMFYUI_FACE_CONFIDENCE_THRESHOLD=0.8

FLUX_DIFFUSION_MODEL_URL=<url real espejada>
FLUX_AE_URL=<url real espejada>
FLUX_CLIP_L_URL=<url real espejada>
FLUX_T5XXL_URL=<url real espejada>
IPADAPTER_FLUX_URL=<url real espejada>
```

### Consideraciones

- `AE` no es un VAE clasico opcional. En FLUX es parte requerida del runtime.
- La imagen de referencia facial sigue entrando por `reference_face_image_url`.
- El worker levanta `ComfyUI` internamente; la app no consume ese HTTP de forma publica cuando el proveedor es `runpod`.

## Endpoint serverless

1. Crear endpoints `Queue based Serverless` separados para `identity image`, `content image`, `lora training` y `video` desde la misma familia de template o desde templates especializados.
2. Definir `workersMin` y `workersMax` explicitos para evitar jobs eternamente en `IN_QUEUE`.
3. Registrar las URLs reales en `RUNPOD_ENDPOINT_IMAGE_IDENTITY`, `RUNPOD_ENDPOINT_IMAGE_CONTENT`, `RUNPOD_ENDPOINT_LORA_TRAIN` y `RUNPOD_ENDPOINT_VIDEO_GEN`.
4. Mantener `RUNPOD_ENDPOINT_IMAGE_GEN` solo como fallback temporal si todavia no existe segmentacion completa.
5. Validar por logs que el worker arranca via `handler.py` y no via `main.py`.

## Smoke test

Request:

```json
{"input":{"action":"healthcheck"}}
```

Esperado:

- `ok=true`
- `runtime_checks.flux_diffusion_model_present=true`
- `runtime_checks.flux_ae_present=true`
- `runtime_checks.flux_clip_l_present=true`
- `runtime_checks.flux_t5xxl_present=true`
- `runtime_checks.ip_adapter_present=true`
- `runtime_contract.model_family=flux`

## Prueba funcional

1. Correr `base_render` con prompt real y `reference_face_image_url`.
2. Confirmar que devuelve `artifacts`, `face_detection_confidence` y `regional_inpaint_triggered=false`.
3. Si `face_detection_confidence < 0.8`, correr `face_detail` con el `resume_checkpoint` devuelto por backend.
4. Confirmar que devuelve `artifacts` finales y `regional_inpaint_triggered=true`.
5. Guardar `provider_job_id`, logs y evidencia de artifacts recuperables.

## Notas operativas

- `FLUX.1-schnell` en Hugging Face es gated, por eso el deploy debe usar URLs propias para los archivos pesados.
- `google/siglip-so400m-patch14-384` se mantiene como identificador del encoder visual requerido por `ComfyUI-IPAdapter-Flux`.
- Si el worker no tiene cache local del encoder visual, el plugin puede resolverlo por `from_pretrained`; si se quiere runtime totalmente aislado, hay que espejar tambien ese asset como snapshot compatible de `transformers`.
- La arquitectura objetivo del producto usa runtimes separados por etapa: `S1 image`, `S2 image`, `lora training` y `video`.
