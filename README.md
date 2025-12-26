# VixenBliss Creator

Plataforma SaaS para generación automatizada de avatares AI y gestión de contenido en redes sociales.

## Descripción del Proyecto

VixenBliss Creator automatiza todo el proceso de creación, gestión y monetización de avatares AI para redes sociales (Instagram/TikTok):

1. **Generación de Identidades**: Crea avatares fotorrealistas con personalidad completa
2. **Producción de Contenido**: Genera 50+ piezas de contenido visual automáticamente
3. **Distribución Automática**: Publica en TikTok/Instagram con scheduling inteligente
4. **Monetización Multi-capa**: Subscripciones, premium packs, custom content
5. **Chatbot Lead Generation**: Convierte DMs en subscriptores automáticamente

## Stack Tecnológico

- **Frontend**: Next.js 14, TypeScript, shadcn/ui, TailwindCSS
- **Backend**: FastAPI, Python 3.11+, Celery
- **Database**: PostgreSQL (Supabase), pgvector
- **LLM**: LangChain, LangGraph, LangFuse
- **AI**: Replicate (LoRA), OpenAI, Anthropic
- **Deployment**: Coolify, Docker, GitHub Actions
- **Storage**: Cloudflare R2

## Estructura del Proyecto

```
vixenbliss_creator/
├── .ai/                        # Agentes especializados de Claude Code
│   ├── agents/                 # 9 agentes especializados
│   │   ├── scrum-master.md     # Orquestador principal (integración Notion)
│   │   ├── architect.md        # Arquitectura del sistema
│   │   ├── backend-dev.md      # Desarrollo FastAPI
│   │   ├── frontend-dev.md     # Desarrollo Next.js
│   │   ├── llm-specialist.md   # LangChain/LangGraph
│   │   ├── database-engineer.md # PostgreSQL/Supabase
│   │   ├── devops-engineer.md  # Coolify/Docker
│   │   ├── qa-tester.md        # Testing
│   │   └── analyst.md          # Analytics y métricas
│   ├── workflows/              # Flujos de trabajo
│   │   ├── feature-development.md
│   │   ├── bug-fixing.md
│   │   └── deployment.md
│   └── context/                # Contexto compartido
│       ├── project-rules.md
│       ├── coding-standards.md
│       └── security-guidelines.md
│
├── docs/                       # Documentación del proyecto
│   ├── ARCHITECTURE.md         # Arquitectura técnica completa
│   ├── API_DOCUMENTATION.md    # Documentación de APIs
│   ├── TASK.md                 # Registro de tareas (2 líneas/tarea)
│   └── BUGS.md                 # Registro de bugs (5 líneas/bug)
│
├── frontend/                   # Next.js app (a implementar)
├── backend/                    # FastAPI app (a implementar)
├── llm-service/                # LangChain/LangGraph (a implementar)
├── database/                   # SQL schemas & migrations (a implementar)
│
├── .scripts/                   # Scripts de utilidad
│   └── notion/                 # Scripts de integración Notion
│
├── .gitignore
└── README.md
```

## Agentes Especializados

Este proyecto utiliza una arquitectura de agentes especializados de Claude Code:

### Scrum Master (Agente Principal)
- Orquesta todo el trabajo del proyecto
- Se conecta con Notion para obtener y actualizar tareas
- Asigna trabajo a agentes especializados
- Hace seguimiento del progreso de las 12 épicas

### Agentes Especializados
- **Architect**: Diseño de arquitectura y decisiones tecnológicas
- **Backend Dev**: Implementación FastAPI, lógica de negocio
- **Frontend Dev**: Desarrollo Next.js, componentes React
- **LLM Specialist**: LangGraph agents, prompts, RAG
- **Database Engineer**: Schemas, migraciones, optimización
- **DevOps Engineer**: Docker, CI/CD, Coolify
- **QA Tester**: Tests unitarios, integración, E2E
- **Analyst**: Análisis de datos, métricas, dashboards

