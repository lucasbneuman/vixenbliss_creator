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
- alias lógico `plus_face` resuelto al asset real `ip-adapter.bin`
- fail-fast para `REFERENCE_IMAGE_NOT_FOUND`, `FACE_CONFIDENCE_UNAVAILABLE`, `RESUME_STATE_INCOMPLETE` y `COMFYUI_EXECUTION_FAILED`
- `runtime_stage=identity_image`
- `lora_supported=false`

## Storage híbrido

- modelos pesados y cache caliente: `Modal Volume`
- artifacts y resultados: preparados para storage externo o persistencia fuera del repo

## Variables relevantes

- `S1_IMAGE_PROVIDER=modal`
- `S1_IMAGE_MODAL_APP_NAME`
- `S1_IMAGE_MODAL_FUNCTION_NAME`
- `S1_IMAGE_MODAL_HEALTHCHECK_FUNCTION_NAME`
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
- `MODAL_TOKEN_ID` y `MODAL_TOKEN_SECRET` alcanzan para invocar la app privada `vixenbliss-s1-image`
- `MODAL_ENDPOINT_S1_IMAGE` solo como fallback legado si existe un web endpoint intermedio

## Prueba local minima

Para una prueba local realista de `S1 image`, el stack minimo queda asi:

- `FastAPI` del runtime ejecutado localmente o en `Coolify`
- acceso autenticado a `Modal` para despertar el worker GPU
- `HF_TOKEN` con acceso a `FLUX.1-schnell`
- `Modal Volume` ya primado con los assets pesados o URLs de bootstrap validas
- una `reference_face_image_url` accesible desde el worker

Validacion minima recomendada:

1. correr `runtime_healthcheck(deep=True)` sobre el worker de `Modal`
2. levantar el runtime `FastAPI` con `S1_IMAGE_EXECUTION_BACKEND=modal`
3. ejecutar `POST /jobs` con `runtime_stage=identity_image`
4. verificar que el resultado devuelva `base_image`, `resume_checkpoint` y `face_detection_confidence`
5. si la confianza facial queda baja, validar la corrida posterior de `face_detail`

## Topologia operativa obligatoria

- `Coolify` aloja el `FastAPI` publico del servicio y el orquestador que consume `LangGraph`
- `Modal` no debe alojar el HTTP publico de `S1 image`
- `Modal` solo expone funciones GPU privadas para ejecutar `ComfyUI`, entrenamiento o inferencia pesada
- el contrato principal con `Modal` es `token + app_name + function_name`; un `MODAL_ENDPOINT_S1_IMAGE` solo aplica como compatibilidad hacia un proxy HTTP externo

## Estrategia de persistencia recomendada

La salida de `S1 image` no debe tratarse como storage permanente en `Modal`.

Direccion recomendada:

- `Modal Volume`: solo para modelos, caches de `ComfyUI` y staging efimero de muy corta vida
- `Directus Files` sobre storage `S3-compatible`: fuente de verdad para `base_image` y evidencia visual de QA
- `s1_artifacts`, `s1_generation_runs` y `s1_identities`: fuente de verdad para `dataset_manifest`, `dataset_package_path`, `character_id` y `seed_bundle`

Modos operativos esperados:

1. modo `review`
- `S1 image` registra `dataset_manifest` y `dataset_package`
- el equipo revisa calidad del dataset
- recien despues se habilita `S1 lora train`

2. modo `autopromote`
- `S1 image` registra como minimo `dataset_manifest`
- `dataset_package` se guarda con retencion corta
- el orquestador dispara `S1 lora train` al terminar la generacion
- luego aplica limpieza automatica de artifacts temporales segun politica

Mientras el flujo este en validacion, priorizar `review`.
Cuando la calidad del dataset ya este estabilizada, pasar a `autopromote` con storage en `Directus`.

## Nota sobre Runpod

`Runpod` queda como referencia histórica de la implementación original y fuente de comparación técnica, pero no como baseline nuevo de `S1 image`.
