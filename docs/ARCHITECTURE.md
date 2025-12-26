# VixenBliss Creator - Architecture Documentation

## Overview
VixenBliss Creator es una plataforma SaaS para generación automatizada de avatares AI y gestión de contenido en redes sociales.

## Los 5 Sistemas Principales

### Sistema 1: Generación de Identidades (ÉPICA 02)
**Objetivo**: Crear avatares AI fotorrealistas con identidad completa.

**Componentes**:
- **API Generación Facial**: Integración con Replicate para generar rostros
- **Dataset Builder**: Genera 50 imágenes variadas del avatar
- **LoRA Training**: Entrena modelo personalizado via Replicate
- **Auto-Bio Generator**: LLM genera biografía basada en nicho/estilo
- **Location/Interests Engine**: Asigna personalidad y contexto
- **Cost Tracking**: Monitoreo de costos por avatar

**Stack**:
- Backend: FastAPI endpoints (`/api/v1/avatars`)
- LLM: LangChain para bio generation
- Storage: Cloudflare R2 para imágenes
- Database: PostgreSQL (tablas: `avatars`, `identity_components`)

**Flow**:
```
1. Usuario crea avatar → Configura nicho, estilo estético
2. Sistema genera rostro base via Replicate
3. Dataset builder crea 50 variaciones
4. LoRA training (20-30 min)
5. LLM genera bio, location, interests
6. Avatar listo para producción de contenido
```

---

### Sistema 2: Producción de Contenido (ÉPICA 03 + 08)
**Objetivo**: Generar 50+ piezas de contenido visual por avatar automáticamente.

**Componentes**:
- **LoRA Inference Engine**: Usa modelo entrenado para generar imágenes
- **Template Library**: 50 poses/escenarios predefinidos
- **Hook Generator**: LLM crea copy atractivo para cada pieza
- **Content Safety Layer**: Moderación de contenido
- **Batch Processing**: Genera 50 piezas en paralelo
- **R2 Upload + CDN**: Almacenamiento y distribución

**Stack**:
- Backend: Celery workers para batch processing
- LLM: LangGraph agent para hook generation
- Storage: R2 + CDN URLs
- Database: tabla `content_pieces` con metadata

**Flow**:
```
1. Avatar completo → Sistema inicia batch generation
2. Selecciona 50 templates de library
3. LoRA inference para cada template
4. LLM genera hook personalizado
5. Safety check (OpenAI moderation)
6. Upload a R2, genera CDN URLs
7. 50 piezas listas para scheduling
```

**Futuro (ÉPICA 08)**:
- Video generation via Replicate
- Voice synthesis
- Multi-provider fallback

---

### Sistema 3: Distribución Automática (ÉPICA 04)
**Objetivo**: Publicar contenido en TikTok/Instagram automáticamente.

**Componentes**:
- **TikTok API Integration**: Publicación programada
- **Instagram API Integration**: Posts + Stories
- **Smart Scheduler**: Optimiza por timezone y engagement patterns
- **Pattern Randomization**: Anti-ban protection
- **Health Monitoring**: Detecta cuentas shadowbanned
- **Auto-Retry + Fallback**: Reintentos inteligentes

**Stack**:
- Backend: Celery beat para scheduling
- APIs: TikTok Business API, Instagram Graph API
- Database: tabla `scheduled_posts`, `platform_accounts`

**Flow**:
```
1. Content piece listo → Entra en scheduling queue
2. Smart scheduler determina mejor momento
3. Pattern randomization aplica variaciones
4. Publica via API (TikTok/Instagram)
5. Health monitoring verifica success
6. Si falla → Auto-retry con backoff exponencial
```

---

### Sistema 4: Monetización Multi-capa (ÉPICA 05, 07, 09)
**Objetivo**: Convertir followers en revenue a través de 3 capas.