## Integración con Notion

El proyecto está integrado con Notion para gestión de tareas:

- **12 Épicas** definidas (E01-E12)
- **~62 Tareas** distribuidas entre épicas
- **Scrum Master** actualiza estados automáticamente: "Sin empezar" → "En progreso" → "Completado"

### IDs de Notion
- ÉPICAS_DB: `2d29bd8b-d487-8053-bec7-e243b9d70e7f`
- TAREAS_DB: `2d29bd8b-d487-80ef-a0b5-efb158e3aefb`
- PROYECTO_ID: `2d29bd8b-d487-800a-b70a-de19939bfa7b`

## Workflows de Desarrollo

### Feature Development
1. Scrum Master obtiene tarea de Notion
2. Asigna a agente especializado apropiado
3. Agente implementa + tests (>80% coverage)
4. QA verifica calidad
5. DevOps deploys a staging
6. Scrum Master actualiza Notion a "Completado"

### Bug Fixing
1. Bug reportado en BUGS.md
2. Scrum Master asigna por severity (Critical/High/Medium/Low)
3. Agente reproduce y corrige
4. QA verifica fix
5. Deploy si es Critical/High

### Deployment
1. Tests passing en staging
2. Database migrations tested
3. Deploy a production via Coolify
4. Health checks + smoke tests
5. Monitoring post-deployment

## Optimización de Costos

Estrategias implementadas para minimizar costos de LLM sin comprometer calidad:

- Uso de modelos apropiados (Haiku/Sonnet/Opus según complejidad)
- Prompts concisos y estructurados
- Queries selectivas a Notion (solo campos necesarios)
- Output estructurado (TASK.md: 2 líneas, BUGS.md: 5 líneas)
- Delegación inteligente a agentes especializados
- Batch processing donde sea posible

## Estándares de Código

### Python (Backend + LLM)
- Type hints obligatorios
- Pydantic para validaciones
- Async/await para I/O
- Tests >80% coverage

### TypeScript (Frontend)
- Strict mode enabled
- Server Components por defecto
- shadcn/ui para UI
- Type-safe API calls

### SQL (Database)
- Migraciones reversibles (up/down)
- Índices apropiados
- EXPLAIN ANALYZE para queries
- pgvector para RAG

## Documentación

- **ARCHITECTURE.md**: Descripción de los 5 sistemas principales
- **API_DOCUMENTATION.md**: Endpoints, schemas, ejemplos
- **TASK.md**: Registro de tareas completadas (2 líneas/tarea)
- **BUGS.md**: Registro de bugs (5 líneas/bug)

## Métricas de Éxito

### Business Metrics
- MRR (Monthly Recurring Revenue)
- CAC (Customer Acquisition Cost)
- LTV (Lifetime Value)
- Churn Rate
- Conversion Rate (Follower → Subscriber)

### Technical Metrics
- LLM Cost per Avatar
- Content Generation Cost
- API Response Times (P50, P95, P99)
- Test Coverage (>80%)
- Error Rates

### Avatar Performance
- Winner: ROI > 5x, conversion > 3%, churn < 5%
- Loser: ROI < 1x, conversion < 1%, churn > 15%

## Próximos Pasos

1. **ÉPICA 01**: Setup inicial (FastAPI, Next.js, Supabase, Coolify)
2. **ÉPICA 02**: Sistema de generación de identidades
3. **ÉPICA 03**: Sistema de producción de contenido
4. **ÉPICA 04**: Sistema de distribución automática
5. **ÉPICA 05-09**: Sistemas de monetización
6. **ÉPICA 10**: Optimización y testing
7. **ÉPICA 11**: Analytics y métricas
8. **ÉPICA 12**: Maintenance y monitoreo

## Licencia

Privado - VixenBliss Creator

## Contacto

Para más información sobre el proyecto, consulta la documentación en `docs/`.
