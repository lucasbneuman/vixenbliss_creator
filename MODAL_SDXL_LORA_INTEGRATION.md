# 🚀 Modal SDXL LoRA Worker - Guía de Integración Completa

## 📋 Tabla de Contenidos
1. [Arquitectura General](#arquitectura-general)
2. [Flujo End-to-End](#flujo-end-to-end)
3. [Contrato API](#contrato-api)
4. [LoRA & R2 Integration](#lora--r2-integration)
5. [Variables de Entorno](#variables-de-entorno)
6. [Ejemplos Prácticos](#ejemplos-prácticos)
7. [Error Handling](#error-handling)
8. [Performance & Scaling](#performance--scaling)
9. [Prompt para Codex](#prompt-para-codex)

---

## Arquitectura General

```
┌─────────────────────────────────────────────────────────────┐
│  FRONTEND (Next.js 14)                                      │
│  ├─ User solicita generar contenido con Avatar + LoRA      │
│  └─ POST /api/v1/content/generate                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ HTTP (JSON)
                     │
┌────────────────────▼────────────────────────────────────────┐
│  BACKEND (FastAPI)                                          │
│  ├─ Route: POST /api/v1/content/generate                   │
│  ├─ Fetch Avatar + LoRA metadata from Supabase             │
│  ├─ Generate presigned R2 URL para LoRA .safetensors      │
│  ├─ Call runpod_sdxl_lora_client.generate_image_with_lora()│
│  └─ client hace HTTP POST a Modal endpoint                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ HTTP POST (JSON)
                     │ Payload: {prompt, lora_url, seed, ...}
                     │
┌────────────────────▼────────────────────────────────────────┐
│  MODAL SERVERLESS (GPU Cloud)                              │
│  ├─ HTTP endpoint for image generation                     │
│  ├─ Load SDXL base model (cached)                          │
│  ├─ Download LoRA from R2 presigned URL                   │
│  ├─ Apply LoRA weights to model                            │
│  ├─ Generate image (diffusers pipeline)                    │
│  ├─ Unfuse LoRA (clean state for next request)            │
│  └─ Return: {image_base64}                                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ HTTP Response (JSON)
                     │ {image_base64: "..."}
                     │
┌────────────────────▼────────────────────────────────────────┐
│  BACKEND (continues)                                        │
│  ├─ Decode base64 → PNG bytes                             │
│  ├─ (Optional) Upload to R2 for persistence               │
│  ├─ Save metadata to DB                                   │
│  └─ Return URL to frontend                                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ HTTP Response (JSON)
                     │ {image_url, ...}
                     │
┌────────────────────▼────────────────────────────────────────┐
│  FRONTEND                                                   │
│  └─ Display generated image to user                        │
└─────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  CLOUDFLARE R2 (Storage)                                     │
│  ├─ Presigned URLs for LoRA .safetensors files             │
│  ├─ Optional: store output images                          │
│  └─ Public CDN for frontend display                        │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  SUPABASE (Database)                                         │
│  ├─ Avatar metadata (ID, name, LoRA associations)          │
│  ├─ LoRA model info (name, path in R2, version)            │
│  └─ Content pieces (generated images metadata)             │
└──────────────────────────────────────────────────────────────┘
```

---

## Flujo End-to-End

### Step 1: Frontend envía solicitud
```javascript
// frontend/app/content/generate.ts
POST /api/v1/content/generate
{
  "avatar_id": "uuid-123",
  "custom_prompt": "ultra detailed face",  // opcional
  "tier": "capa1",  // calidad/resolución
}
```

### Step 2: Backend prepara payload
**Archivo**: `backend/app/api/content.py`

```python
# 1. Obtener avatar + LoRA asociado
avatar = await supabase.table("avatars").select("*").eq("id", avatar_id).single()
# avatar = {
#   "id": "uuid-123",
#   "name": "Character X",
#   "lora_model_id": "lora-456",
#   ...
# }

# 2. Obtener LoRA metadata
lora_model = await supabase.table("lora_models").select("*").eq("id", "lora-456").single()
# lora_model = {
#   "id": "lora-456",
#   "name": "style_cyberpunk",
#   "r2_path": "loras/cyberpunk_v2.safetensors",
#   "version": "2.0",
#   ...
# }

# 3. Generar presigned R2 URL para LoRA (válida 15 min)
presigned_lora_url = await storage_service.generate_presigned_url(
    file_path=lora_model["r2_path"],
    expiration_seconds=900  # 15 minutos
)
# presigned_lora_url = "https://r2.../loras/cyberpunk_v2.safetensors?X-Amz-Signature=..."

# 4. Construir prompt final
final_prompt = f"{avatar['base_prompt']} {custom_prompt or ''}"
# final_prompt = "ultra detailed cyberpunk character face, sharp details"

# 5. Llamar Modal worker via HTTP
result = await runpod_sdxl_lora_client.generate_image_with_lora(
    prompt=final_prompt,
    negative_prompt="blurry, low quality",
    lora_url=presigned_lora_url,
    lora_scale=0.9,
    width=1024,
    height=1024,
    seed=seed if seed else None,
    steps=28,
    cfg=5.5,
)
```

### Step 3: Modal worker procesa
**Archivo**: `modal_app/sdxl_lora_handler.py`

```python
# 1. Recibe HTTP POST
@app.function()
async def generate_image(request_data: dict):
    # request_data = {
    #   "prompt": "ultra detailed cyberpunk...",
    #   "lora_url": "https://presigned-r2-url/...",
    #   "lora_scale": 0.9,
    #   ...
    # }
    
    # 2. Load SDXL base (cached en warm worker)
    pipe = load_sdxl_pipeline()  # 1.5s si cached, 30s si cold-start
    
    # 3. Download LoRA desde presigned URL
    lora_path = download_to_temp(request_data["lora_url"])
    # File downloaded to: /tmp/lora_xyz.safetensors (50-100MB)
    
    # 4. Apply LoRA to pipeline
    apply_lora_weights(pipe, lora_path, scale=request_data["lora_scale"])
    
    # 5. Generate image
    image = pipe(
        prompt=request_data["prompt"],
        num_inference_steps=28,
        guidance_scale=5.5,
        height=1024,
        width=1024,
    ).images[0]
    
    # 6. Unfuse LoRA (critical: prevents model contamination)
    unfuse_lora_weights(pipe)
    
    # 7. Encode to base64
    image_base64 = encode_image_to_base64(image)  # ~8KB for PNG
    
    # 8. Return response
    return {
        "image_base64": image_base64,
        "generation_time": 8.5,  # segundos
        "model_info": {
            "base_model": "SDXL 1.0",
            "lora_version": "2.0",
            "applied_scale": 0.9,
        }
    }
```

### Step 4: Backend procesa respuesta
```python
# 1. Recibe image_base64 del Modal worker
response = {
    "image_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
    "generation_time": 8.5
}

# 2. Decode base64 → PNG bytes
image_bytes = base64.b64decode(response["image_base64"])

# 3. (OPCIONAL) Guardar en R2
output_url = await storage_service.upload_file(
    file_content=image_bytes,
    file_path=f"content/{avatar_id}/{uuid.uuid4()}.png",
    content_type="image/png",
)
# output_url = "https://cdn.example.com/content/uuid-123/abc-def.png"

# 4. Guardar metadata en DB
content_piece = ContentPiece(
    avatar_id=avatar_id,
    lora_id=lora_model_id,
    image_url=output_url,
    image_hash=hashlib.sha256(image_bytes).hexdigest(),
    generation_params={
        "prompt": final_prompt,
        "lora_scale": 0.9,
        "seed": seed,
        "generation_time": 8.5,
    },
    created_at=datetime.utcnow(),
)
await db.add(content_piece)
await db.commit()

# 5. Retornar al frontend
return {
    "image_url": output_url,
    "content_id": content_piece.id,
    "generation_time": 8.5,
}
```

### Step 5: Frontend muestra imagen
```javascript
// frontend/app/content/[id].tsx
const { image_url } = response;
// <Image src={image_url} alt="Generated" />
```

---

## Contrato API

### Request (Backend → Modal)

**Método**: `POST`  
**Endpoint**: `https://modal-app.modal.run/generate-image`  
**Headers**: 
```json
{
  "Content-Type": "application/json",
  "Authorization": "Bearer <MODAL_API_TOKEN>"  // si requiere
}
```

**Body**:
```json
{
  "prompt": "string (required)",
  "negative_prompt": "string (optional, default: '')",
  "lora_url": "string (optional) — presigned URL to .safetensors",
  "lora_scale": "number (optional, default: 1.0, range: 0.0-1.0)",
  "width": "integer (optional, default: 1024, values: 512/768/1024/1344/1536)",
  "height": "integer (optional, default: 1024)",
  "steps": "integer (optional, default: 28, range: 20-50)",
  "cfg": "number (optional, default: 5.5, range: 1.0-20.0)",
  "seed": "integer (optional) — use for reproducibility",
  "timeout": "integer (optional, default: 60, max: 300) — seconds"
}
```

**Example Request**:
```json
{
  "prompt": "a beautiful woman in cyberpunk aesthetic, detailed face, sharp eyes, wearing neon jacket, ultra realistic, 8k",
  "negative_prompt": "blurry, low quality, distorted, ugly",
  "lora_url": "https://1b25234e908e6f431171a26744700241.r2.cloudflarestorage.com/vixenbliss-creator/loras/cyberpunk_v2.safetensors?X-Amz-Signature=...",
  "lora_scale": 0.9,
  "width": 1024,
  "height": 1024,
  "steps": 28,
  "cfg": 5.5,
  "seed": 42
}
```

---

### Response (Modal → Backend)

**Status Code**: `200 OK` (success) or `400/500` (error)

**Success Response**:
```json
{
  "image_base64": "iVBORw0KGgoAAAANSUhEUgAABLAAAASwCAYAAABIfLLa...",
  "image_size": [1024, 1024],
  "generation_time_seconds": 8.5,
  "model_info": {
    "base_model": "stabilityai/stable-diffusion-xl-base-1.0",
    "lora_applied": true,
    "lora_version": "2.0",
    "lora_scale": 0.9
  },
  "metadata": {
    "seed_used": 42,
    "actual_steps": 28,
    "actual_cfg": 5.5
  }
}
```

**Error Response** (4xx/5xx):
```json
{
  "error": "string — error message",
  "error_code": "string — error type",
  "details": "string (optional) — detailed traceback",
  "retry_after": "integer (optional) — seconds to wait before retry"
}
```

**Error Codes**:
- `INVALID_PROMPT`: Prompt vacío o contiene caracteres prohibidos
- `LORA_DOWNLOAD_FAILED`: No pudo descargar LoRA desde presigned URL
- `LORA_LOAD_FAILED`: LoRA descargado pero no se puede cargar/aplicar
- `MODEL_LOAD_FAILED`: No pudo cargar base SDXL
- `GENERATION_FAILED`: Error durante inferencia
- `TIMEOUT`: Generación tardó más que timeout limit
- `CUDA_OOM`: Memoria GPU insuficiente

---

## LoRA & R2 Integration

### ¿Cómo se pasan LoRAs desde R2?

**Flujo**:

1. **LoRA almacenado en R2**:
   ```
   s3://vixenbliss-creator/loras/
   ├─ cyberpunk_v2.safetensors     (80 MB, shareable)
   ├─ realistic_skin_v1.safetensors (50 MB)
   └─ anime_style_v3.safetensors    (60 MB)
   ```

2. **Backend genera presigned URL**:
   ```python
   # backend/app/services/storage.py
   presigned_url = storage_service.generate_presigned_url(
       file_path="loras/cyberpunk_v2.safetensors",
       expiration_seconds=900  # válida 15 minutos
   )
   # Retorna: https://...r2.../loras/cyberpunk_v2.safetensors?X-Amz-Signature=abc123&X-Amz-Expires=900&...
   ```

3. **Modal worker descarga LoRA**:
   ```python
   @app.function()
   def download_lora(lora_url: str) -> str:
       """Download LoRA from presigned URL to temp location."""
       response = requests.get(lora_url, timeout=120)
       response.raise_for_status()
       
       # Save to temp
       temp_path = f"/tmp/lora_{uuid.uuid4()}.safetensors"
       with open(temp_path, "wb") as f:
           f.write(response.content)
       
       logger.info(f"Downloaded LoRA: {len(response.content)} bytes to {temp_path}")
       return temp_path
   ```

4. **Apply LoRA to SDXL**:
   ```python
   from diffusers import StableDiffusionXLPipeline
   from peft import LoraConfig, get_peft_model
   
   def apply_lora(pipe: StableDiffusionXLPipeline, lora_path: str, scale: float = 1.0):
       """Apply LoRA weights to pipeline."""
       # Método 1: diffusers native (RECOMENDADO)
       try:
           pipe.load_lora_weights(lora_path)
           pipe.fuse_lora(lora_scale=scale)
           logger.info(f"LoRA applied (scale={scale})")
           return True
       except Exception:
           # Fallback: manual load
           logger.warning("Diffusers load_lora_weights failed, trying manual load")
           return apply_lora_manual(pipe, lora_path, scale)
   
   def apply_lora_manual(pipe, lora_path: str, scale: float):
       """Manual LoRA application via safetensors."""
       from safetensors import safe_open
       
       with safe_open(lora_path, framework="pt", device="cuda") as f:
           state_dict = {k: f.get_tensor(k) for k in f.keys()}
       
       # Apply to UNet and text encoder
       _apply_lora_to_model(pipe.unet, state_dict, scale)
       _apply_lora_to_model(pipe.text_encoder, state_dict, scale)
   ```

5. **Unfuse LoRA (CRÍTICO)**:
   ```python
   def unfuse_lora(pipe: StableDiffusionXLPipeline):
       """Remove LoRA weights to reset model state."""
       try:
           pipe.unfuse_lora()
           logger.info("LoRA unfused")
       except AttributeError:
           logger.debug("unfuse_lora not available, attempting unload")
           try:
               pipe.unload_lora_weights()
           except:
               logger.warning("Could not fully unload LoRA")
   ```

### ¿Por qué presigned URLs?

- ✅ **Seguridad**: No expone credenciales R2 al Modal worker
- ✅ **Tiempo limitado**: URL válida solo 15 minutos (si falla, se intenta de nuevo)
- ✅ **Escalable**: el worker no necesita conocer R2 credentials
- ✅ **Standard**: AWS S3 compatible, funciona en todos lados

---

## Variables de Entorno

### Backend (.env)

```bash
# Modal SDXL LoRA Configuration
LORA_PROVIDER=modal_sdxl_lora                                # Provider selector
MODAL_ENDPOINT_URL=https://modal-app.modal.run/generate-image  # Modal HTTP endpoint
MODAL_API_TOKEN=<token-if-required>                          # Modal auth token (opcional)

# Modal async polling (si usas async tasks)
MODAL_POLL_SECONDS=2
MODAL_TIMEOUT_SECONDS=300

# R2 (Required for presigned URLs)
R2_ACCESS_KEY_ID=<key>
R2_SECRET_ACCESS_KEY=<secret>
R2_BUCKET_NAME=vixenbliss-creator
R2_ENDPOINT_URL=https://1b25234e908e6f431171a26744700241.r2.cloudflarestorage.com
R2_PUBLIC_URL=https://pub-a8fbe8295aac44d384c00952267b9f54.r2.dev

# Database (for LoRA metadata)
DATABASE_URL=postgresql://user:pass@host:5432/db

# Fallback provider (if Modal fails)
REPLICATE_API_TOKEN=<token>
```

### Modal (environment secrets)

```bash
# Set in Modal dashboard or via modal.Volume for caching

# Optional: HuggingFace token (if model requires it)
HUGGINGFACE_HUB_TOKEN=<hf_token>

# Optional: model caching path
HF_HOME=/root/.cache/huggingface
```

---

## Ejemplos Prácticos

### Ejemplo 1: Request simple (base SDXL sin LoRA)

```python
# backend/app/api/content.py
import httpx

async def generate_base_image(prompt: str):
    """Generate image without LoRA."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://modal-app.modal.run/generate-image",
            json={
                "prompt": prompt,
                "negative_prompt": "low quality",
                "steps": 28,
            },
            timeout=60.0,
        )
        response.raise_for_status()
        return response.json()

# Call:
result = await generate_base_image("a beautiful landscape")
# {
#   "image_base64": "iVBORw0KGgo...",
#   "generation_time_seconds": 8.2,
#   ...
# }
```

### Ejemplo 2: Request con LoRA (el caso normal)

```python
# backend/app/api/content.py
from app.services.storage import storage_service

async def generate_with_lora(avatar_id: str, prompt: str, seed: int = None):
    """Generate image with avatar-specific LoRA."""
    
    # 1. Get avatar + LoRA
    avatar = await db.query(Avatar).filter_by(id=avatar_id).first()
    lora = await db.query(LoRAModel).filter_by(id=avatar.lora_model_id).first()
    
    # 2. Get presigned URL
    presigned_url = storage_service.generate_presigned_url(
        file_path=lora.r2_path,
        expiration_seconds=900,
    )
    
    # 3. Call Modal
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://modal-app.modal.run/generate-image",
            json={
                "prompt": f"{avatar.base_prompt} {prompt}",
                "negative_prompt": avatar.negative_prompt,
                "lora_url": presigned_url,
                "lora_scale": avatar.lora_scale or 0.9,
                "seed": seed,
                "steps": 28,
            },
            timeout=60.0,
        )
        response.raise_for_status()
        data = response.json()
    
    # 4. Process response
    image_bytes = base64.b64decode(data["image_base64"])
    
    # 5. Save to R2 (optional)
    image_url = storage_service.upload_file(
        file_content=image_bytes,
        file_path=f"content/{avatar_id}/{uuid.uuid4()}.png",
        content_type="image/png",
    )
    
    # 6. Save metadata
    content = ContentPiece(
        avatar_id=avatar_id,
        lora_id=lora.id,
        image_url=image_url,
        generation_time=data["generation_time_seconds"],
        parameters={
            "prompt": avatar.base_prompt + " " + prompt,
            "lora_scale": avatar.lora_scale,
            "seed": seed,
        },
    )
    db.add(content)
    db.commit()
    
    return {"image_url": image_url, "id": content.id}
```

### Ejemplo 3: Batch generation (múltiples imágenes)

```python
# backend/app/api/content.py
import asyncio

async def generate_batch(avatar_id: str, prompts: List[str], count: int = 3):
    """Generate multiple images for same avatar."""
    
    tasks = []
    for prompt in prompts:
        for i in range(count):
            seed = random.randint(0, 2**32 - 1)
            task = generate_with_lora(avatar_id, prompt, seed)
            tasks.append(task)
    
    # Run concurrently (max 3-5 concurrent to avoid rate limits)
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    return [r for r in results if not isinstance(r, Exception)]
```

---

## Error Handling

### Casos de Error Comunes

**1. LoRA presigned URL expirada o inválida**:
```python
# Modal worker recibe:
lora_url = "https://...?X-Amz-Signature=expires"
# ↓
# requests.get(lora_url) → 403 Forbidden (expired)

# Respuesta Modal:
{
    "error": "Failed to download LoRA",
    "error_code": "LORA_DOWNLOAD_FAILED",
    "details": "HTTP 403 Forbidden - presigned URL expired"
}

# Backend retry: solicita nueva presigned URL y reintenta
```

**2. LoRA incompatible con SDXL**:
```python
# LoRA fue entrenado para Stable Diffusion 1.5 (no SDXL)
# Modal intenta apply_lora → erro de shapes

# Respuesta Modal:
{
    "error": "LoRA shape mismatch",
    "error_code": "LORA_LOAD_FAILED",
    "details": "Expected shape (1024,) got (512,)"
}

# Backend: retorna error al frontend, guarda fallo en DB
```

**3. Timeout (generación tardía)**:
```python
# Generación toma >60s
# httpx timeout dispara

# Backend captura:
except httpx.TimeoutException:
    logger.error("Modal generation timeout")
    # Retry o fallback a otro provider (Replicate)
    return await fallback_generate_with_replicate(...)
```

**4. GPU OOM (out of memory)**:
```python
# Usuario solicita resolution 1536x1536 en L40S (24GB)
# torch.cuda.OutOfMemoryError durante inference

# Respuesta Modal:
{
    "error": "CUDA out of memory",
    "error_code": "CUDA_OOM",
    "details": "Requested 0.00 GiB, available 1.23 GiB"
}

# Backend: retry una o dos veces, luego failed
```

---

## Performance & Scaling

### Timing (caso normal)

```
Cold start (first request):
├─ Download SDXL model:     25-30s
├─ Compile/optimize:         5-10s
├─ Total cold start:         30-40s

Warm start (cached model):
├─ Download LoRA:             3-5s
├─ Apply LoRA:                1-2s
├─ Inference (28 steps):      8-12s
├─ Encode base64:             0.5s
├─ Total warm:                8-15s
```

### Concurrency Limits

```python
# Modal default: 1 concurrent request per worker
# Recommendation: use Modal's autoscaling

# In Modal app:
@app.function(
    gpu="A100",
    concurrency_limit=2,  # 2 requests per worker
    max_inputs_per_batch=1,
    timeout=300,
)
def generate_image(...):
    pass

# Backend should:
# - NOT fire more than 5-10 concurrent requests
# - Implement exponential backoff on 429 (rate limit)
```

### Cost Estimation

```
L40S GPU (24GB VRAM):
├─ Per second: $0.001 (while running)
├─ Per image (12s warm):  ~$0.0012
├─ Per image (38s cold):  ~$0.038

If generates 1000 images/day:
├─ Warm runs:    900 × 12s × $0.001 = $10.80
├─ Cold starts:   100 × 38s × $0.001 = $3.80
├─ Total/day:    ~$14.60
├─ Total/month:  ~$438
```

---

## Prompt para Codex

Copia-pega esto a Codex en tu otro repo Modal:

```
I need to build a Modal serverless app for SDXL + dynamic LoRA loading.

## Requirements

1. HTTP endpoint (GET /health, POST /generate-image)
2. Cache base SDXL model in memory (warm workers)
3. Per-request LoRA loading from presigned R2 URLs
4. LoRA unfuse after each generation (prevent model contamination)
5. Return PNG as base64 JSON

## Request Contract

POST /generate-image
{
  "prompt": "string",
  "negative_prompt": "string (optional)",
  "lora_url": "string (presigned URL, optional)",
  "lora_scale": "float (0.0-1.0, optional, default 1.0)",
  "width": "int (512-1536, default 1024)",
  "height": "int (512-1536, default 1024)",
  "steps": "int (20-50, default 28)",
  "cfg": "float (1.0-20.0, default 5.5)",
  "seed": "int (optional)"
}

## Response Contract

Success (200):
{
  "image_base64": "iVBORw0KGgo...",
  "image_size": [1024, 1024],
  "generation_time_seconds": 8.5,
  "model_info": {
    "base_model": "stabilityai/stable-diffusion-xl-base-1.0",
    "lora_applied": true/false,
    "lora_scale": 0.9
  }
}

Error (4xx/5xx):
{
  "error": "error message",
  "error_code": "ERROR_TYPE",
  "details": "traceback (optional)"
}

## Key Implementation Details

- Use diffusers.StableDiffusionXLPipeline
- Load LoRA via pipe.load_lora_weights(lora_path) + pipe.fuse_lora(scale)
- CRITICAL: Call pipe.unfuse_lora() after generation to prevent model pollution
- Download LoRA with requests.get(presigned_url)
- Keep model in GPU memory between requests (don't rebuild)
- Handle CUDA OOM gracefully
- Log all steps with timestamps
- Timeout: max 300 seconds per request

## Tech Stack

- Modal (@modal.app)
- diffusers >= 0.24.0
- torch >= 2.0.0
- peft >= 0.7.0 (for manual LoRA if needed)
- safetensors >= 0.4.0
- requests >= 2.31.0
- Pillow >= 10.0.0

## Backend Integration

The backend (FastAPI, separate repo) will:
1. Generate presigned R2 URLs for LoRAs
2. POST JSON to this endpoint
3. Decode image_base64 response
4. Save to R2 and DB
5. Return URL to frontend

You only need to implement the HTTP endpoint and image generation logic.

## Validation

Before deploying:
1. python -m py_compile your_app.py
2. Test local: modal run your_app.py::function()
3. Test HTTP endpoint: modal serve your_app.py (if available)
4. Check logs/errors in Modal dashboard

## Deployment

1. Create repo: modal-sdxl-lora (or similar)
2. modal.toml at root:
   [project]
   name = "modal-sdxl-lora"
3. modal deploy your_app.py
4. Copy endpoint URL → paste in backend .env as MODAL_ENDPOINT_URL
5. Backend tests will validate end-to-end
```

---

## Debugging Checklist

| Síntoma | Causa Probable | Solución |
|---------|---|---|
| 403 on LoRA download | Presigned URL expirada | Backend aumenta TTL, reintenta |
| LoRA fuse fails silently | Versión diffusers incompatible | Update diffusers, check LoRA format |
| Model generates same image 2x | LoRA no se unfusó | Add explicit unfuse_lora() in finally |
| Generation very slow (>20s) | Cold start (model loading) | Modal caches, warm workers faster |
| CUDA OOM | Resolution demasiada alta | Reduce width/height, o upgrade GPU |
| 504 Gateway | Timeout en backend | Increase MODAL_TIMEOUT_SECONDS |
| image_base64 decode fails | Invalid base64 encoding | Modal: ensure PNG → base64 correct |
| Different images same seed | LoRA contamination | Modal: unfuse LoRA properly |

---

## Next Steps

1. ✅ Send this doc to Codex in Modal repo
2. ✅ Codex implements the HTTP endpoint
3. ✅ Update backend `.env` with `MODAL_ENDPOINT_URL`
4. ✅ Update `backend/app/services/lora_inference.py` to use Modal provider
5. ✅ Run `backend/test_runpod_integration.py` (or rename to test_modal_integration.py)
6. ✅ Test end-to-end: frontend → backend → Modal → image generated

---

**Created**: 2026-02-11  
**Status**: Ready for Codex implementation  
**Priority**: HIGH - this is the contract / spec
