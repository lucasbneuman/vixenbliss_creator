# Runpod ComfyUI Image Runtime

## Objetivo

Esta carpeta define una unidad deployable para `GitHub` y `Runpod Serverless` que levanta un worker propio para generacion de imagen usando `ComfyUI` como motor interno.

La imagen esta preparada para:

- exponer `ComfyUI` por HTTP para uso por API
- ejecutar jobs compatibles con `Runpod Serverless`
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

1. subir esta carpeta al repositorio en `GitHub`
2. crear la imagen del runtime usando este `Dockerfile`
3. configurar en `Runpod` las variables del `.env.example`
4. asegurar que `IPADAPTER_PLUS_FACE_URL` y `CHECKPOINT_MODEL_URL` apunten a artefactos reales si queres bootstrap automatico de modelos
5. desplegar el endpoint `Queue based Serverless`
6. probar un job de healthcheck con `{\"input\": {\"action\": \"healthcheck\"}}`
7. verificar que el handler arranca `ComfyUI` internamente y que el workflow base fue copiado a `COMFYUI_USER_DIR/workflows`
8. revisar logs y confirmar que no hubo re-bootstrap de repositorios ni fallos de `git clone`

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
- una corrida exitosa con `regional_inpaint_triggered=false`
- una corrida exitosa con `regional_inpaint_triggered=true`
