# Deployment Workflow

## Descripción
Flujo para deployments de VixenBliss Creator a staging y production usando Coolify.

## Trigger
- Feature completo y tested
- Hotfix crítico
- Release programado

## Participants
- **Scrum Master**: Orquestador
- **QA Tester**: Pre-deployment testing
- **DevOps Engineer**: Deployment execution
- **Backend/Frontend**: Support durante deployment
- **Database Engineer**: Migrations

## Deployment Types

### 1. Staging Deployment (Features nuevos)
```
[SM] Verifica tests passing
[QA] Ejecuta regression suite completo
[DB] Si hay migrations → aplica a staging DB
[OPS] Deploy a staging via Coolify webhook
[OPS] Verifica health checks
[QA] Smoke tests en staging
[SM] Output: [SM-###] Deploy staging completado, smoke tests OK
```

### 2. Production Deployment (Releases)
```
[SM] Verifica staging está stable por 24h+
[SM] Coordina deployment window
[DB] Backup production DB
[DB] Aplica migrations a production
[OPS] Deploy a production via Coolify
[OPS] Monitorea logs en tiempo real
[OPS] Verifica health checks
[QA] Smoke tests críticos en production
[SM] Output: [SM-###] Deploy production v1.X.X completado
```

### 3. Hotfix Deployment (Bugs críticos)
```
[SM] Valida bug es Critical severity
[QA] Verifica fix en local/staging
[OPS] Hotfix deployment directo a production
[OPS] Rollback plan preparado
[OPS] Monitorea metrics post-deployment
[SM] Output: [SM-###] Hotfix bug-XXX deployed a production
```

## Pre-Deployment Checklist

### Backend
- ✅ Tests passing (unit + integration)
- ✅ Type hints completos
- ✅ Environment variables documentadas
- ✅ Migrations tested (up/down)
- ✅ No secrets hardcoded

### Frontend
- ✅ Build successful
- ✅ No console errors
- ✅ API integration tested
- ✅ Environment variables configuradas
- ✅ Assets optimizados

### Database
- ✅ Migrations reversibles
- ✅ Backup realizado
- ✅ Índices verificados
- ✅ Query performance OK

### DevOps
- ✅ Docker images optimizadas
- ✅ Health checks configurados
- ✅ Logs accesibles
- ✅ Secrets en Coolify
- ✅ Rollback plan preparado

## Deployment Steps

### 1. Pre-Deployment
```bash
# QA - Run tests
cd backend && pytest
cd frontend && npm test

# DB - Backup
pg_dump $PROD_DB_URL > backup_$(date +%Y%m%d).sql

# DevOps - Build images
docker build -t vixenbliss-backend:latest ./backend
docker build -t vixenbliss-frontend:latest ./frontend
```

### 2. Deployment
```bash
# DevOps - Trigger Coolify webhook
curl -X POST $COOLIFY_WEBHOOK_URL

# DevOps - Monitor logs
docker logs -f vixenbliss-backend
docker logs -f vixenbliss-frontend
```

### 3. Post-Deployment
```bash
# DevOps - Health checks
curl https://api.vixenbliss.com/health
curl https://vixenbliss.com

# QA - Smoke tests
# - Login flow
# - Avatar creation
# - Content generation
# - API endpoints críticos
```

### 4. Rollback (si es necesario)
```bash
# DevOps - Rollback to previous version
curl -X POST $COOLIFY_ROLLBACK_WEBHOOK

# DB - Rollback migration
psql $PROD_DB_URL -f migrations/XXX_down.sql

# DevOps - Verify rollback
curl https://api.vixenbliss.com/health
```

## Monitoring Post-Deployment

### First 15 minutes
- ✅ Health checks passing
- ✅ No error spikes in logs
- ✅ Response times normal
- ✅ CPU/Memory usage normal

### First 1 hour
- ✅ User flows working
- ✅ Background jobs running
- ✅ Database queries performant
- ✅ LLM integrations working

### First 24 hours
- ✅ No increase in error rate
- ✅ No user complaints
- ✅ Metrics stable
- ✅ Costs dentro de budget

## Output Format
```
[OPS-###] Deployed v1.X.X to staging/production - components: BE, FE, DB
[QA-###] Smoke tests post-deployment: 10/10 passing
[SM-###] Deployment v1.X.X completado, monitoring OK
```

## Cost Optimization
- Deployments batched (no deploy cada cambio pequeño)
- Smoke tests minimal (solo critical paths)
- Monitoring automatizado (no manual watching)
- Rollback automático si health checks fail
