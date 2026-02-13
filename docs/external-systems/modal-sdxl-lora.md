# Modal SDXL + LoRA (Sistema Externo)

Estado: activo
Ultima actualizacion: 2026-02-12
Fuente consolidada de: `MODAL_SDXL_LORA_INTEGRATION.md` + `MODAL_SUMMARY.md`

## Objetivo

Describir como VixenBliss depende de un worker serverless externo en Modal para inferencia SDXL + LoRA dinamico por request.

## Dependencia por sistema

- `S1` (Identidades): usa LoRA metadata y rutas R2 para avatares.
- `S2` (Contenido): usa el worker Modal para generar imagenes con LoRA.

## Flujo E2E (resumen)

1. Frontend llama `POST /api/v1/content/generate`.
2. Backend obtiene avatar + LoRA model metadata.
3. Backend genera presigned URL de R2 para `.safetensors`.
4. Backend llama a Modal con prompt + params + `lora_url`.
5. Worker Modal descarga LoRA, aplica a SDXL, genera imagen.
6. Worker hace unfuse/unload de LoRA (evita contaminacion entre requests).
7. Worker responde `image_base64`.
8. Backend decodifica, opcionalmente sube PNG a R2, guarda metadata y devuelve URL.

## Contrato externo (Backend -> Modal)

Endpoint externo esperado (ejemplo):
- `POST {MODAL_ENDPOINT_URL}` o `POST https://api.modal.com/v1/functions/{MODAL_SDXL_LORA_ENDPOINT_ID}/invoke`

Payload minimo:
```json
{
  "prompt": "string",
  "negative_prompt": "string",
  "lora_url": "https://...presigned...",
  "lora_scale": 0.9,
  "width": 1024,
  "height": 1024,
  "steps": 28,
  "cfg": 5.5,
  "seed": 42
}
```

Respuesta esperada (success):
```json
{
  "image_base64": "iVBORw0...",
  "generation_time_seconds": 8.5,
  "model_info": {
    "base_model": "sdxl",
    "lora_applied": true,
    "lora_scale": 0.9
  }
}
```

Respuesta de error (shape objetivo):
```json
{
  "error": "string",
  "error_code": "LORA_DOWNLOAD_FAILED|LORA_LOAD_FAILED|MODEL_LOAD_FAILED|GENERATION_FAILED|TIMEOUT|CUDA_OOM",
  "details": "string"
}
```

## Variables de entorno relevantes (backend)

- `LORA_PROVIDER=modal_sdxl_lora`
- `MODAL_SDXL_LORA_ENDPOINT_ID` y/o `MODAL_ENDPOINT_URL`
- `MODAL_API_KEY` o `MODAL_API_TOKEN`
- `MODAL_MODE=async|sync`
- `MODAL_POLL_SECONDS`, `MODAL_TIMEOUT_SECONDS`
- `R2_ENDPOINT_URL`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME`, `R2_PUBLIC_URL`

## Requisitos de seguridad

- No exponer credenciales R2 al worker: usar presigned URLs con TTL corto.
- Validar/sanitizar prompt y parametros numéricos antes de invocar.
- Enmascarar secretos y URLs firmadas en logs.
- Aplicar timeout y retry acotado con backoff.

## Riesgos conocidos y mitigaciones

- URL presigned expirada -> regenerar URL y reintentar.
- LoRA incompatible con SDXL -> fallback de provider o error controlado.
- Timeout/cold start -> ajustar timeout y capacidad de warm workers.
- CUDA OOM -> reducir resolucion/pasos o escalar GPU.
- Contaminacion de estado -> unfuse/unload LoRA siempre en `finally`.

## Performance orientativa

- Cold start: ~30-40s (carga modelo)
- Warm request: ~8-15s

## Checklist de operacion

1. Endpoint Modal desplegado y accesible.
2. `.env` backend configurado con provider Modal y R2.
3. Smoke test backend -> Modal -> R2 exitoso.
4. Monitoreo de errores `LORA_*`, `TIMEOUT`, `CUDA_OOM`.

## Archivos relacionados

- `backend/app/services/modal_sdxl_lora_client.py`
- `backend/app/services/lora_inference.py`
- `docs/SYSTEM_MAP.md`
- `docs/api-contracts/v1_endpoints.md`
- `docs/api-contracts/breaking-change-policy.md`
