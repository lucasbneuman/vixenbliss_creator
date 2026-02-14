# System 2 Optimization & Best Practices Guide

**Version**: 1.0  
**Last Updated**: 2026-02-13  
**Owner**: Engineering Team  

---

## Table of Contents

1. [Performance Tuning](#performance-tuning)
2. [Cost Optimization](#cost-optimization)
3. [Database Optimization](#database-optimization)
4. [Caching Strategy](#caching-strategy)
5. [Error Handling & Resilience](#error-handling--resilience)
6. [Monitoring & Observability](#monitoring--observability)
7. [Batch Processing Guidelines](#batch-processing-guidelines)
8. [Common Issues & Solutions](#common-issues--solutions)

---

## Performance Tuning

### Batch Size Selection

**Optimal Batch Sizes**:
- **Small batches (5-10 pieces)**: Fast feedback, higher per-piece cost
  - Use case: Real-time generation requests
  - Latency: ~10-20s per batch
  - Cost: ~$0.10-0.20 per batch

- **Medium batches (20-50 pieces)**: Balanced throughput & cost
  - Use case: Scheduled daily/weekly content production
  - Latency: ~2-5 min per batch
  - Cost: ~$0.30-0.80 per batch
  - **Recommended default**: 50 pieces

- **Large batches (100+ pieces)**: Maximum efficiency, longer wait
  - Use case: Bulk content generation (monthly archival)
  - Latency: ~10-20 min per batch
  - Cost: ~$1.50-2.00 per batch

**Decision Tree**:
```
Is real-time response needed?
  → YES: Use small batch (5-10)
  → NO: Is weekly production? → small batch (20)
         Is monthly production? → large batch (100+)
         Default: Medium batch (50)
```

### Concurrent Request Handling

**Concurrency Limits**:
- **Modal SDXL LoRA**: Max 5 concurrent requests (timeout: 300s each)
- **ComfyUI**: Max 10 concurrent requests (local, fast)
- **Replicate**: Max 20 concurrent requests (rate-limited)

**Strategy**:
```python
# Recommended concurrency per provider
MAX_CONCURRENT = {
    "modal": 3,        # Conservative due to cost
    "comfyui": 10,     # Local, can afford higher
    "replicate": 5     # Fallback, rate-limited
}

# Batch 50 images: Split into 5 groups of 10
# Each group attempts: ComfyUI (10 parallel) → Modal (3 parallel) → Replicate (5 parallel)
```

### Provider Chain Tuning

**Current Provider Sequence**:
1. **ComfyUI** (0-2s, free, local)
2. **Modal SDXL LoRA** (10-15s, $0.01/image, high quality)
3. **Replicate FLUX** (8-12s, $0.01-0.05, fallback)

**Optimization Recommendations**:

- **For speed**: Enable ComfyUI for batch generation
  ```bash
  export COMFYUI_ENABLED=true
  export COMFYUI_ENDPOINT=http://localhost:8188
  ```

- **For quality**: Prioritize Modal, use Replicate as fallback
  ```bash
  export LORA_INFERENCE_PROVIDER_ORDER=modal,replicate
  ```

- **For cost**: Check ComfyUI first, fall back to cheapest option
  ```bash
  export PROVIDER_STRATEGY=cost-optimized
  ```

**Timing Analysis** (from lora_inference.py logs):
```
ComfyUI attempt #1: 0-2s (expected to succeed 70% of time)
Modal attempt #2:   10-15s (expected to succeed 99% of time)
Replicate attempt #3: 8-12s (fallback)

Total time for 1 image: ~2-15s (most succeed in <3s via ComfyUI)
Parallel generation of 50: ~5-7 min (assuming 10 concurrent ComfyUI)
```

---

## Cost Optimization

### Cost Breakdown (per 50-piece batch)

| Component | Cost | Optimizable |
|-----------|------|------------|
| Image Generation (Modal) | $0.50 | ✅ Use ComfyUI when available |
| Hook Generation (Claude) | $0.10-0.20 | ✅ Batch together, cache templates |
| Safety Check (OpenAI) | $0.05 | ✅ Batch operations, skip for low-risk |
| Storage Upload (R2) | $0.01 | N/A (minimal) |
| **Total** | **$0.66-0.76** | - |

### Cost Reduction Strategies

**1. ComfyUI First Approach** (-50% image cost)
```python
# Enable local ComfyUI for free inference
# Saves $0.25 per 50-piece batch
COMFYUI_ENABLED=true
COMFYUI_FALLBACK_ON_ERROR=true
```

**2. Hook Generation Batching** (-20% hook cost)
```python
# Instead of 50 individual calls, batch into 5 calls of 10
await hook_generator.batch_generate_hooks(
    items=50,
    batch_size=10  # Reduces API calls from 50 to 5
)
```

**3. Safety Check Optimization** (-30% safety cost)
```python
# Skip safety check for known-safe content categories
SKIP_SAFETY_CHECK_CATEGORIES = ["fitness", "lifestyle"]

# Or: Sample-based checking (check 20% of content)
SAFETY_CHECK_SAMPLE_RATE = 0.2  # Check only 10 of 50 pieces
```

**4. Template Reuse** (-15% LLM cost)
```python
# Cache template descriptions, reuse in hook generation
# Built-in caching via @lru_cache in template_library
# Cache stats: /api/v1/content/health → cache_performance
```

**Monthly Savings Example**:
```
Baseline: 50 batches × $0.76 = $38/month
- ComfyUI: 50 × $0.26 = $13
- Hook batching: 50 × $0.76 × 0.8 = $30.40
- Safety sampling: 50 × $0.76 × 0.7 = $26.60
- Total with all optimizations: ~$13-20/month (50-60% savings)
```

---

## Database Optimization

### Query Performance

**Current Query Patterns** (from content.py):
- Avatar lookup: `select(Avatar).where(Avatar.id == id_value)` - O(1) with index
- Content listing: `select(ContentPiece).where(ContentPiece.avatar_id == id)` - O(n) batch
- Stats calculation: `func.count()` aggregations - O(n) scan

**Indexes to Create**:
```sql
-- Already defined in schema
CREATE INDEX idx_content_piece_avatar_id ON content_piece(avatar_id);
CREATE INDEX idx_content_piece_access_tier ON content_piece(access_tier);
CREATE INDEX idx_content_piece_safety_rating ON content_piece(safety_rating);

-- Additional recommended indexes for analytics
CREATE INDEX idx_content_piece_created_at ON content_piece(created_at);
CREATE INDEX idx_content_piece_avatar_created ON content_piece(avatar_id, created_at);
```

**Query Optimization Tips**:

1. **Prefer aggregations over in-app counting**:
   ```python
   # FAST: Database handles counting
   count = db.execute(
       select(func.count()).select_from(ContentPiece).where(
           ContentPiece.avatar_id == avatar_id,
           ContentPiece.access_tier == "capa1"
       )
   ).scalar()

   # SLOW: Fetch all, count in Python
   pieces = db.query(ContentPiece).filter(...).all()
   count = len(pieces)
   ```

2. **Limit result sets**:
   ```python
   # For listing endpoints, always paginate
   from sqlalchemy import limit, offset
   
   stmt = select(ContentPiece).where(
       ContentPiece.avatar_id == avatar_id
   ).order_by(ContentPiece.created_at.desc()).limit(20).offset((page-1)*20)
   ```

3. **Batch status updates**:
   ```python
   # Instead of updating one by one
   for piece in pieces:
       piece.status = "processed"
       db.commit()  # BAD: N commits

   # Use bulk update
   from sqlalchemy import update
   db.execute(
       update(ContentPiece)
       .where(ContentPiece.id.in_([p.id for p in pieces]))
       .values(status="processed")
   )
   db.commit()  # Good: 1 commit
   ```

### Connection Pooling

**Current Configuration** (database.py):
```python
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,           # Active connections
    max_overflow=10        # Extra connections under load
)
```

**For High Concurrency**:
```python
# Increase pool if seeing connection exhaustion errors
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,          # More active connections
    max_overflow=20,       # More extra connections
    pool_recycle=3600      # Recycle connections after 1 hour
)
```

---

## Caching Strategy

### Template Library Cache

**Status**: Built-in LRU caching with statistics

**Cache Metrics** (from `/api/v1/content/health`):
```json
{
  "template_library": {
    "cache_performance": {
      "total_calls": 1245,
      "cache_hits": 1198,
      "cache_misses": 47,
      "hit_rate_percent": 96.23
    }
  }
}
```

**How It Works**:
- All template retrieval methods cached via `@lru_cache`
- Cache size: 128 for all templates, 64 per category, 50 by ID, 32 per avatar
- Automatic TTL: None (persistent for session)
- Clear command: `template_library.clear_cache()`

**Cache Hit Scenarios**:
- Same niche requested multiple times: ~100% cache hits
- Batch generation of 50 pieces: ~95% cache hits (template selection cached)
- Template filter by category: ~90% cache hits

### Response Caching

**Recommended** (add to content endpoints):
```python
from fastapi_cache2 import FastAPICache2
from fastapi_cache2.backends.redis import RedisBackend

# Cache health check response for 5 minutes
@router.get("/health")
@cached(expire=300)  # 5 minutes
async def system_2_health_check(db: Session = Depends(get_db)):
    # Endpoint implementation
    pass

# Cache template list for 1 hour (changes infrequently)
@router.get("/templates")
@cached(expire=3600)  # 1 hour
async def get_templates(category: Optional[str] = None):
    # Endpoint implementation
    pass
```

**Cache Invalidation**:
```python
# Clear cache when templates are updated
async def update_templates():
    await template_library.clear_cache()
    await FastAPICache2.clear()  # Clear HTTP response cache
```

---

## Error Handling & Resilience

### Retry Strategy

**Current Provider Chain** (automatic retries):
1. ComfyUI: No retry (fast, stateless)
2. Modal SDXL: Retry 3x (important provider)
3. Replicate: Retry 2x (fallback)

**Configuration** (lora_inference.py):
```python
RETRY_CONFIG = {
    "modal": {
        "max_attempts": 3,
        "backoff_factor": 1.5,  # Wait 1.5s, 2.25s, 3.37s
        "timeout": 300
    },
    "replicate": {
        "max_attempts": 2,
        "backoff_factor": 2.0,
        "timeout": 60
    }
}
```

### Circuit Breaker Pattern

**Implement for critical failures**:
```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
async def modal_generate_image(prompt, avatar_id):
    """Open circuit after 5 failures, close after 60s"""
    return await modal_client.generate(prompt, avatar_id)

# This prevents cascading failures:
# - 5 failures in quick succession → circuit opens
# - All subsequent requests fail immediately (fast fail)
# - After 60s, circuit closes and tries recovery
```

### Graceful Degradation

**Content Generation Tiers**:

| Tier | Quality | Cost | Fallback |
|------|---------|------|----------|
| 1 (Ideal) | Modal SDXL + Hook + Safety | $0.76 | ✅ Replicate + basic hook |
| 2 (Degraded) | Replicate only | $0.20 | ✅ Cached template images |
| 3 (Critical) | Cached assets | $0.01 | ❌ Service unavailable (HTTP 503) |

**Strategy**:
```python
async def generate_with_fallback(prompt, avatar_id):
    # Tier 1: Try ideal path
    try:
        return await batch_processor.process_batch(...)
    except ModalTimeoutError:
        logger.warning("Modal timeout, attempting Tier 2 (Replicate)")
    
    # Tier 2: Try fallback provider
    try:
        return await fallback_generate_image(prompt)
    except Exception as e:
        logger.error("Tier 2 failed, using cached assets")
    
    # Tier 3: Serve cached/template content
    return get_cached_content_for_avatar(avatar_id)
```

### Timeout Configuration

**Critical Timeouts** (should not exceed):
```
Batch generation of 50 pieces: 15 min max
├─ Template selection: 1s
├─ Image generation: 10 min (10 images × 60s avg)
├─ Hook generation: 2 min
├─ Safety check: 1 min
├─ Storage upload: 1 min
└─ DB save: 30s
```

**Implementation**:
```python
from fastapi import BackgroundTasks

# Sync endpoint should timeout after 30s
@router.post("/batch/sync", timeout=30.0)
async def generate_batch_sync(...):
    # Must complete within 30s or return HTTP 504

# Async endpoint with background task
@router.post("/batch")  # No sync timeout
async def generate_batch_async(background_tasks: BackgroundTasks, ...):
    # Start task, return immediately
    background_tasks.add_task(batch_processor.process_batch, ...)
    return {"task_id": "...", "status": "queued"}
```

---

## Monitoring & Observability

### Key Performance Indicators (KPIs)

**Real-time Metrics** (from logs with grep):
```bash
# Image generation performance
grep "STEP 2/7.*Image Generation" logs/app.log | \
  grep -oP "Duration: \K[0-9.]+" | \
  awk '{sum+=$1; count++} END {print "Avg:", sum/count "s"}'

# Hook generation success rate
grep "Hook generation summary" logs/app.log | \
  grep -oP "Success: \K[0-9]+(?=/)" | \
  awk '{sum+=$1} //{sum2++} END {print "Success rate:", sum/(sum+sum2)*100 "%"}'

# Safety check rejection rate
grep "Safety check summary" logs/app.log | \
  grep -oP "Rejected: \K[0-9]+(?=/)"
```

**Health Check Endpoint**:
```bash
curl http://localhost:8000/api/v1/content/health | jq

# Response includes:
# - Database status & counts
# - Template cache hit rate (>90% is good)
# - Provider availability
# - R2 storage configuration
```

### Structured Logging

**Log Levels Used**:
- `logger.debug()`: Detailed step-by-step progress (batch steps 1-7)
- `logger.info()`: High-level events (batch start/complete)
- `logger.warning()`: Recoverable issues (hook generation fail, tier mismatch)
- `logger.error()`: Blocking errors (database fail, upload fail)

**Example Log Pattern** (batch_processor.py):
```
[BATCH START] Avatar: a1b2c3d4, Pieces: 50, Platform: instagram
[STEP 1/7] Template Selection | Selected: 50 | Duration: 0.15s
[STEP 2/7] Image Generation | Generated: 50 | Duration: 285.42s | Avg per image: 5.71s
[STEP 3/7] Hook Generation | Generated: 48/50 | Duration: 15.23s
[STEP 4/7] Safety Check | Passed: 48, Rejected: 2 | Duration: 8.51s
[STEP 5/7] Storage Upload | Uploaded: 48/50 to R2 | Duration: 12.34s
[STEP 6/7] Database Save | Saved: 48 | Duration: 2.15s
[STEP 7/7] Statistics Calculation | Duration: 0.05s
[BATCH COMPLETE] Avatar: a1b2c3d4 | Total Duration: 328.15s | Pieces: 48 | Cost: $0.73
```

**Parsing for Analysis**:
```python
import re
from datetime import datetime

log_lines = open("app.log").readlines()
for line in log_lines:
    if "[BATCH COMPLETE]" in line:
        match = re.search(r"Duration: ([0-9.]+)s.*Pieces: (\d+).*Cost: \$([0-9.]+)", line)
        duration, pieces, cost = match.groups()
        print(f"Batch: {pieces} pieces in {float(duration)/60:.1f}min at ${cost}")
```

### Alert Thresholds

**Recommended Alert Configuration**:

| Metric | Threshold | Action |
|--------|-----------|--------|
| Batch duration | >600s (10min) | Warn: investigate delays |
| Provider success | <80% | Warn: check provider health |
| Database response | >5s | Error: connection pool issue |
| Cache hit rate | <50% | Debug: analyze query patterns |
| Hook generation errors | >10% | Warn: LLM service issue |
| Safety check rejections | >20% | Info: monitor content tier |

---

## Batch Processing Guidelines

### Optimal Workflow

```
User Request
    ↓
Validate (check avatar has lora_weights_url)
    ↓
Queue Batch Task (Celery)
    ↓
[ASYNC] Process Batch:
 1. Select templates (0.1-0.2s)
 2. Generate images (90% of time)
 3. Generate hooks (25-30s for 50)
 4. Safety check (15-20s for 50)
 5. Upload to R2 (10-15s for 50)
 6. Save to DB (0.1-0.3s)
 7. Calculate stats (0.05s)
    ↓
Callback: Store results, notify user
    ↓
Return: Task ID + status polling endpoint
```

### Tier Distribution Example

**For Lifestyle Avatar** (60% safe, 30% suggestive, 10% explicit):

```python
config = BatchProcessorConfig(
    num_pieces=50,
    tier_distribution={
        "capa1_ratio": 0.6,   # 30 safe pieces (fit for social media)
        "capa2_ratio": 0.3,   # 15 suggestive (premium subscribers)
        "capa3_ratio": 0.1    # 5 explicit (high-tier only)
    },
    platform=Platform.INSTAGRAM,
    include_hooks=True,       # Generate captions
    safety_check=True,        # Run OpenAI moderation
    upload_to_storage=True    # Persist to R2
)
```

### Custom Prompt Injection

**Important**: Custom prompts bypass template system
```python
# Custom prompts for maximum control
config = BatchProcessorConfig(num_pieces=5)
custom_prompts = [
    "close-up portrait, studio lighting, professional makeup",
    "athletic pose, gym environment, dynamic lighting",
    # ...
]
result = await batch_processor.process_batch(
    db, avatar, config, 
    custom_prompts=custom_prompts
)
```

**Risks**:
- No template-based safety guardrails
- LLM may misinterpret complex prompts
- No tier classification (defaults to capa1)

**Mitigation**:
```python
# Always run safety check with custom prompts
config.safety_check = True
# Manually specify tiers to override defaults
custom_tiers = ["capa2", "capa1", "capa3", ...]
```

---

## Common Issues & Solutions

### Issue 1: Slow Image Generation (>20s per image)

**Root Causes**:
1. Modal queue is backed up (many concurrent requests)
2. ComfyUI not available (falling back to slower provider)
3. LoRA weights not optimized

**Diagnosis**:
```bash
# Check logs for provider attempt timing
grep "provider_attempt" app.log | tail -20

# Check Avatar LoRA weights
curl http://localhost:8000/api/v1/avatars/{avatar_id} | \
  jq '.lora_weights_url'
```

**Solutions**:
1. Reduce batch size to avoid queue congestion
2. Enable ComfyUI if available
3. Use Replicate provider (cheaper, same speed)
4. Re-generate avatar LoRA weights (System 1)

### Issue 2: High Safety Check Rejection Rate (>30%)

**Root Causes**:
1. Prompts too explicit (tier mismatch)
2. OpenAI moderation too strict
3. Template categories too suggestive

**Diagnosis**:
```bash
# Check rejection breakdown
grep "Safety check summary" app.log | \
  grep -oP "Rejected: \K[0-9]+(?=/)" | \
  head -20

# Check rejected categories
grep "Content rejected" app.log | \
  grep -oP "Reason: \K[^|]+" | sort | uniq -c | sort -rn
```

**Solutions**:
1. Adjust tier distribution (more capa1, less capa3)
2. Review template prompts for explicit content
3. Reduce capa2/capa3 ratio in batch config
4. Add content filtering before generating

### Issue 3: Hook Generation Failures (>5% errors)

**Root Causes**:
1. Claude API rate limit (quota exceeded)
2. Prompt too long (TooManyTokensError)
3. Network timeout (API unavailable)

**Diagnosis**:
```bash
# Check error types
grep "Hook generation.*Error" app.log | \
  grep -oP "Error: \K[^|]+" | sort | uniq -c | sort -rn
```

**Solutions**:
1. Implement exponential backoff retry
2. Truncate long prompts (max 500 tokens)
3. Add circuit breaker (stop trying if 5 consecutive failures)
4. Fallback: Generate placeholder hooks from templates

### Issue 4: Database Connection Exhaustion

**Symptom**: `sqlalchemy.exc.InvalidRequestError: QueuePool limit exceeded`

**Root Cause**: Database connections not returned to pool

**Solution**:
```python
# Ensure proper session cleanup
from contextlib import asynccontextmanager

@asynccontextmanager
async def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        await session.close()  # Always close
        
# Or use dependency injection (already done in FastAPI)
db: Session = Depends(get_db)  # Auto-closes after request
```

**Monitoring**:
```bash
# Check pool status
curl http://localhost:8000/api/v1/content/health | \
  jq '.checks.database'
```

### Issue 5: R2 Upload Failures (network, auth)

**Root Causes**:
1. Invalid R2 credentials
2. Bucket permissions inadequate
3. Presigned URL expired

**Diagnosis**:
```bash
# Check R2 configuration
curl http://localhost:8000/api/v1/content/health | \
  jq '.checks.r2_storage'

# Check credentials env vars
echo $R2_ACCOUNT_ID $R2_BUCKET_NAME
```

**Solutions**:
1. Regenerate R2 API tokens (30-day rotation)
2. Verify bucket policy allows uploads
3. Use presigned URLs with longer TTL (3-7 days)
4. Implement local fallback storage

---

## Environment Variables Reference

```bash
# Image Generation Providers
COMFYUI_ENABLED=true
COMFYUI_ENDPOINT=http://localhost:8188
MODAL_TOKEN_ID=...
REPLICATE_API_TOKEN=...

# LLM Services
ANTHROPIC_API_KEY=...           # For hooks
OPENAI_API_KEY=...               # For safety check

# Storage
R2_ACCOUNT_ID=...
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET_NAME=vixenbliss-content
R2_PUBLIC_URL=https://r2.example.com

# Processing Configuration
BATCH_GENERATION_TIMEOUT=600     # 10 minutes
HOOK_GENERATION_ENABLED=true
SAFETY_CHECK_ENABLED=true
UPLOAD_TO_STORAGE_ENABLED=true

# Logging
LOG_LEVEL=INFO
ENABLE_STRUCTURED_LOGGING=true   # For parse-friendly logs
```

---

## Quick Start: Optimization Checklist

- [ ] Enable ComfyUI for 50% cost reduction
- [ ] Configure proper batch sizes (default: 50)
- [ ] Set up database indexes (check schema.sql)
- [ ] Enable LRU caching for template lookups
- [ ] Configure timeout limits (batch max 600s)
- [ ] Set up health check monitoring (`/api/v1/content/health`)
- [ ] Review logs for bottlenecks (grep `[STEP` logs)
- [ ] Enable structured logging for metrics
- [ ] Test provider fallback chain (ComfyUI → Modal → Replicate)
- [ ] Implement cost tracking (log $cost per batch)

---

**References**:
- [System 2 Flow Documentation](./SYSTEM_2_FLOW.md)
- [API Contracts](../api-contracts/v1_endpoints.md)
- [Breaking Change Policy](../api-contracts/breaking-change-policy.md)
- [Modal SDXL LoRA Integration](../external-systems/modal-sdxl-lora.md)