**Capa 1: Subscripción Básica** (ÉPICA 05)
- **Precio**: $9-19/mes
- **Acceso**: Contenido exclusivo, DM access
- **Stripe Integration**: Subscripciones recurrentes
- **Content Gating**: Paywall para contenido premium

**Capa 2: Premium Packs** (ÉPICA 07)
- **Precio**: $20-50 por pack
- **Contenido**: Sets temáticos, contenido especial
- **Upsell Automation**: Chatbot detecta oportunidades
- **Conversion Tracking**: Funnel Capa 1 → Capa 2

**Capa 3: Custom Content** (ÉPICA 09)
- **Precio**: $50-200 por request
- **Custom Requests**: Usuario pide contenido específico
- **Chatbot Negotiation**: Automatiza proceso de venta
- **Auto-Delivery**: Genera y entrega contenido custom

**Stack**:
- Backend: Stripe webhooks, subscription management
- Database: tablas `subscriptions`, `purchases`, `revenue`
- LLM: Agent para upsell detection y negotiation

**Flow**:
```
Capa 1: Follower → DM → Chatbot ofrece subscription → Stripe checkout → Subscriber
Capa 2: Subscriber → Chatbot detecta engagement alto → Ofrece premium pack → Upsell
Capa 3: Premium user → Solicita custom → Chatbot negocia → Pago → Auto-genera
```

---

### Sistema 5: Chatbot Lead Generation (ÉPICA 06)
**Objetivo**: Automatizar conversión de DMs en subscriptores.

**Componentes**:
- **DM Auto-Responder**: Responde DMs en IG/TikTok automáticamente
- **3-Stage Funnel Engine**: Engagement → Qualification → Conversion
- **Lead Scoring System**: Clasifica leads por probabilidad de conversión
- **Conversion Tracking**: Métricas de funnel
- **A/B Testing Framework**: Optimiza copy y estrategia

**Stack**:
- LLM: LangGraph multi-stage agent
- Backend: Webhooks de IG/TikTok
- Database: tabla `conversations`, `leads`, `conversions`

**3-Stage Funnel**:
```
Stage 1: Engagement
- Usuario envía DM
- Bot responde con personalidad del avatar
- Califica interés (lead scoring)

Stage 2: Qualification
- Bot hace preguntas para entender necesidad
- Detecta fit con subscription
- Incrementa lead score

Stage 3: Conversion
- Bot ofrece subscription con CTA
- Maneja objeciones
- Cierra venta o schedule follow-up
```

**LangGraph Agent**:
```python
workflow = StateGraph(ConversationState)
workflow.add_node("personality_injection", inject_personality)
workflow.add_node("lead_scoring", score_lead)
workflow.add_node("qualification", qualify_lead)
workflow.add_node("upsell_detection", detect_upsell)
workflow.add_conditional_edges(...)
```

---

## Stack Tecnológico Completo

### Frontend
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript (strict mode)
- **UI**: shadcn/ui + TailwindCSS
- **State**: React Server Components
- **Deployment**: Coolify + Docker

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Validation**: Pydantic v2
- **Background Jobs**: Celery + Redis
- **Database**: PostgreSQL (Supabase) + pgvector
- **ORM**: SQLAlchemy / Raw SQL
- **Deployment**: Coolify + Docker

### LLM Service
- **Framework**: LangChain + LangGraph
- **Observability**: LangFuse
- **Providers**:
  - OpenAI (gpt-4o-mini, gpt-4o)
  - Anthropic (claude-3-haiku, claude-3-sonnet)
  - Replicate (LoRA training/inference)

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Deployment**: Coolify (self-hosted PaaS)
- **CI/CD**: GitHub Actions
- **Storage**: Cloudflare R2 (S3-compatible)
- **Database**: Supabase (managed PostgreSQL)
- **Cache/Queue**: Redis

