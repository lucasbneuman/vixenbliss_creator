# VixenBliss Creator - Setup Guide

Guía de configuración del ambiente de desarrollo para VixenBliss Creator.

## Requisitos Previos

### Software Requerido
- **Python**: 3.11 o superior
- **Node.js**: 20.x o superior
- **PostgreSQL**: 15 o superior
- **Redis**: 7.x o superior
- **Git**: Para control de versiones

### Servicios Externos
- Cuenta en **Replicate** (LoRA training/inference)
- API keys de **OpenAI** y **Anthropic**
- Cuenta en **Stripe** (modo test para desarrollo)
- Cuenta en **Cloudflare** (R2 para storage)
- Cuenta en **Notion** (gestión de tareas)

## Instalación

### 1. Clonar el Repositorio

```bash
git clone <repository-url>
cd vixenbliss_creator
```

### 2. Backend Setup (FastAPI)

#### Crear Ambiente Virtual

```bash
cd backend
python -m venv venv
```

#### Activar Ambiente Virtual

**Windows:**
```bash
venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

#### Instalar Dependencias

```bash
# Producción
pip install -r requirements.txt

# Desarrollo (incluye herramientas adicionales)
pip install -r requirements-dev.txt
```

#### Configurar Variables de Entorno

```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar .env con tus API keys
# IMPORTANTE: NO commitear .env a git
```

#### Variables Críticas (Backend)

Edita `backend/.env` con tus valores:

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/vixenbliss
REDIS_URL=redis://localhost:6379
SECRET_KEY=<genera-una-clave-secreta-aleatoria>
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
REPLICATE_API_TOKEN=r8_...
STRIPE_SECRET_KEY=sk_test_...
```

**Generar SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Frontend Setup (Next.js)

```bash
cd frontend
```

#### Instalar Dependencias

```bash
npm install
```

#### Configurar Variables de Entorno

```bash
# Copiar archivo de ejemplo
cp .env.example .env.local

# Editar .env.local
```

#### Variables Críticas (Frontend)

Edita `frontend/.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=<genera-una-clave-secreta>
```

**Generar NEXTAUTH_SECRET:**
```bash
openssl rand -base64 32
```

### 4. Database Setup

#### Crear Base de Datos

```bash
# PostgreSQL
createdb vixenbliss

# O usando psql
psql -U postgres
CREATE DATABASE vixenbliss;
\q
```

#### Ejecutar Migrations

```bash
cd database
psql $DATABASE_URL -f migrations/001_create_avatars.up.sql
# ... ejecutar todas las migrations en orden
```

### 5. Redis Setup

#### Instalar Redis

**macOS (Homebrew):**
```bash
brew install redis
brew services start redis
```

**Ubuntu/Debian:**
```bash
sudo apt-get install redis-server
sudo systemctl start redis
```

**Windows:**
Usar Docker o WSL2 con Ubuntu

#### Verificar Redis

```bash
redis-cli ping
# Debe responder: PONG
```

## Ejecutar el Proyecto

### Opción 1: Desarrollo Local (Servicios Separados)

#### Terminal 1 - Backend API
```bash
cd backend
source venv/bin/activate  # o venv\Scripts\activate en Windows
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Terminal 2 - Celery Worker
```bash
cd backend
source venv/bin/activate
celery -A app.workers.celery_app worker --loglevel=info
```

#### Terminal 3 - Celery Beat (Scheduler)
```bash
cd backend
source venv/bin/activate
celery -A app.workers.celery_app beat --loglevel=info
```

#### Terminal 4 - Frontend
```bash
cd frontend
npm run dev
```

### Opción 2: Docker Compose (Recomendado)

```bash
# Construir y levantar todos los servicios
docker-compose up --build

# En background
docker-compose up -d

# Ver logs
docker-compose logs -f

# Detener servicios
docker-compose down
```

## Verificar Instalación

### Backend Health Check
```bash
curl http://localhost:8000/health
```

Debe responder:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00",
  "version": "1.0.0"
}
```

### Frontend
Abre en navegador:
```
http://localhost:3000
```

### Redis
```bash
redis-cli ping
# PONG
```

### PostgreSQL
```bash
psql $DATABASE_URL -c "SELECT version();"
```

## Comandos Útiles

### Backend

```bash
# Ejecutar tests
pytest

# Con coverage
pytest --cov=app --cov-report=html

# Format code
black .

# Lint
flake8 app/

# Type check
mypy app/
```

### Frontend

```bash
# Ejecutar tests
npm test

# Con coverage
npm test -- --coverage

# Lint
npm run lint

# Build producción
npm run build

# Preview build
npm start
```

### Database

```bash
# Crear nueva migration
# migrations/00X_nombre.up.sql
# migrations/00X_nombre.down.sql

# Aplicar migration
psql $DATABASE_URL -f migrations/00X_nombre.up.sql

# Rollback migration
psql $DATABASE_URL -f migrations/00X_nombre.down.sql
```

## Estructura de Directorios

```
vixenbliss_creator/
├── backend/              # FastAPI application
│   ├── app/
│   │   ├── main.py      # FastAPI app entry
│   │   ├── api/         # API endpoints
│   │   ├── models/      # Pydantic models
│   │   ├── services/    # Business logic
│   │   └── workers/     # Celery tasks
│   ├── tests/           # Backend tests
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/            # Next.js application
│   ├── app/            # Next.js 14 App Router
│   ├── components/     # React components
│   ├── lib/           # Utilities
│   ├── package.json
│   └── .env.example
│
├── database/           # SQL migrations
│   └── migrations/
│
├── llm-service/       # LangChain/LangGraph (futuro)
│
├── .claude/agents/    # Claude Code agents
├── .ai/              # Agent documentation
├── docs/             # Project documentation
├── docker-compose.yml
└── README.md
```

## Troubleshooting

### Error: Port 8000 already in use
```bash
# Encontrar proceso
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Matar proceso
kill -9 <PID>
```

### Error: Cannot connect to PostgreSQL
- Verificar que PostgreSQL está corriendo
- Verificar DATABASE_URL en .env
- Verificar credenciales de usuario

### Error: Redis connection refused
- Verificar que Redis está corriendo: `redis-cli ping`
- Iniciar Redis si está detenido

### Error: npm install fails
- Limpiar cache: `npm cache clean --force`
- Borrar node_modules: `rm -rf node_modules`
- Reinstalar: `npm install`

### Error: Python dependencies fail
- Actualizar pip: `pip install --upgrade pip`
- Instalar build tools si es necesario
- Verificar versión de Python: `python --version`

## Siguientes Pasos

1. **Revisar ARCHITECTURE.md** - Entender la arquitectura del sistema
2. **Ejecutar ÉPICA 01** - Setup inicial del proyecto
3. **Configurar IDE** - VSCode con extensiones recomendadas
4. **Familiarizarse con los agentes** - Ver `.claude/agents/README.md`

## Recursos Adicionales

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js 14 Documentation](https://nextjs.org/docs)
- [LangChain Documentation](https://python.langchain.com/)
- [shadcn/ui Components](https://ui.shadcn.com/)
- [Replicate Documentation](https://replicate.com/docs)

## Soporte

Para problemas o preguntas:
- Revisar documentación en `docs/`
- Consultar `.ai/` para guías de agentes
- Revisar BUGS.md para bugs conocidos
