# Runpod ComfyUI Image Runtime

## Objetivo

Esta carpeta define una unidad deployable para `GitHub` y `Runpod Serverless` que levanta un worker propio para generacion de imagen usando `ComfyUI` como motor interno.

La imagen esta preparada para:

- ejecutar jobs compatibles con `Runpod Serverless`
- encapsular `ComfyUI` como motor interno del worker
- instalar `IPAdapter Plus` e `Impact Pack`
- versionar un workflow base de imagen dentro del repo
- alinear el runtime con el contrato actual del backend visual
- hornear `ComfyUI` y custom nodes dentro de la imagen para evitar cold starts fragiles

No cubre aun:

- entrenamiento `FluxSchnell`
- runtime de video
- descarga garantizada de modelos pesados sin credenciales o URLs reales
- generacion automatica de workflows desde lenguaje natural

## Estructura

- `Dockerfile`: imagen productiva del runtime
- `requirements.txt`: dependencias del bootstrap
- `.env.example`: variables requeridas por este deploy
- `handler.py`: handler serverless compatible con `Runpod`
- `scripts/bootstrap.sh`: valida que `ComfyUI`, custom nodes y workflow esten horneados en la imagen
- `scripts/entrypoint.sh`: arranca `ComfyUI` localmente cuando el handler lo necesita
- `scripts/healthcheck.sh`: smoke check HTTP del runtime
- `scripts/download_models.sh`: descarga opcional de modelos desde URLs declaradas
- `workflows/base-image-ipadapter-impact.json`: workflow base versionado
- `config/node-map.example.json`: mapa logico de nodos esperados por el backend

## Contrato minimo del runtime

La imagen debe dejar operativo un worker que soporte como minimo:

- jobs queue-based en `Runpod Serverless`
- `ComfyUI` local accesible en `COMFYUI_BASE_URL` dentro del contenedor
- workflow `COMFYUI_WORKFLOW_IMAGE_ID` disponible en el runtime
- custom nodes `IPAdapter Plus` e `Impact Pack` instalados
- modelo `COMFYUI_IP_ADAPTER_MODEL` disponible o error fail-fast si no existe
- respuesta serverless estable con `artifacts`, `face_detection_confidence`, `ip_adapter_used`, `regional_inpaint_triggered`, `provider_job_id` y `metadata`
- nodos mapeables a:
  - `COMFYUI_IP_ADAPTER_NODE_ID`
  - `COMFYUI_FACE_DETECTOR_NODE_ID`
  - `COMFYUI_FACE_DETAILER_NODE_ID`

## Estrategia de build y runtime

Para reducir fallos en `Runpod Serverless`, el diseño actual no clona repositorios al arrancar el worker.

- durante el build de la imagen se clonan `ComfyUI`, `ComfyUI_IPAdapter_plus` y `ComfyUI-Impact-Pack`
- durante el build tambien se instalan sus dependencias Python
- durante el arranque del job el handler valida artefactos horneados, descarga modelos opcionales y arranca `ComfyUI` localmente si todavia no esta arriba

Esto evita fallos tipicos de cold start por `git clone` y reduce el costo de workers que reinician.

## Variables importantes

### Runpod

- `RUNPOD_API_KEY`
- `RUNPOD_ENDPOINT_IMAGE_GEN`
- `RUNPOD_POLL_INTERVAL_SECONDS`
- `RUNPOD_JOB_TIMEOUT_SECONDS`
- `RUNPOD_USE_RUNSYNC`

### Runtime ComfyUI

- `COMFYUI_BASE_URL`
- `COMFYUI_PORT`
- `COMFYUI_LISTEN`
- `COMFYUI_HOME`
- `COMFYUI_CUSTOM_NODES_DIR`
- `COMFYUI_MODELS_DIR`
- `COMFYUI_USER_DIR`

### Contrato visual

