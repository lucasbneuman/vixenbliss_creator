# System 2: Content Production Flow & Reference Guide

**Status**: ✅ Tested & Optimized (Feb 13, 2026)  
**Last Updated**: Feb 13, 2026  
**Owner**: Engineering  
**Related**: [System 2 Optimization Guide](./SYSTEM_2_OPTIMIZATION.md) | [API Contracts](../api-contracts/v1_endpoints.md)

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture & Components](#architecture--components)
3. [Runtime Flow (End-to-End)](#runtime-flow-end-to-end)
4. [API Endpoints Reference](#api-endpoints-reference)
5. [Database Models](#database-models)
6. [Provider Chain & Fallbacks](#provider-chain--fallbacks)
7. [Performance & Optimization](#performance--optimization)
8. [Troubleshooting & Error Codes](#troubleshooting--error-codes)
9. [Dependency on System 1](#dependency-on-system-1)
10. [Configuration & Environment](#configuration--environment)

---

## System Overview

**System 2** (Content Production) is responsible for generating, processing, and storing AI-generated content (images, videos) for avatars trained in System 1. It serves as the revenue-generating engine for the vixenbliss application.

### Key Responsibilities

- 🎬 **Image Generation**: SDXL + fine-tuned LoRA weights → professional-quality content
- 🏷️ **Metadata Creation**: Hooks, captions, safety ratings, tier classifications
- 🔒 **Safety Compliance**: Content moderation, explicit content classification
- 💾 **Storage & Delivery**: Persist to R2, serve via CDN
- 📊 **Analytics**: Track generation costs, performance metrics
- ⚡ **Async Processing**: Batch generation via Celery for scalability

### Metrics

- **Cost per image**: $0.01 (Modal) / $0.01-0.05 (Replicate fallback)
- **Generation time**: 5-15 seconds per image (ComfyUI avg 2-3s, Modal 10-15s)
- **Batch sizes**: 5-50 (default) to 100+ (bulk)
- **Concurrency**: 3-10 parallel generations (provider-dependent)
- **Max throughput**: ~400 images/hour/avatar (with ComfyUI)
- **Cache hit rate**: >90% for template lookups
- **Health check**: `GET /api/v1/content/health` for monitoring

---

## Architecture & Components

### High-Level Flow

```
Client Request
    ↓
[/api/v1/content/*] FastAPI Endpoint
    ↓
{Auth, Validation, Avatar lookup}
    ↓
[LoRA Inference Engine] — Multi-provider router
    ├─ Primary: Modal SDXL LoRA (serverless)
    ├─ Secondary: ComfyUI (optional local)
    └─ Fallback: Replicate (external API)
    ↓
[Batch Processor] — Orchestrates pipeline
    ├─ Step 1: Template Selection
    ├─ Step 2: Image Generation (parallel)
    ├─ Step 3: Hook Generation (LLM)
    ├─ Step 4: Safety Check (moderation)
    ├─ Step 5: R2 Upload (storage)
    ├─ Step 6: Database Persistence
    └─ Step 7: Statistics
    ↓
[Response] → Client (JSON)
    ↓
[Celery Task] (async, optional) → Notification
```

### Services & Modules

| Module | Purpose | Status |
|--------|---------|--------|
| `lora_inference.py` | Multi-provider image generation router | ✅ Active |
| `batch_processor.py` | End-to-end pipeline orchestration | ✅ Active |
| `template_library.py` | 50+ pre-made content templates | ✅ Active |
| `hook_generator.py` | LLM-based caption/hook generation (Claude 3.5 or GPT-4) | ✅ Active |
| `content_safety.py` | OpenAI Moderation API integration | ✅ Active |
| `modal_sdxl_lora_client.py` | Modal serverless worker client | ✅ Active |
| `comfyui_client.py` | Local ComfyUI inference (optional) | ✅ Optional |
| `storage.py` | Cloudflare R2 / S3 upload manager | ✅ Active |
| `workers/tasks.py` | Celery async tasks | ✅ Active |

---

## Runtime Flow (End-to-End)

### 1️⃣ Single Image Generation: `POST /api/v1/content/generate`

**Request**:
```json
{
  "avatar_id": "uuid-here",
  "custom_prompt": "athletic woman in gym, professional lighting",
  "platform": "instagram",
  "tier": "capa1"
}
```

**Flow**:
```
1. Validate avatar exists
   └─ If not: HTTP 404

2. Check avatar.lora_weights_url is set
   └─ If empty: HTTP 400 "No trained LoRA weights"
   └─ (This is System 1 dependency!)

3. Get template OR use custom_prompt
   └─ Template: Load from in-memory library
   └─ Custom: Use prompt as-is

4. LoRA Inference Engine.generate_image_with_lora()
   └─ Inject trigger word: "{TOK_avatar_id}, {prompt}"
   └─ Try providers in order (modal → comfyui → replicate)
   └─ Return: {image_base64, generation_time, cost, parameters}

5. Convert image to data:image/png;base64 URL (if needed)
   └─ If no URL returned: HTTP 502 (generation failed)

6. Create ContentPiece in DB
   └─ avatar_id, content_type="image", access_tier, url, metadata

7. Return HTTP 200 + ContentPieceResponse
```

**Response** (HTTP 200):
```json
{
  "id": "uuid",
  "avatar_id": "uuid",
  "content_type": "image",
  "access_tier": "capa1",
  "url": "data:image/png;base64,iVBOR...",
  "hook_text": null,
  "safety_rating": null,
  "created_at": "2026-02-13T10:30:00Z",
  "metadata": {
    "generation_params": {...},
    "generation_time": 8.5,
    "cost": 0.01
  }
}
```

---

### 2️⃣ Batch Generation: `POST /api/v1/content/batch/sync`

**Request**:
```json
{
  "avatar_id": "uuid",
  "num_pieces": 50,
  "platform": "instagram",
  "include_hooks": true,
  "safety_check": true,
  "upload_to_storage": true,
  "tier_distribution": {
    "capa1_ratio": 0.6,
    "capa2_ratio": 0.3,
    "capa3_ratio": 0.1
  }
}
```

**Flow** (Synchronous):
```
BatchProcessor.process_batch(db, avatar, config)
  ├─ Step 1: Template Selection
  │   └─ Select 50 templates per tier distribution
  │   └─ Prioritize niche-specific templates
  │   └─ Log: "Selected {N} templates"
  │
  ├─ Step 2: Image Generation (Parallel, max 5 concurrent)
  │   └─ For each template:
  │       ├─ Generate with lora_inference_engine
  │       ├─ Log retry count + time per image
  │       └─ Create ContentPiece object (not persisted yet)
  │   └─ Semaphore(5) controls concurrency
  │   └─ Log: "Generated {N} images"
  │
  ├─ Step 3: Hook Generation (Optional, if include_hooks=true)
  │   └─ Call HookGenerator.generate_hooks() per piece
  │   └─ LLM: Claude 3.5 Sonnet (preferred) or GPT-4
  │   └─ 5 variations per piece
  │   └─ Log: "Generated hooks for {N} pieces"
  │
  ├─ Step 4: Safety Check (Optional, if safety_check=true)
  │   └─ Call ContentSafetyService.check_image_safety() per piece
  │   └─ Return: rating (safe/suggestive/borderline)
  │   └─ Auto-assign tier based on safety score
  │   └─ Log: "Safety check passed for {N} pieces"
  │
  ├─ Step 5: Storage Upload (Optional, if upload_to_storage=true)
  │   └─ Download image from temp URL
  │   └─ PUT to R2: content/{avatar_id}/{piece_id}.jpg
  │   └─ Update piece.url with CDN URL
  │   └─ Log: "Uploaded {N} pieces to R2"
  │
  ├─ Step 6: Database Persistence
  │   └─ db.add(piece) for each piece
  │   └─ db.commit()
  │   └─ Log: "Saved {N} pieces to DB"
  │
  └─ Step 7: Statistics
      └─ Count by tier, safety rating, cost
      └─ Return result dict
```

**Response** (HTTP 200):
```json
{
  "success": true,
  "avatar_id": "uuid",
  "total_pieces": 50,
  "content_pieces": [...],
  "statistics": {
    "tier_distribution": {
      "capa1": 30,
      "capa2": 15,
      "capa3": 5
    },
    "safety_distribution": {
      "safe": 48,
      "suggestive": 2,
      "borderline": 0
    },
    "total_cost": 0.50,
    "total_generation_time": 385.2
  },
  "config": {...}
}
```

---

### 3️⃣ Async Batch: `POST /api/v1/content/batch` (Celery)

**Request**: Same as `/batch/sync`

**Flow**:
```
FastAPI Endpoint
  └─ Enqueue Celery task: generate_content_batch()
  └─ Return immediately with task_id

Celery Worker (background)
  └─ Same as /batch/sync flow
  └─ Update task state: STARTED → progress 0% → 100% → COMPLETE
  └─ Store result in Redis/database

Frontend Poll
  └─ GET /api/v1/loras/training/status/{task_id}
  └─ Receive progress + final result
```

---

## API Endpoints Reference

### Content Generation

| Endpoint | Method | Purpose | Response |
|----------|--------|---------|----------|
| `/api/v1/content/generate` | POST | Generate single image | `ContentPieceResponse` |
| `/api/v1/content/batch` | POST | Async batch (Celery) | `{task_id, estimated_time_minutes, ...}` |
| `/api/v1/content/batch/sync` | POST | Sync batch | `BatchGenerationResponse` |
| `/api/v1/content/templates` | GET | List templates | `TemplateListResponse` |
| `/api/v1/content/templates/{id}` | GET | Get template detail | Template dict |
| `/api/v1/content/hooks` | POST | Generate hooks/captions | `HookGenerationResponse` |
| `/api/v1/content/safety-check` | POST | Check content safety | `SafetyCheckResponse` |
| `/api/v1/content/upload-batch` | POST | Upload to R2 | `{total_uploaded, total_failed, results[]}` |
| `/api/v1/content/avatar/{avatar_id}/content` | GET | List content for avatar | `ContentPieceResponse[]` |
| `/api/v1/content/stats/{avatar_id}` | GET | Content statistics | `{total_content, tier_distribution, ...}` |

### Status Codes

```
200 OK           → Success
400 Bad Request  → Avatar not found, missing LoRA, invalid request
404 Not Found    → Avatar/template not found
422 Unprocessable→ Validation error (invalid tier, num_pieces out of range)
502 Bad Gateway  → Generation failed, all providers exhausted
```

---

## Database Models

### ContentPiece

```python
id: UUID (primary key)
avatar_id: UUID (FK → Avatar.id, CASCADE delete)
content_type: str ["image", "video"]
access_tier: str ["capa1", "capa2", "capa3"]
url: str NOT NULL (R2 CDN URL or data:image;base64)
thumbnail_url: str (optional)
hook_text: str (optional, caption/hook)
safety_rating: str (optional ["safe", "suggestive", "borderline"])
explicitness_level: int (1-10, for premium content)
price_usd: float (optional, for premium packs)
meta_data: JSON {
    "generation_params": {...},
    "generation_time": 8.5,
    "cost": 0.01,
    "hooks": [...]
}
created_at: datetime (auto)
published_at: datetime (optional)
```

### Avatar Relations

```python
# In Avatar model
lora_weights_url: str NOT NULL (for System 2)
  Example: "https://r2.example.com/loras/avatar-id.safetensors"
  
meta_data: JSON {
    "personality": "...",
    "generation_config": {
        "steps": 28,
        "cfg_scale": 3.5,
        "scheduler": "euler"
    }
}

content_pieces: relationship (OneToMany)
```

---

## Provider Chain & Fallbacks

### Primary: Modal SDXL LoRA (Recommended)

- **Endpoint**: `${MODAL_ENDPOINT_URL}/api/v1/inference`
- **Auth**: `Authorization: Bearer ${MODAL_API_TOKEN}`
- **Timeout**: `${MODAL_TIMEOUT_SECONDS}` (default 300s)
- **Retries**: `${MODAL_MAX_RETRIES}` (default 3) with exponential backoff
- **Precondition**: LoRA weights must be accessible via presigned R2 URL
- **Cost**: ~$0.005-0.01 per image
- **Speed**: 8-12 seconds per image

**Retry logic**:
```python
MODAL_MAX_RETRIES = 3
MODAL_RETRY_BACKOFF_BASE = 1.0  # 1s, 2s, 4s
MODAL_TIMEOUT_SECONDS = 300
```

**Failure modes**:
- `LORA_DOWNLOAD_FAILED` → Retry (presigned URL expired?)
- `MODEL_LOAD_FAILED` → Try fallback
- `CUDA_OOM` → Try fallback (out of GPU memory)
- `TIMEOUT` → Retry with backoff

### Secondary: ComfyUI (Local, Optional)

- **Endpoint**: `http://comfyui:8188` (Docker internal)
- **Config**: `${COMFYUI_ENABLED}` (default false)
- **Speed**: 5-10 seconds (local, faster)
- **Cost**: $0 (runs on own hardware)

### Tertiary: Replicate (Fallback)

- **Endpoint**: `https://api.replicate.com/v1/predictions`
- **Auth**: `${REPLICATE_API_TOKEN}`
- **Model**: `black-forest-labs/flux-1.1-pro` (default, no LoRA support)
- **Cost**: ~$0.01-0.05 per image
- **Speed**: 15-20 seconds
- **Limitation**: No fine-tuned LoRA weights (uses generic FLUX model)

### Configuration

```bash
# Set primary provider
AI_IMAGE_PROVIDER=modal_sdxl_lora

# Set fallback chain
AI_IMAGE_PROVIDER_FALLBACKS="comfyui,replicate"

# Or use environment aliases
LORA_PROVIDER=modal_sdxl_lora
```

---

## Troubleshooting & Error Codes

### HTTP 400: "Avatar has no trained LoRA weights"

**Cause**: System 1 (avatar training) has not completed. Avatar exists but `lora_weights_url` is null.

**Resolution**:
1. Check avatar stage: should be "active" or "ready", not "training"
2. Verify System 1 workflow completed: check `avatars.lora_weights_url` in DB
3. If training failed, re-run System 1 training pipeline

```sql
SELECT id, name, stage, lora_weights_url FROM avatars WHERE id = 'uuid';
```

---

### HTTP 502: "Generation succeeded but no image URL/base64 returned"

**Cause**: Provider returned successfully but image URL is missing from response.

**Resolution**:
1. Check Modal worker logs: `modal logs -c app.workers.modal_sdxl_lora`
2. Verify LoRA weights are accessible: `curl -I https://r2.example.com/loras/avatar-id.safetensors`
3. Check provider returned valid response format
4. Fallback providers will be retried automatically

---

### HTTP 502: "Failed to upload to R2"

**Cause**: R2 credentials invalid or bucket not accessible.

**Resolution**:
1. Check env vars: `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_ENDPOINT_URL`, `R2_BUCKET_NAME`
2. Test R2 access:
   ```bash
   aws s3 ls s3://${R2_BUCKET_NAME} --endpoint-url ${R2_ENDPOINT_URL}
   ```
3. Check presigned URL TTL not too short (should be >generation time)

---

### Timeout: generation_time > 300 seconds

**Cause**: Modal worker unavailable or severely congested.

**Resolution**:
1. Check Modal dashboard for outages: https://modal.com/status
2. Increase `MODAL_TIMEOUT_SECONDS` (e.g. 600)
3. Check network connectivity from backend to Modal
4. Fallback to Replicate if Modal persistently fails

---

### Database: contentPiece has null `url`

**Cause**: Image generation succeeded but URL handling failed.

**Resolution**:
1. Check logs: "Generation succeeded but no image URL/base64 returned"
2. Verify response from LoRA provider includes `image_base64` OR `image_url`
3. If using base64, ensure < 100MB size (DB TEXT column limit)
4. For large batches, enable `upload_to_storage=true` to use R2 instead of base64

---

## Dependency on System 1

### ⚠️ Critical: System 1 Must Complete Before System 2

System 2 **blocks** if System 1 outputs are missing:

| System 1 Output | System 2 Check | If Missing |
|---|---|---|
| `avatars.lora_weights_url` (string) | NOT NULL check | ❌ HTTP 400 |
| Presigned R2 URL validity | Download test | ❌ HTTP 502 |
| Avatar stage="active" | Implicit | ⚠️ May cause issues |

### Expected System 1 → System 2 Data Flow

```
System 1 Output (Avatar Training Complete)
    ├─ Avatar.lora_weights_url = "https://r2.../lora/avatar-id.safetensors"
    ├─ Avatar.stage = "active"
    ├─ Avatar.meta_data.generation_config = {...}
    └─ LoRA weights file accessible at R2 URL
         ↓
    System 2 Input (Content Generation Starts)
        └─ Load lora_weights_url
        └─ Pass to Modal SDXL LoRA worker
        └─ Generate images with fine-tuned weights
```

### Validation Script

```bash
# Check if System 1 outputs ready
sqlite3 app.db << EOF
SELECT 
    id, name, stage, LENGTH(lora_weights_url) as url_len, 
    CASE WHEN lora_weights_url IS NULL THEN '❌ BLOCKED' ELSE '✅ READY' END as status
FROM avatars
WHERE user_id = '${USER_ID}';
EOF
```

---

## Configuration & Environment

### Required Environment Variables

```bash
# Modal SDXL LoRA Provider
MODAL_API_TOKEN=<api-key>
MODAL_ENDPOINT_URL=https://api.modal.com/v1/functions/<endpoint-id>
MODAL_TIMEOUT_SECONDS=300
MODAL_MAX_RETRIES=3

# Cloudflare R2 Storage
R2_ACCESS_KEY_ID=<key>
R2_SECRET_ACCESS_KEY=<secret>
R2_ENDPOINT_URL=https://account-id.r2.cloudflarestorage.com
R2_BUCKET_NAME=vixenbliss-content
R2_PUBLIC_URL=https://cdn.example.com  # CDN domain

# OpenAI (for safety check & hook generation fallback)
OPENAI_API_KEY=<key>

# Anthropic (Claude for hook generation, preferred)
ANTHROPIC_API_KEY=<key>

# Replicate (fallback image generation)
REPLICATE_API_TOKEN=<token>

# Celery (async tasks)
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
```

### Optional Environment Variables

```bash
# Provider override
AI_IMAGE_PROVIDER=modal_sdxl_lora
AI_IMAGE_PROVIDER_FALLBACKS=comfyui,replicate

# ComfyUI (local inference, optional)
COMFYUI_ENABLED=false
COMFYUI_ENDPOINT=http://comfyui:8188

# Testing & debugging
SKIP_MODAL_TESTS=false  # Set true to skip real API tests
ENABLE_REPLICATE_FALLBACK=true
```

### Database Migrations

```sql
-- Ensure content_pieces table exists
CREATE TABLE IF NOT EXISTS content_pieces (
    id CHAR(36) PRIMARY KEY,
    avatar_id CHAR(36) NOT NULL,
    content_type VARCHAR(50) NOT NULL,
    access_tier VARCHAR(20) NOT NULL DEFAULT 'capa1',
    url TEXT NOT NULL,
    thumbnail_url TEXT,
    hook_text TEXT,
    safety_rating VARCHAR(20),
    explicitness_level INT,
    price_usd FLOAT,
    meta_data JSON DEFAULT '{}',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    published_at DATETIME,
    FOREIGN KEY(avatar_id) REFERENCES avatars(id) ON DELETE CASCADE,
    INDEX idx_avatar_id (avatar_id),
    INDEX idx_access_tier (access_tier)
);
```

---

## Testing & Validation

### Unit Tests (No External APIs)

```bash
pytest backend/tests/test_content_generation_mock.py -v
# 10+ tests covering error cases, schema validation, mocked providers
```

### Smoke Tests (Real APIs)

```bash
# Requires MODAL_API_TOKEN, R2 credentials, etc.
pytest backend/tests/test_content_generation_smoke.py -v

# Or skip external tests
SKIP_MODAL_TESTS=true pytest backend/tests/test_content_generation_smoke.py -v
```

### Health Check

```bash
curl http://localhost:8000/health
```

---

## Related Documentation

- **System 1 (Identities)**: [docs/context/README.md](../context/README.md)
- **API Contracts**: [docs/api-contracts/v1_endpoints.md](../api-contracts/v1_endpoints.md)
- **External Systems**: [docs/external-systems/modal-sdxl-lora.md](../external-systems/modal-sdxl-lora.md)
- **Governance**: [docs/context/governance.md](../context/governance.md)
- **Architecture**: [docs/SYSTEM_MAP.md](../SYSTEM_MAP.md)

---

## FAQ

**Q: What happens if Modal is down?**  
A: Automatic failover to ComfyUI (if enabled) or Replicate. User receives HTTP 502 only if all providers exhaust retries.

**Q: Can I generate content without hooks/safety checks?**  
A: Yes, set `include_hooks=false` and `safety_check=false` for faster generation (skip LLM and moderation).

**Q: Why is my image all black/corrupted?**  
A: Usually indicates LoRA weights file is invalid or corrupted. Verify file exists at lora_weights_url and is accessible.

**Q: How do I monitor batch generation progress?**  
A: Poll `/api/v1/loras/training/status/{task_id}` (returns progress 0-100%) for async batches.

**Q: Can I customize the tier distribution?**  
A: Yes, use `tier_distribution` param: `{"capa1_ratio": 0.6, "capa2_ratio": 0.3, "capa3_ratio": 0.1}`

---

**End of documentation**  
For issues or updates, refer to [docs/BUGS.md](../BUGS.md) or [docs/TASK.md](../TASK.md)
