# SYSTEM_MAP.md - Mapeo de Sistemas a Módulos

## Propósito

Este documento mapea los **5 Sistemas Independientes** de VixenBliss Creator a los módulos, archivos y componentes reales de este repositorio.

Es la fuente de verdad para entender:
- ¿Dónde está cada sistema? (qué archivos)
- ¿Qué módulos pertenecen a cada sistema?
- ¿Qué dependencias tipicamente tienen?
- ¿Quién es responsible de cada sistema? (agente)

## 5 Sistemas Principales

### Sistema 1: Generación de Identidades _(Avatar Creation)_

**Propósito**: Crear avatares parametrizados fotorrealistas con datos completos de personalidad, biografía, y LoRA dinámico.

**Flujo**:
1. Usuario define avatar (niche, personality traits, visual characteristics)
2. Sistema genera dataset de 50 imágenes entrenables con variaciones
3. LoRA es entrenado en Replicate (async, costo ~$2.50)
4. LoRA es almacenado en Cloudflare R2 con presigned URLs
5. Avatar queda listo para generación de contenido

| Componente | Ubicación | Archivos |
|-----------|-----------|----------|
| **Data Models** | `backend/app/models/` | `avatar.py`, `identity_component.py` |
| **Schemas** | `backend/app/schemas/` | `identity.py` |
| **APIs** | `backend/app/api/` | `identities.py`, `avatars.py` |
| **Services (Core)** | `backend/app/services/` | `ai_providers.py`, `avatar_service.py` |
| **Services (LoRA)** | `backend/app/services/` | `lora_training.py`, `modal_sdxl_lora_client.py` |
| **Services (Dataset)** | `backend/app/services/` | `dataset_builder.py`, `image_processor.py` |
| **Services (Storage)** | `backend/app/services/` | `storage_service.py` |
| **Workers (Async)** | `backend/app/workers/` | `celery_app.py` - tasks: `create_avatar`, `train_lora`, `generate_dataset` |
| **Frontend Pages** | `frontend/app/` | `avatars/` page + components |
| **Frontend Components** | `frontend/components/` | `avatar-card.tsx`, `avatar-form.tsx`, etc. |
| **Database** | `database/` | Schema: `avatars` table, `identity_components` table, `lora_models` table |
| **Tests** | `backend/tests/` | `test_avatar_service.py`, `test_lora_training.py` |
| **Config** | `backend/config/` | `vixenbliss.json` (SDXL config) |

**Key Dependencies**:
- Replicate API (image generation, LoRA training)
- Cloudflare R2 (LoRA storage + presigned URLs)
- PostgreSQL (avatar metadata + LoRA history)
- OpenAI/Anthropic (bio generation)
- Modal (optional: serverless SDXL LoRA inference)

**Owner**: Backend Dev (avatar service) + LLM Specialist (bio generation)

---

### Sistema 2: Producción de Contenido _(Content Generation)_

**Propósito**: Generar 50+ piezas de contenido visual automaticamente usando avatar + LoRA, con prompts variados para cada niche.

**Flujo**:
1. Recibe avatar + niche + contenidos planificados
2. Genera 50 variaciones de imágenes (ángulos, expresiones, iluminación, backgrounds)
3. Genera captions y hashtags para cada imagen usando LLM
4. Almacena piezas en R2 + metadata en DB
5. Piezas quedan listas para distribución

| Componente | Ubicación | Archivos |
|-----------|-----------|----------|
| **Data Models** | `backend/app/models/` | `content_piece.py`, `social_account.py` |
| **Schemas** | `backend/app/schemas/` | `content.py` |
| **APIs** | `backend/app/api/` | `content.py` |
| **Services (Core)** | `backend/app/services/` | `content_generator.py`, `batch_processor.py` |
| **Services (Prompts)** | `backend/app/services/` | `prompt_generator.py`, `hook_generator.py` |
| **Services (LoRA Inference)** | `backend/app/services/` | `lora_inference.py` |
| **Services (Image)** | `backend/app/services/` | `image_processor.py`, `asset_manager.py` |
| **Services (LLM)** | `backend/app/services/` | `ai_providers.py` (OpenAI, Anthropic) |
| **Workers (Async)** | `backend/app/workers/` | `celery_app.py` - tasks: `generate_content_batch`, `generate_caption`, `process_image` |
| **Frontend Pages** | `frontend/app/` | `content/` page |
| **Frontend Components** | `frontend/components/` | `batch-generation-dialog.tsx`, `content-grid.tsx` |
| **Database** | `database/` | Schema: `content_pieces` table, `assets` table |
| **Tests** | `backend/tests/` | `test_content_generator.py`, `test_prompt_generator.py` |
| **Config** | `backend/config/` | `vixenbliss.json` (prompts templates) |