- `COMFYUI_WORKFLOW_IMAGE_ID`
- `COMFYUI_WORKFLOW_IMAGE_VERSION`
- `COMFYUI_IP_ADAPTER_MODEL`
- `COMFYUI_IP_ADAPTER_NODE_ID`
- `COMFYUI_FACE_DETECTOR_NODE_ID`
- `COMFYUI_FACE_DETAILER_NODE_ID`
- `COMFYUI_FACE_CONFIDENCE_THRESHOLD`

### Provision opcional de modelos

- `IPADAPTER_PLUS_FACE_URL`
- `CHECKPOINT_MODEL_URL`
- `VAE_MODEL_URL`

## Como levantarlo en GitHub + Runpod Serverless

### Build y push de imagen publica

1. publicar el repo en `GitHub`
2. ejecutar el workflow [runpod-comfyui-image.yml](/C:/Users/AVALITH/Desktop/Proyectos/vixenbliss_creator/.github/workflows/runpod-comfyui-image.yml)
3. verificar que la imagen quede publicada en `ghcr.io/<owner>/vixenbliss-runpod-comfyui:<tag>`
4. usar un tag trazable por commit, preferentemente `sha-<commit>`

### Template serverless

1. crear un `template` serverless nuevo en `Runpod`
2. usar como imagen `ghcr.io/<owner>/vixenbliss-runpod-comfyui:<tag>`
3. configurar en el template las variables de [infra/runpod-comfyui/.env.example](/C:/Users/AVALITH/Desktop/Proyectos/vixenbliss_creator/infra/runpod-comfyui/.env.example)
4. completar `IPADAPTER_PLUS_FACE_URL` y `CHECKPOINT_MODEL_URL` con artefactos reales
5. definir `workersMin` y `workersMax` explicitos para evitar jobs eternamente en `IN_QUEUE`

### Endpoint serverless

1. crear un endpoint `Queue based Serverless` desde ese template
2. registrar la URL real en `RUNPOD_ENDPOINT_IMAGE_GEN`
3. validar que el worker arranca por `handler.py` y no por `main.py`
4. revisar logs y confirmar que no hubo `git clone` en startup

### Smoke test

1. enviar `{\"input\":{\"action\":\"healthcheck\"}}`
2. confirmar `ok=true`
3. confirmar `runtime_checks.checkpoint_present=true`
4. confirmar `runtime_checks.ip_adapter_present=true`
5. confirmar `workflow_id=base-image-ipadapter-impact`

### Prueba funcional

1. correr `base_render` con prompt real y `reference_face_image_url`
2. confirmar que devuelve `artifacts`, `face_detection_confidence` y `regional_inpaint_triggered=false`
3. si `face_detection_confidence < 0.8`, correr `face_detail` con el `resume_checkpoint` devuelto por backend
4. confirmar que devuelve `artifacts` finales y `regional_inpaint_triggered=true`
5. guardar `provider_job_id`, logs y evidencia de artifacts recuperables

## Validacion operativa minima

### Smoke checks del runtime

- un job `healthcheck` devuelve `ok=true`
- `ComfyUI` responde en `/system_stats` dentro del contenedor
- el workflow base existe en el runtime
- `IPAdapter Plus` e `Impact Pack` aparecen instalados en `custom_nodes`

### Validacion funcional manual

1. correr un job con `action=healthcheck`
2. verificar que el workflow `base-image-ipadapter-impact` se usa en el handler
3. verificar que el nodo `ip_adapter_apply` existe y usa el modelo `plus_face`
4. verificar que el nodo `face_detector` y el nodo `face_detailer` existen
5. correr un job de generacion con prompt real
6. guardar `prompt_id`, logs y artifacts recuperables

## Evidencia recomendada para conectar con el backend

- URL real del runtime
- nombre/version del workflow base cargado
- ids reales de `ip_adapter`, `face_detector` y `face_detailer`
- evidencia de que el modelo `plus_face` esta disponible
- evidencia de que `base_render` devuelve `face_detection_confidence`
- una corrida exitosa con `regional_inpaint_triggered=false`
- una corrida exitosa con `regional_inpaint_triggered=true`
