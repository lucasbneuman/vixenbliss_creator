# Runpod S1 Model Loader

## Objetivo

Esta carpeta define un pod temporal de un solo uso para poblar el `Runpod Network Volume` de `S1` con los modelos requeridos por `DEV-8`.

No es un serverless ni un worker productivo. Su unica responsabilidad es descargar los modelos desde `Hugging Face` y escribirlos dentro del volumen montado.

## Cuando usarlo

Usalo cuando:

- el volumen de modelos este vacio
- falte algun archivo de `FLUX`
- quieras actualizar o rehidratar el volumen sin pasar por tu maquina local

No usarlo para:

- generar imagenes
- correr `ComfyUI`
- guardar dataset o artifacts finales del producto

## Recursos objetivo

- `Network Volume`: `kl6ru4hrmh`
- `Bucket`: `kl6ru4hrmh`
- `Data center`: `US-GA-2`
- mount esperado en el pod: `/runpod-volume`

## Layout final del volumen

```text
/runpod-volume/models/diffusion_models/flux1-schnell.safetensors
/runpod-volume/models/vae/ae.safetensors
/runpod-volume/models/text_encoders/clip_l.safetensors
/runpod-volume/models/text_encoders/t5xxl_fp8_e4m3fn.safetensors
/runpod-volume/models/ipadapter-flux/flux-ipadapter-face.safetensors
```

## Imagen del pod

Publicar con un workflow similar al de los bundles serverless o construirla localmente si preferis.

Path del repo:

- `path`: `infra/runpod-s1-model-loader`
- `dockerfile path`: `infra/runpod-s1-model-loader/Dockerfile`

Imagen esperada:

- `ghcr.io/<owner>/vixenbliss-runpod-s1-model-loader:sha-<commit>`

## Configuracion del pod

Crear un pod temporal con estas caracteristicas:

- `compute`: CPU
- `image`: `ghcr.io/<owner>/vixenbliss-runpod-s1-model-loader:sha-<commit>`
- `network volume`: `kl6ru4hrmh`
- `volume mount path`: `/runpod-volume`
- `container disk`: `20 GB` o mas
- `workers`: no aplica; es pod temporal

## Env del pod

```env
HF_TOKEN=<tu token de Hugging Face con acceso aprobado a FLUX.1-schnell>
RUNPOD_VOLUME_PATH=/runpod-volume
RUNPOD_MODELS_ROOT=/runpod-volume/models

FLUX_REPO_ID=black-forest-labs/FLUX.1-schnell
FLUX_DIFFUSION_FILENAME=flux1-schnell.safetensors
FLUX_AE_FILENAME=ae.safetensors

FLUX_TEXT_ENCODERS_REPO_ID=comfyanonymous/flux_text_encoders
FLUX_CLIP_L_FILENAME=clip_l.safetensors
FLUX_T5XXL_FILENAME=t5xxl_fp8_e4m3fn.safetensors

FLUX_IPADAPTER_REPO_ID=XLabs-AI/flux-ip-adapter
FLUX_IPADAPTER_SOURCE_FILENAME=ip_adapter.safetensors
FLUX_IPADAPTER_TARGET_FILENAME=flux-ipadapter-face.safetensors

FORCE_REDOWNLOAD=false
```

## Comportamiento

Cuando el pod arranca:

1. valida que el volumen este montado
2. descarga `flux1-schnell.safetensors` y `ae.safetensors` desde el repo gated de `black-forest-labs`
3. descarga `clip_l`, `t5xxl` e `ip_adapter` desde repos publicos
4. escribe todo dentro de `/runpod-volume/models/...`
5. termina

Si el archivo ya existe y `FORCE_REDOWNLOAD=false`, lo salta.

## Requisito critico

`HF_TOKEN` es obligatorio para los archivos gated de `black-forest-labs/FLUX.1-schnell`.

Antes de usar este pod:

- el usuario de Hugging Face debe haber aceptado los terminos del modelo
- el token debe tener acceso a ese repo

## Siguiente paso

Una vez poblado el volumen, desplegar `infra/runpod-s1-image-serverless` montando el mismo `Network Volume` y usarlo como fuente preferida de modelos.