**Key Dependencies**:
- Modal SDXL LoRA provider (imagen generation con LoRA presigned URLs)
- OpenAI/Anthropic (caption + hook generation)
- Cloudflare R2 (storage de content pieces)
- PostgreSQL (content metadata)

**Owner**: Backend Dev (content service) + LLM Specialist (prompt engineering)

---

### Sistema 3: Distribución Automática _(Social Distribution)_

**Propósito**: Publicar contenido automáticamente en TikTok/Instagram con scheduling inteligente, hashtag management y optimal timing.

**Flujo**:
1. Selecciona contenido generado + avatar + timing
2. Enriquece captions con hashtags trending
3. Programa publicación en social networks via APIs
4. Trackea engagement (views, likes, comments, shares)
5. Adjusta scheduling según performance

| Componente | Ubicación | Archivos |
|-----------|-----------|----------|
| **Data Models** | `backend/app/models/` | `social_account.py`, `distribution_schedule.py` |
| **Schemas** | `backend/app/schemas/` | Distribution schemas |
| **APIs** | `backend/app/api/` | `distribution.py` |
| **Services (Social)** | `backend/app/services/` | `tiktok_client.py`, `instagram_client.py`, `social_api_client.py` |
| **Services (DM)** | `backend/app/services/` | `dm_webhook_handler.py`, `webhook_manager.py` |
| **Services (Scheduling)** | `backend/app/services/` | `scheduler_service.py`, `timing_optimizer.py` |
| **Services (Engagement)** | `backend/app/services/` | `engagement_tracker.py`, `analytics_service.py` |
| **Workers (Async)** | `backend/app/workers/` | `celery_app.py` - tasks: `post_to_social`, `track_engagement`, `schedule_distribution` |
| **Frontend Pages** | `frontend/app/` | `distribution/` page |
| **Frontend Components** | `frontend/components/` | `distribution-form.tsx`, `engagement-chart.tsx` |
| **Database** | `database/` | Schema: `distributions` table, `social_posts` table, `engagement_metrics` table |
| **Tests** | `backend/tests/` | `test_tiktok_client.py`, `test_scheduler_service.py` |
| **Webhooks** | `backend/app/api/` | `webhooks.py` (recibir DMs de Instagram/TikTok) |

**Key Dependencies**:
- TikTok API v1 (posting, engagement tracking, DM webhooks)
- Instagram Graph API (posting, engagement tracking, DM webhooks)
- PostgreSQL (schedule metadata, engagement history)
- Redis (scheduler state, rate limiting)

**Owner**: Backend Dev (social APIs) + DevOps (webhooks stability)

---

### Sistema 4: Monetización Multi-capa _(Revenue & Premium)_

**Propósito**: Gestionar suscripciones, premium packs, custom content, y revenue sharing automático.

**Flujo**:
1. Sistema detecta usuarios premium vs free
2. Avatar premium genera contenido exclusivo + early access
3. Custom content requests son procesados con upcharge
4. Revenue sharing automático con creators
5. Métricas de MRR, CAC, LTV se trackean continuamente

| Componente | Ubicación | Archivos |
|-----------|-----------|----------|
| **Data Models** | `backend/app/models/` | `user.py` (subscription tier), `conversation.py` (custom requests) |
| **Schemas** | `backend/app/schemas/` | Premium schemas |
| **APIs** | `backend/app/api/` | `premium.py`, `revenue.py` |
| **Services (Payments)** | `backend/app/services/` | `stripe_client.py`, `payment_processor.py` |
| **Services (Subscription)** | `backend/app/services/` | `subscription_manager.py` |
| **Services (Pricing)** | `backend/app/services/` | `pricing_engine.py`, `custom_content_pricing.py` |
| **Services (Revenue)** | `backend/app/services/` | `revenue_tracker.py`, `payout_manager.py` |
| **Services (Cost)** | `backend/app/services/` | `cost_tracker.py` |
| **Workers (Async)** | `backend/app/workers/` | `celery_app.py` - tasks: `process_payment`, `generate_custom_content`, `calculate_revenue`, `trigger_payout` |
| **Frontend Pages** | `frontend/app/` | `revenue/` page, `premium/` page |
| **Frontend Components** | `frontend/components/` | `revenue-chart.tsx`, `metric-card.tsx`, `subscription-form.tsx` |
| **Database** | `database/` | Schema: `subscriptions` table, `payments` table, `revenue` table |
| **Tests** | `backend/tests/` | `test_payment_processor.py`, `test_revenue_tracker.py` |

**Key Dependencies**:
- Stripe API (payments, subscription management)
- PostgreSQL (subscription metadata, revenue history)
- Stripe webhooks (payment events)

**Owner**: Backend Dev (payments logic) + Analyst (revenue metrics)

---

### Sistema 5: Chatbot Lead Generation _(DM to Subscriber)_

