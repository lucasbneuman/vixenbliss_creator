# VixenBliss Creator - Agentes Especializados

## Proyecto Overview
**Plataforma SaaS** para generación automatizada de avatares AI y gestión de contenido en redes sociales.

### Stack Principal
- **Backend**: FastAPI + PostgreSQL + Celery
- **Frontend**: Next.js 14 + TypeScript + shadcn/ui
- **AI**: Replicate (LoRA) + OpenAI + Anthropic
- **Infra**: Docker + Coolify + Cloudflare R2

### Estado Actual
✅ Sistema 1: Generación de Identidades (con LoRAs pre-entrenados - FAST TRACK)
✅ Sistema 2: Producción de Contenido (50 piezas/avatar)
🔄 Sistema 3-5: En implementación

---

## Agentes Disponibles

### scrum-master
**Uso**: Gestión de proyecto, coordinación, Notion integration
- Obtiene tareas de Notion
- Asigna a agentes especializados
- Actualiza estados

### backend-dev
**Uso**: APIs FastAPI, lógica de negocio, Celery workers
- Endpoints REST con Pydantic
- Background jobs
- Integración con servicios externos

### frontend-dev
**Uso**: Componentes React, páginas Next.js, UI
- Industrial UI theme (Bloomberg-style)
- shadcn/ui components
- Type-safe API integration

### database-engineer
**Uso**: Schemas PostgreSQL, migrations, optimización
- Diseño de tablas
- Migrations (alembic)
- Índices y performance

### devops-engineer
**Uso**: Docker, CI/CD, deployments
- Docker Compose setup
- GitHub Actions
- Coolify deployment

### qa-tester
**Uso**: Tests, verificación de calidad
- pytest (backend)
- Jest (frontend)
- Coverage >80%

---

## Workflow Típico

1. **scrum-master** → Obtiene tarea de Notion
2. **Agente especializado** → Implementa
3. **qa-tester** → Verifica
4. **scrum-master** → Actualiza Notion

---

## Archivos de Contexto

- `docs/ARCHITECTURE.md` - Arquitectura del proyecto
- `docs/TASK.md` - Registro de tareas completadas
- `.ai/context/project-rules.md` - Reglas del proyecto
- `FAST_TRACK_LORAS.md` - Guía de LoRAs pre-entrenados

---

## Uso

Claude Code invocará automáticamente el agente apropiado:

```
Implementa el endpoint POST /api/v1/avatars
→ Usa backend-dev automáticamente

Crea el componente AvatarCard
→ Usa frontend-dev automáticamente

Obtén la próxima tarea de Notion
→ Usa scrum-master automáticamente
```

O explícitamente:
```
Usa backend-dev para implementar el endpoint de avatars
```