### Third-Party APIs
- **Social Media**: Instagram Graph API, TikTok Business API
- **Payments**: Stripe (subscriptions + one-time payments)
- **AI Generation**: Replicate (LoRA), OpenAI, Anthropic
- **Project Management**: Notion API

---

## Database Schema (High-Level)

### Core Tables
```
avatars (identidad del avatar)
├── identity_components (bio, interests, location)
├── content_pieces (imágenes/videos generados)
├── scheduled_posts (distribution queue)
├── subscriptions (Capa 1)
├── purchases (Capa 2 + 3)
└── conversations (chatbot interactions)

users (propietarios de avatares)
platform_accounts (IG/TikTok credentials)
revenue (tracking de ingresos)
llm_costs (tracking de costos LLM)
```

### Vector Storage
```
avatar_memories (pgvector for RAG)
- embedding: vector(1536)  -- OpenAI embeddings
- Used for: Chatbot context, personality consistency
```

---

## API Boundaries

### Backend API (FastAPI)
```
/api/v1/avatars          - CRUD avatares
/api/v1/content          - Content pieces
/api/v1/scheduling       - Distribution
/api/v1/subscriptions    - Monetización
/api/v1/analytics        - Métricas
/webhooks/stripe         - Stripe events
/webhooks/instagram      - IG events
/webhooks/tiktok         - TikTok events
```

### LLM Service (Internal)
```
/generate/bio            - Auto-bio generation
/generate/hook           - Content hooks
/conversation/respond    - Chatbot responses
/conversation/score      - Lead scoring
/moderation/check        - Content safety
```

---

## Security Architecture

### Authentication
- **Frontend**: NextAuth.js (JWT sessions)
- **Backend**: JWT Bearer tokens
- **APIs**: API keys en environment variables

### Secrets Management
- **Development**: `.env` files (gitignored)
- **Production**: Coolify secrets
- **Never**: Hardcoded secrets

### Data Protection
- **Encryption**: SSL/TLS for all connections
- **Passwords**: bcrypt hashing
- **Database**: Row-level security (RLS) via Supabase

---

## Monitoring & Analytics

### Business Metrics (ÉPICA 11)
- **MRR**: Monthly Recurring Revenue
- **CAC**: Customer Acquisition Cost
- **LTV**: Lifetime Value
- **Churn Rate**: Subscriber cancellations
- **Conversion Rate**: Follower → Subscriber

### Technical Metrics
- **LLM Cost per Avatar**: Token usage tracking
- **Content Generation Cost**: Replicate API costs
- **API Response Times**: P50, P95, P99
- **Error Rates**: 4xx, 5xx por endpoint
- **Background Job Success Rate**: Celery tasks

### Winner/Loser Detection
```python
Winner: ROI > 5x, conversion > 3%, churn < 5%
Loser: ROI < 1x, conversion < 1%, churn > 15%
```

---

## Deployment Architecture

### Environments
- **Development**: Local Docker Compose
- **Staging**: Coolify (testing)
- **Production**: Coolify (live)

### Coolify Services
```
vixenbliss-frontend (Next.js)
vixenbliss-backend (FastAPI)
vixenbliss-llm-service (LangChain)
vixenbliss-postgres (Supabase)
vixenbliss-redis (Cache/Queue)
vixenbliss-celery-worker (Background jobs)
vixenbliss-celery-beat (Scheduler)
```

---

## Development Workflow

### Feature Development
1. Scrum Master obtiene tarea de Notion
2. Asigna a agente especializado
3. Agente implementa + tests
4. QA verifica
5. DevOps deploys a staging
6. Scrum Master actualiza Notion

### Bug Fixing
1. Bug reportado en BUGS.md
2. Scrum Master asigna por severity
3. Agente reproduce + fix
4. QA verifica fix
5. Deploy si es Critical/High

### Deployment
1. Tests passing en staging
2. Migrations tested
3. Deploy a production via Coolify
4. Health checks + smoke tests
5. Monitor metrics post-deployment