**Propósito**: Automatizar conversaciones en DMs para convertir followers en subscriptores.

**Flujo**:
1. Recibe DMs desde TikTok/Instagram via webhooks
2. Chatbot responde automaticamente usando LangGraph agent
3. Si usuario muestra interés → automáticamente suscribir con plan free trial
4. LLM trackea conversación e intent del usuario
5. Engagement metrics se actualizan continuamente

| Componente | Ubicación | Archivos |
|-----------|-----------|----------|
| **Data Models** | `backend/app/models/` | `conversation.py` |
| **Schemas** | `backend/app/schemas/` | Conversation schemas |
| **APIs** | `backend/app/api/` | `conversations.py`, `webhooks.py` |
| **Services (Agent)** | `backend/app/services/` | `chatbot_agent.py`, `langgraph_workflows.py` |
| **Services (Webhook)** | `backend/app/services/` | `dm_webhook_handler.py` |
| **Services (Intent)** | `backend/app/services/` | `intent_detector.py`, `conversation_analyzer.py` |
| **Services (Conversion)** | `backend/app/services/` | `lead_converter.py`, `trial_manager.py` |
| **Services (LLM)** | `backend/app/services/` | `ai_providers.py` (Claude agent) |
| **Workers (Async)** | `backend/app/workers/` | `celery_app.py` - tasks: `process_dm`, `reply_on_dm`, `convert_to_subscriber` |
| **Frontend Pages** | `frontend/app/` | Dashboard: conversation history, metrics |
| **Frontend Components** | `frontend/components/` | `conversation-list.tsx`, `chatbot-metrics.tsx` |
| **Database** | `database/` | Schema: `conversations` table, `messages` table, `intent_logs` table |
| **Tests** | `backend/tests/` | `test_chatbot_agent.py`, `test_intent_detector.py` |
| **LLM Config** | `.ai/` or `backend/config/` | LangGraph workflow definitions |

**Key Dependencies**:
- LangGraph (multi-step agent workflows)
- Claude 3.5 Sonnet (intelligence)
- TikTok/Instagram APIs (recibir y responder DMs)
- PostgreSQL (conversation history)
- Stripe API (crear trial subscriptions)

**Owner**: LLM Specialist (agent workflows) + Backend Dev (DM handling)

---

## Cross-System Components

Algunos componentes sirven a múltiples sistemas:

| Component | Location | Used by Systems | Purpose |
|-----------|----------|-----------------|---------|
| **Database** | `database/schema.sql` | All 5 | Single source of truth para datos |
| **Storage Service** | `backend/app/services/storage_service.py` | 1, 2, 3, 4, 5 | R2 management (upload, delete, presigned URLs) |
| **AI Providers** | `backend/app/services/ai_providers.py` | 1, 2, 5 | Replicate, OpenAI, Anthropic abstractions |
| **Cost Tracker** | `backend/app/services/cost_tracker.py` | 1, 2, 4, 5 | Tracking LLM + image generation costs |
| **Health Monitor** | `backend/app/services/health_monitoring.py` | Control plane | Monitorear salud de APIs externas |
| **Celery Workers** | `backend/app/workers/` | All 5 | Async task processing |
| **Logging/Observability** | `backend/app/` (logging setup) | All 5 | Structured logging + debugging |
| **Frontend API Client** | `frontend/lib/api/` | All 5 | HTTP client wrapper con error handling |
| **Webhooks Handler** | `backend/app/api/webhooks.py` | 3, 5 | Webhook processing (social + DM events) |

---

## Technology Stack by System

### System 1: Generación de Identidades
```
Frontend: React (avatars/ page), shadcn/ui
Backend: FastAPI, SQLAlchemy, Pydantic
External: Replicate (SDXL), Cloudflare R2, OpenAI/Claude
Database: PostgreSQL + pgvector (embeddings para bio search)
Async: Celery (train_lora task)
```

### System 2: Producción de Contenido
```
Frontend: React (content/ page), Canvas/Sharp para previews
Backend: FastAPI, Batch processing, Prompt templating
External: Modal SDXL LoRA (inference), OpenAI (captions)
Database: PostgreSQL
Async: Celery (batch generation tasks)
```

### System 3: Distribución Automática
```
Frontend: React (distribution/ page), Charts (engagement visualization)
Backend: FastAPI, Scheduler (APScheduler), Webhooks
External: TikTok API, Instagram Graph API
Database: PostgreSQL
Async: Celery (post_to_social task), Redis (scheduler state)
```

### System 4: Monetización Multi-capa
```
Frontend: React (revenue/ page), Metrics cards
Backend: FastAPI, Payment processing
External: Stripe API
Database: PostgreSQL
Async: Celery (payment processing, revenue calculation)
```

