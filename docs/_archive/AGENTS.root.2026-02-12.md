# ARCHIVED

Archivo archivado el 2026-02-12 durante consolidacion de entrypoint de contexto.
Fuente original: /AGENTS.md

---
# Repository Guidelines

## Estructura del Proyecto y OrganizaciÃ³n de MÃ³dulos
- `backend/`: app FastAPI (`app/`), workers de Celery, servicios, modelos y tests en `backend/tests/`.
- `frontend/`: app Next.js 14 con App Router (`frontend/app/`), componentes UI en `frontend/components/`, utilidades en `frontend/lib/`.
- `database/`: migraciones SQL en `database/migrations/`.
- `docs/`: arquitectura, API, tareas y bugs (`ARCHITECTURE.md`, `API_DOCUMENTATION.md`, `TASK.md`, `BUGS.md`).
  - `docs/modal-sdxl-lora-worker/`: Worker files para Modal Serverless SDXL + LoRA.
  - `docs/MODAL_SDXL_LORA_DEPLOYMENT.md`: GuÃ­a completa de deployment.
- `.ai/` y `.claude/`: procesos/guÃ­as de agentes (referencia, no cÃ³digo runtime).

## GeneraciÃ³n de ImÃ¡genes con LoRA DinÃ¡mico

### Arquitectura
**Provider**: `modal_sdxl_lora` (nuevo endpoint serverless dedicado)
- Base model: SDXL (configurable por env var `MODEL_ID` en Modal)
- LoRA por request: Descargadas desde Cloudflare R2 (presigned URLs)
- Output: PNG base64 (opcional guardar a R2)

### Flujo Actual
1. Frontend solicita generaciÃ³n (`POST /api/v1/content/generate`)
2. Backend consulta avatar + LoRA URL en Supabase
3. Genera presigned GET URL de R2 para .safetensors
4. Llama `lora_inference_engine.generate_image_with_lora()` con provider `modal_sdxl_lora`
5. Cliente Modal (`modal_sdxl_lora_client.py`) envÃ­a request a Modal Serverless
6. Worker descarga LoRA, carga modelo, genera imagen, unfuses LoRA (sin contaminaciÃ³n)
7. Worker retorna image_base64
8. Backend opcionalmente guarda PNG a R2 y retorna image_url

### Nuevo CÃ³digo Backend
- `backend/app/services/modal_sdxl_lora_client.py`: Cliente para Modal Serverless SDXL + LoRA
- ModificaciÃ³n: `backend/app/services/lora_inference.py` - nuevo provider `modal_sdxl_lora`

### Env Vars (Backend)
```bash
# Modal Serverless SDXL LoRA
MODAL_SDXL_LORA_ENDPOINT_ID=<endpoint-id>  # Obtener de Modal console
MODAL_API_KEY=<api-key>
MODAL_MODE=async                            # "async" o "sync"
MODAL_POLL_SECONDS=2
MODAL_TIMEOUT_SECONDS=300

# Provider
LORA_PROVIDER=modal_sdxl_lora                # Usar nuevo endpoint

# R2 (para presigned URLs y guardar resultados)
R2_ENDPOINT_URL=https://<account>.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=<key>
R2_SECRET_ACCESS_KEY=<secret>
R2_BUCKET_NAME=vixenbliss
R2_PUBLIC_URL=https://cdn.yourdomain.com     # Optional
```

## Deployment de Modal Worker

Ver [docs/MODAL_SDXL_LORA_DEPLOYMENT.md](docs/MODAL_SDXL_LORA_DEPLOYMENT.md) para instrucciones completas.

**Resumen**:
1. Fork template Modal â†’ subir `rp_handler.py`, `requirements.txt`, `Dockerfile`
2. Modal Console â†’ Serverless â†’ New Endpoint â†’ Import Git Repository
3. Seleccionar GPU (24GB mÃ­n), setear `MODEL_ID` env
4. Deploy y obtener Endpoint ID
5. Setear env vars en backend

## Comandos de Build, Test y Desarrollo
Backend (desde `backend/`):
- `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` â€“ levanta el API.
- `celery -A app.workers.celery_app worker --loglevel=info` â€“ inicia workers.
- `pytest` / `pytest --cov=app --cov-report=html` â€“ tests con coverage.
- `black .`, `flake8 app/`, `mypy app/` â€“ formato, lint y type-check.

Frontend (desde `frontend/`):
- `npm run dev` â€“ servidor de desarrollo.
- `npm run build` / `npm start` â€“ build y preview.
- `npm run lint` â€“ linting de Next.
- `npm test` / `npm run test:coverage` â€“ tests Jest.

## Estilo de CÃ³digo y Convenciones de Nombres
- Python: 4 espacios, type hints obligatorios, Pydantic para schemas; I/O async en funciones `async`.
- TypeScript/React: 2 espacios, tipos estrictos; `camelCase` para variables, `PascalCase` para componentes.
- Herramientas: `black` para Python, `eslint`/`next lint` para frontend.

## GuÃ­as de Testing
- Backend: `pytest` con objetivo de coverage >80% (ver `SETUP.md`).
- Frontend: Jest + React Testing Library (ver `frontend/__tests__/`).
- Nombres de tests descriptivos (ej.: `test_avatar_creation.py`, `page.test.tsx`).

## Commits y Pull Requests
- ConvenciÃ³n de commits: `feat:`, `fix:`, `chore:` (ver `git log`).
- PRs: resumen corto, issue/tarea vinculada si aplica, screenshots para cambios UI.
- Mencionar migraciones, nuevos env vars o workers en la descripciÃ³n del PR.

## Seguridad y ConfiguraciÃ³n
- No commitear secretos; usar `.env`.
- Config Modal/ComfyUI y R2 por env vars (ver `SETUP.md`, `SETUP_CLOUDFLARE_MODAL.md`, `MODAL_SDXL_LORA_DEPLOYMENT.md`).
