# VixenBliss Creator - Project Rules

## Proyecto Overview
**VixenBliss Creator** es una plataforma SaaS para generación automatizada de avatares AI y gestión de contenido en redes sociales.

### Los 5 Sistemas Principales
1. **Sistema 1: Generación de Identidades** (ÉPICA 02)
   - API generación facial via Replicate
   - Dataset builder (50 imágenes/avatar)
   - LoRA training integration
   - Auto-bio generator con LLM

2. **Sistema 2: Producción de Contenido** (ÉPICA 03 + 08)
   - LoRA inference engine
   - Template library (50 poses)
   - Hook generator automático
   - Content safety layer
   - Video generation (futuro)

3. **Sistema 3: Distribución Automática** (ÉPICA 04)
   - TikTok API integration
   - Instagram API integration
   - Smart scheduler por timezone
   - Pattern randomization anti-ban

4. **Sistema 4: Monetización Multi-capa** (ÉPICA 05, 07, 09)
   - Capa 1: Subscripción básica ($9-19/mes)
   - Capa 2: Premium packs ($20-50)
   - Capa 3: Custom content ($50-200)
   - Stripe integration

5. **Sistema 5: Chatbot Lead Generation** (ÉPICA 06)
   - DM auto-responder (IG/TikTok)
   - 3-stage funnel engine
   - Lead scoring system
   - Conversion tracking

## Stack Tecnológico

### Frontend
- Next.js 14 (App Router)
- TypeScript (strict mode)
- shadcn/ui + TailwindCSS
- Deployment: Coolify + Docker

### Backend
- FastAPI (Python 3.11+)
- Pydantic v2 para validaciones
- Celery para background jobs
- PostgreSQL (Supabase) + pgvector

### LLM/AI
- LangChain + LangGraph
- LangFuse para observability
- OpenAI (gpt-4o-mini, gpt-4o)
- Anthropic (claude-3-haiku, claude-3-sonnet)
- Replicate (LoRA training & inference)

### Infrastructure
- Docker + Docker Compose
- Coolify para deployment
- GitHub Actions para CI/CD
- Cloudflare R2 para storage

## Épicas y Tareas (Notion)
- **12 Épicas** definidas en Notion
- **~62 Tareas** distribuidas entre épicas
- **Database IDs**:
  - ÉPICAS_DB: `2d29bd8b-d487-8053-bec7-e243b9d70e7f`
  - TAREAS_DB: `2d29bd8b-d487-80ef-a0b5-efb158e3aefb`
  - PROYECTO_ID: `2d29bd8b-d487-800a-b70a-de19939bfa7b`

## Reglas de Trabajo

### 1. Documentation Standards
- **TASK.md**: 2 líneas por tarea completada
  ```
  [PREFIX-###] Acción realizada con detalles específicos
  ```
- **BUGS.md**: 5 líneas por bug
  ```
  [BUG-###] Descripción
  Location: archivo:línea
  Impact: Severity - Descripción
  Temp Fix: Workaround o N/A
  Next: Próximos pasos
  ```
- **ARCHITECTURE.md**: Single source of truth para arquitectura
- **API_DOCUMENTATION.md**: Documentar endpoints, schemas, ejemplos

### 2. Agent Collaboration
- **Scrum Master** orquesta todo el trabajo
- Agentes especializados solo trabajan en su dominio
- Handoffs explícitos entre agentes
- Output estructurado y conciso (ahorro de costos)

### 3. Notion Integration
- Scrum Master es el único que actualiza Notion
- Queries selectivas (solo fields necesarios)
- Estados: "Sin empezar" → "En progreso" → "Completado"
- Prioridad: Alta, Media, Baja

### 4. Code Quality
- Tests requeridos (>80% coverage)
- Type hints en Python
- TypeScript strict mode
- No código comentado (eliminar)
- No TODOs en commits (resolver o crear tarea)

### 5. Cost Optimization
- Usar modelos apropiados (Haiku/Sonnet/Opus)
- Prompts concisos
- Batch processing donde sea posible
- Cache de queries repetitivos
- Eliminar verbosidad en outputs

## Forbidden Practices
- ❌ NO hardcodear secrets/API keys
- ❌ NO commits sin tests
- ❌ NO modificar DB schema sin migration
- ❌ NO deployment directo a production (usar staging)
- ❌ NO crear features sin tarea en Notion

## Cleanup Protocol
- Eliminar archivos temporales inmediatamente
- Borrar código comentado antes de commit
- Remover logs de debug en production
- Archivar documentación obsoleta
- Limpiar Docker images no usadas

## Success Metrics
- MRR (Monthly Recurring Revenue)
- CAC (Customer Acquisition Cost)
- LTV (Lifetime Value)
- Churn Rate
- Content generation cost per avatar
- LLM cost per conversation