### System 5: Chatbot Lead Generation
```
Frontend: React (conversations/ history)
Backend: FastAPI, LangGraph (agent orchestration)
External: Claude (LLM), TikTok/Instagram APIs (DM), Stripe (trial creation)
Database: PostgreSQL
Async: Celery (agent execution tasks), Message queue
```

---

## Dependency Graph

```
Sistema 1 (Identidades)
    ├─ Cloudflare R2 (LoRA storage)
    ├─ Replicate (training)
    ├─ PostgreSQL (avatar metadata)
    └─ OpenAI/Claude (bio generation) → Sistema 5 puede reutilizar bios

Sistema 2 (Contenido)
    ├─ Sistema 1 (requiere avatar + LoRA)
    ├─ Modal SDXL LoRA (inference con LoRA presigned URL)
    ├─ OpenAI (caption generation)
    ├─ Cloudflare R2 (piece storage)
    └─ PostgreSQL (piece metadata)

Sistema 3 (Distribución)
    ├─ Sistema 2 (requiere content pieces)
    ├─ TikTok API (posting + webhook)
    ├─ Instagram API (posting + webhook)
    ├─ PostgreSQL (schedule + engagement tracking)
    └─ Redis (scheduler state)

Sistema 4 (Monetización)
    ├─ Sistema 1 (avatar metrics)
    ├─ Sistema 2 (content metrics)
    ├─ Sistema 3 (engagement metrics para revenue calculation)
    ├─ Stripe (payment + subscription)
    └─ PostgreSQL (subscription + revenue data)

Sistema 5 (Chatbot)
    ├─ Sistema 1 (avatar info para contexto chatbot)
    ├─ Sistema 3 (DM webhooks)
    ├─ Claude 3.5 Sonnet (agent intelligence)
    ├─ TikTok/Instagram APIs (DM send)
    ├─ Stripe (create trial subscription)
    └─ PostgreSQL (conversation history)
```

---

## File Locations Quick Reference

| Task | File(s) | System |
|------|---------|--------|
| Agregar campo a avatar | `backend/app/models/avatar.py` + migration | 1 |
| Implementar nuevo endpoint | `backend/app/api/[module].py` + `backend/app/schemas/` | Any |
| Agregar Celery task | `backend/app/workers/celery_app.py` | Any |
| Cambiar prompt template | `backend/config/vixenbliss.json` or `backend/app/services/prompt_generator.py` | 2, 5 |
| Agregar social network | `backend/app/services/[network]_client.py` | 3 |
| Agregar métrica de revenue | `backend/app/services/revenue_tracker.py` + `frontend/components/metric-card.tsx` | 4 |
| Actualizar LangGraph agent | `backend/app/services/chatbot_agent.py` or `.ai/workflows/` | 5 |
| Agregar test | `backend/tests/test_[module].py` | Any |

---

**Última actualización**: 2026-02-11  
**Versión**: 1.0  
**Responsable de actualización**: Architect + Scrum Master

---

## Notas Importantes

1. **Este mapa es living document**: Debe actualizarse cuando se agregan nuevos módulos o sistemas.
2. **Cross-system dependencies**: Cambios a componentes compartidos (Database, Storage Service) pueden afectar múltiples sistemas → require coordinated testing.
3. **Owner responsability**: Cada sistema tiene "owner" (agente especializado) responsable de la salud e integridad.
4. **Testing strategy**: Tests deben ser por sistema + integration tests entre sistemas críticos (ej: 1→2, 3→4).

---

## Complemento Arquitectonico (Consolidado)

Esta seccion incorpora contenido operativo que antes vivia en `docs/ARCHITECTURE.md`.
Desde 2026-02-12, `docs/SYSTEM_MAP.md` es la fuente unica activa para arquitectura + mapeo.

### Seguridad Baseline

- Auth principal por JWT/Bearer para endpoints privados.
- Secretos solo por variables de entorno (sin hardcode).
- Conexiones externas bajo TLS.
- Revisiones de seguridad obligatorias para auth, pagos, webhooks y providers externos.

### Observabilidad y Metricas

- Negocio: MRR, CAC, LTV, conversion rate, churn.
- Tecnicas: latencia API (P50/P95/P99), error rate por endpoint, exito de jobs async.
- Costos: tracking por avatar/batch/provider para LLM e inferencia de imagen/video.

### Topologia de Despliegue (alto nivel)

- Frontend: Next.js
- Backend: FastAPI
- Async: Celery + Redis
- DB: PostgreSQL/Supabase
- Storage: Cloudflare R2
- Externos: Modal, OpenAI/Anthropic, Stripe, APIs sociales

### Regla de Mantenimiento

- No reintroducir duplicado de arquitectura en `docs/ARCHITECTURE.md`.
- Toda actualizacion de arquitectura o mapeo va en este archivo.
- Historial anterior: `docs/_archive/ARCHITECTURE.2026-02-12.md`.
