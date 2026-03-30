# Runpod ComfyUI Image Runtime

## Objetivo

Esta carpeta define una unidad deployable para `GitHub` y `Runpod` que levanta un runtime propio de `ComfyUI` orientado a la generacion de imagen del proyecto.

La imagen esta preparada para:

- exponer `ComfyUI` por HTTP para uso por API
- instalar `IPAdapter Plus` e `Impact Pack`
- versionar un workflow base de imagen dentro del repo
- alinear el runtime con el contrato actual del backend visual

No cubre aun:

- entrenamiento `FluxSchnell`
- runtime de video
- descarga garantizada de modelos pesados sin credenciales o URLs reales
- generacion automatica de workflows desde lenguaje natural

## Estructura

- `Dockerfile`: imagen productiva del runtime
- `requirements.txt`: dependencias del bootstrap
- `.env.example`: variables requeridas por este deploy
- `scripts/bootstrap.sh`: clona `ComfyUI`, instala custom nodes y prepara directorios
- `scripts/entrypoint.sh`: arranca el runtime y copia el workflow versionado
- `scripts/healthcheck.sh`: smoke check HTTP del runtime
- `scripts/download_models.sh`: descarga opcional de modelos desde URLs declaradas
- `workflows/base-image-ipadapter-impact.json`: workflow base versionado
- `config/node-map.example.json`: mapa logico de nodos esperados por el backend

## Contrato minimo del runtime

La imagen debe dejar operativo un `ComfyUI` que soporte como minimo:

- endpoint HTTP accesible en `COMFYUI_BASE_URL`
- workflow `COMFYUI_WORKFLOW_IMAGE_ID` disponible en el runtime
- custom nodes `IPAdapter Plus` e `Impact Pack` instalados
- modelo `COMFYUI_IP_ADAPTER_MODEL` disponible o error fail-fast si no existe
- nodos mapeables a:
  - `COMFYUI_IP_ADAPTER_NODE_ID`
  - `COMFYUI_FACE_DETECTOR_NODE_ID`
  - `COMFYUI_FACE_DETAILER_NODE_ID`

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

## Como levantarlo en GitHub + Runpod

1. subir esta carpeta al repositorio en `GitHub`
2. crear la imagen del runtime usando este `Dockerfile`
3. configurar en `Runpod` las variables del `.env.example`
4. asegurar que `IPADAPTER_PLUS_FACE_URL` y `CHECKPOINT_MODEL_URL` apunten a artefactos reales si queres bootstrap automatico de modelos
5. desplegar el serverless o endpoint contenedorizado
6. verificar que `COMFYUI_BASE_URL` responde y que el workflow base fue copiado a `COMFYUI_USER_DIR/workflows`

## Validacion operativa minima

### Smoke checks del runtime

- `scripts/healthcheck.sh` devuelve `ok`
- `ComfyUI` responde en `/system_stats`
- el workflow base existe en el runtime
- `IPAdapter Plus` e `Impact Pack` aparecen instalados en `custom_nodes`

### Validacion funcional manual

1. importar o abrir `base-image-ipadapter-impact.json`
2. verificar que el nodo `ip_adapter_apply` existe y usa el modelo `plus_face`
3. verificar que el nodo `face_detector` y el nodo `face_detailer` existen
4. correr un caso con confianza facial `>= 0.8` y confirmar que no hay correccion regional
5. correr un caso con confianza facial `< 0.8` y confirmar que si hay correccion regional
6. guardar `prompt_id`, logs y artifacts recuperables

## Evidencia recomendada para conectar con el backend

- URL real del runtime
- nombre/version del workflow base cargado
- ids reales de `ip_adapter`, `face_detector` y `face_detailer`
- evidencia de que el modelo `plus_face` esta disponible
- una corrida exitosa con `regional_inpaint_triggered=false`
- una corrida exitosa con `regional_inpaint_triggered=true`
