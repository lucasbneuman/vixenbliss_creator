# Inventario del Proyecto: VixenBliss Creator

Generado automaticamente: 2026-02-11 20:44:14

## Resumen de la Aplicacion

VixenBliss Creator es una plataforma SaaS para crear y operar avatares AI orientados a redes sociales. El sistema cubre la generacion de identidad, produccion de contenido visual, automatizacion de publicacion y flujos de monetizacion.

Arquitectura principal:
- Frontend en Next.js 14 (App Router) para panel de gestion y flujos de usuario.
- Backend en FastAPI con workers Celery para logica de negocio y procesamiento asincrono.
- Base de datos PostgreSQL/Supabase con migraciones SQL y soporte de vectores (pgvector).
- Integracion AI para generacion de imagenes con SDXL + LoRA dinamico via Modal Serverless.
- Storage en Cloudflare R2 para LoRAs, assets y resultados generados.

Flujo de generacion LoRA (alto nivel): frontend solicita generacion, backend obtiene avatar y LoRA, firma URL de R2, invoca provider modal_sdxl_lora, el worker genera imagen y backend retorna o almacena resultado.

## Cobertura del Inventario

- Carpetas listadas: 37
- Archivos listados: 164
- Se excluyen carpetas de entorno/cache para mantener el inventario util: `.git/`, `.venv/`, `venv/`, `node_modules/`, `.pytest_cache/`, `__pycache__/`, `.next/`.
- Se ignoran entradas invalidas del sistema como `nul`.

## Estructura Completa (Ruta y Carpeta Padre)

| Tipo | Ruta | Carpeta padre |
|---|---|---|
| Carpeta | `.ai` | `.` |
| Carpeta | `.ai/context` | `.ai` |
| Archivo | `.ai/context/coding-standards.md` | `.ai/context` |
| Archivo | `.ai/context/project-rules.md` | `.ai/context` |
| Archivo | `.ai/context/security-guidelines.md` | `.ai/context` |
| Carpeta | `.claude` | `.` |
| Carpeta | `.claude/agents` | `.claude` |
| Archivo | `.claude/agents/backend-dev.md` | `.claude/agents` |
| Archivo | `.claude/agents/database-engineer.md` | `.claude/agents` |
| Archivo | `.claude/agents/devops-engineer.md` | `.claude/agents` |
| Archivo | `.claude/agents/frontend-dev.md` | `.claude/agents` |
| Archivo | `.claude/agents/qa-tester.md` | `.claude/agents` |
| Archivo | `.claude/agents/README.md` | `.claude/agents` |
| Archivo | `.claude/agents/scrum-master.md` | `.claude/agents` |
| Archivo | `.coolify.json` | `.` |
| Archivo | `.env` | `.` |
| Carpeta | `.github` | `.` |
| Carpeta | `.github/workflows` | `.github` |
| Archivo | `.github/workflows/deploy.yml` | `.github/workflows` |
| Archivo | `.gitignore` | `.` |
| Archivo | `AGENTS.md` | `.` |
| Carpeta | `backend` | `.` |
| Archivo | `backend/.dockerignore` | `backend` |
| Archivo | `backend/.env` | `backend` |
| Archivo | `backend/.env.example` | `backend` |
| Archivo | `backend/.env.example.modal-sdxl-lora` | `backend` |
| Carpeta | `backend/app` | `backend` |
| Carpeta | `backend/app/api` | `backend/app` |
| Archivo | `backend/app/api/__init__.py` | `backend/app/api` |
| Archivo | `backend/app/api/content.py` | `backend/app/api` |
| Archivo | `backend/app/api/conversations.py` | `backend/app/api` |
| Archivo | `backend/app/api/costs.py` | `backend/app/api` |
| Archivo | `backend/app/api/distribution.py` | `backend/app/api` |
| Archivo | `backend/app/api/identities.py` | `backend/app/api` |
| Archivo | `backend/app/api/loras.py` | `backend/app/api` |
| Archivo | `backend/app/api/premium.py` | `backend/app/api` |
| Archivo | `backend/app/api/storage.py` | `backend/app/api` |
| Archivo | `backend/app/api/video.py` | `backend/app/api` |
| Archivo | `backend/app/api/webhooks.py` | `backend/app/api` |
| Archivo | `backend/app/database.py` | `backend/app` |
| Archivo | `backend/app/main.py` | `backend/app` |
| Carpeta | `backend/app/models` | `backend/app` |
| Archivo | `backend/app/models/__init__.py` | `backend/app/models` |
| Archivo | `backend/app/models/avatar.py` | `backend/app/models` |
| Archivo | `backend/app/models/content_piece.py` | `backend/app/models` |
| Archivo | `backend/app/models/conversation.py` | `backend/app/models` |
| Archivo | `backend/app/models/identity_component.py` | `backend/app/models` |
| Archivo | `backend/app/models/lora_model.py` | `backend/app/models` |
| Archivo | `backend/app/models/social_account.py` | `backend/app/models` |
| Archivo | `backend/app/models/user.py` | `backend/app/models` |
| Carpeta | `backend/app/schemas` | `backend/app` |
| Archivo | `backend/app/schemas/__init__.py` | `backend/app/schemas` |
| Archivo | `backend/app/schemas/content.py` | `backend/app/schemas` |
| Archivo | `backend/app/schemas/identity.py` | `backend/app/schemas` |
| Archivo | `backend/app/schemas/lora.py` | `backend/app/schemas` |
| Carpeta | `backend/app/services` | `backend/app` |
| Archivo | `backend/app/services/__init__.py` | `backend/app/services` |
| Archivo | `backend/app/services/ab_testing.py` | `backend/app/services` |
| Archivo | `backend/app/services/ai_providers.py` | `backend/app/services` |
| Archivo | `backend/app/services/batch_processor.py` | `backend/app/services` |
| Archivo | `backend/app/services/bio_generator.py` | `backend/app/services` |
| Archivo | `backend/app/services/chatbot_agent.py` | `backend/app/services` |
| Archivo | `backend/app/services/comfyui_client.py` | `backend/app/services` |
| Archivo | `backend/app/services/content_safety.py` | `backend/app/services` |
| Archivo | `backend/app/services/conversion_tracking.py` | `backend/app/services` |
| Archivo | `backend/app/services/cost_tracker.py` | `backend/app/services` |
| Archivo | `backend/app/services/cost_tracking.py` | `backend/app/services` |
| Archivo | `backend/app/services/dataset_builder.py` | `backend/app/services` |
| Archivo | `backend/app/services/dm_webhook_handler.py` | `backend/app/services` |
| Archivo | `backend/app/services/health_monitoring.py` | `backend/app/services` |
| Archivo | `backend/app/services/hook_generator.py` | `backend/app/services` |
| Archivo | `backend/app/services/identity_service.py` | `backend/app/services` |
| Archivo | `backend/app/services/instagram_integration.py` | `backend/app/services` |
| Archivo | `backend/app/services/lead_scoring.py` | `backend/app/services` |
| Archivo | `backend/app/services/lora_inference.py` | `backend/app/services` |
| Archivo | `backend/app/services/lora_training.py` | `backend/app/services` |
| Archivo | `backend/app/services/modal_sdxl_lora_client.py` | `backend/app/services` |
| Archivo | `backend/app/services/persona_engine.py` | `backend/app/services` |
| Archivo | `backend/app/services/premium_packs.py` | `backend/app/services` |
| Archivo | `backend/app/services/prompt_enhancer.py` | `backend/app/services` |
| Archivo | `backend/app/services/prompt_presets.py` | `backend/app/services` |
| Archivo | `backend/app/services/smart_scheduler.py` | `backend/app/services` |
| Archivo | `backend/app/services/social_integration.py` | `backend/app/services` |
| Archivo | `backend/app/services/storage.py` | `backend/app/services` |
| Archivo | `backend/app/services/template_library.py` | `backend/app/services` |
| Archivo | `backend/app/services/tiktok_integration.py` | `backend/app/services` |
| Archivo | `backend/app/services/video_generation.py` | `backend/app/services` |
| Archivo | `backend/app/services/voice_synthesis.py` | `backend/app/services` |
| Carpeta | `backend/app/workers` | `backend/app` |
| Archivo | `backend/app/workers/__init__.py` | `backend/app/workers` |
| Archivo | `backend/app/workers/celery_app.py` | `backend/app/workers` |
| Archivo | `backend/app/workers/tasks.py` | `backend/app/workers` |
| Carpeta | `backend/config` | `backend` |
| Archivo | `backend/config/vixenbliss.json` | `backend/config` |
| Archivo | `backend/config/vixenbliss_video_svd.json` | `backend/config` |
| Archivo | `backend/Dockerfile` | `backend` |
| Archivo | `backend/requirements.txt` | `backend` |
| Archivo | `backend/requirements-dev.txt` | `backend` |
| Archivo | `backend/test_modal_client_local.py` | `backend` |
| Carpeta | `backend/tests` | `backend` |
| Archivo | `backend/tests/conftest.py` | `backend/tests` |
| Archivo | `backend/tests/test_main.py` | `backend/tests` |
| Archivo | `backend/vixenbliss_dev.db` | `backend` |
| Archivo | `CODEX_PROMPT_MODAL.md` | `.` |
| Carpeta | `database` | `.` |
| Carpeta | `database/migrations` | `database` |
| Archivo | `database/schema.sql` | `database` |
| Archivo | `docker-compose.yml` | `.` |
| Carpeta | `docs` | `.` |
| Archivo | `docs/API_DOCUMENTATION.md` | `docs` |
| Archivo | `docs/ARCHITECTURE.md` | `docs` |
| Archivo | `docs/BUGS.md` | `docs` |
| Archivo | `docs/PROJECT_INVENTORY.md` | `docs` |
| Archivo | `docs/TASK.md` | `docs` |
| Carpeta | `frontend` | `.` |
| Archivo | `frontend/.dockerignore` | `frontend` |
| Archivo | `frontend/.env.example` | `frontend` |
| Archivo | `frontend/.env.local` | `frontend` |
| Carpeta | `frontend/.swc` | `frontend` |
| Carpeta | `frontend/.swc/plugins` | `frontend/.swc` |
| Carpeta | `frontend/.swc/plugins/v7_windows_x86_64_0.106.15` | `frontend/.swc/plugins` |
| Carpeta | `frontend/__tests__` | `frontend` |
| Archivo | `frontend/__tests__/page.test.tsx` | `frontend/__tests__` |
| Carpeta | `frontend/app` | `frontend` |
| Carpeta | `frontend/app/avatars` | `frontend/app` |
| Archivo | `frontend/app/avatars/page.tsx` | `frontend/app/avatars` |
| Carpeta | `frontend/app/content` | `frontend/app` |
| Archivo | `frontend/app/content/page.tsx` | `frontend/app/content` |
| Carpeta | `frontend/app/distribution` | `frontend/app` |
| Archivo | `frontend/app/distribution/page.tsx` | `frontend/app/distribution` |
| Carpeta | `frontend/app/factory` | `frontend/app` |
| Archivo | `frontend/app/factory/page.tsx` | `frontend/app/factory` |
| Archivo | `frontend/app/globals.css` | `frontend/app` |
| Archivo | `frontend/app/layout.tsx` | `frontend/app` |
| Carpeta | `frontend/app/models` | `frontend/app` |
| Archivo | `frontend/app/models/page.tsx` | `frontend/app/models` |
| Archivo | `frontend/app/page.tsx` | `frontend/app` |
| Carpeta | `frontend/app/revenue` | `frontend/app` |
| Archivo | `frontend/app/revenue/page.tsx` | `frontend/app/revenue` |
| Carpeta | `frontend/components` | `frontend` |
| Archivo | `frontend/components.json` | `frontend` |
| Archivo | `frontend/components/action-button.tsx` | `frontend/components` |
| Archivo | `frontend/components/batch-generation-dialog.tsx` | `frontend/components` |
| Archivo | `frontend/components/error-boundary.tsx` | `frontend/components` |
| Archivo | `frontend/components/health-indicator.tsx` | `frontend/components` |
| Archivo | `frontend/components/loading-state.tsx` | `frontend/components` |
| Archivo | `frontend/components/metric-card.tsx` | `frontend/components` |
| Archivo | `frontend/components/model-table.tsx` | `frontend/components` |
| Archivo | `frontend/components/page-transition.tsx` | `frontend/components` |
| Archivo | `frontend/components/revenue-chart.tsx` | `frontend/components` |
| Archivo | `frontend/components/sidebar.tsx` | `frontend/components` |
| Archivo | `frontend/components/top-nav.tsx` | `frontend/components` |
| Carpeta | `frontend/components/ui` | `frontend/components` |
| Archivo | `frontend/components/ui/alert.tsx` | `frontend/components/ui` |
| Archivo | `frontend/components/ui/badge.tsx` | `frontend/components/ui` |
| Archivo | `frontend/components/ui/button.tsx` | `frontend/components/ui` |
| Archivo | `frontend/components/ui/card.tsx` | `frontend/components/ui` |
| Archivo | `frontend/components/ui/dialog.tsx` | `frontend/components/ui` |
| Archivo | `frontend/components/ui/dropdown-menu.tsx` | `frontend/components/ui` |
| Archivo | `frontend/components/ui/input.tsx` | `frontend/components/ui` |
| Archivo | `frontend/components/ui/label.tsx` | `frontend/components/ui` |
| Archivo | `frontend/components/ui/progress.tsx` | `frontend/components/ui` |
| Archivo | `frontend/components/ui/select.tsx` | `frontend/components/ui` |
| Archivo | `frontend/components/ui/separator.tsx` | `frontend/components/ui` |
| Archivo | `frontend/components/ui/table.tsx` | `frontend/components/ui` |
| Archivo | `frontend/Dockerfile` | `frontend` |
| Carpeta | `frontend/hooks` | `frontend` |
| Archivo | `frontend/hooks/use-api.ts` | `frontend/hooks` |
| Archivo | `frontend/INDUSTRIAL_UI.md` | `frontend` |
| Archivo | `frontend/jest.config.js` | `frontend` |
| Archivo | `frontend/jest.setup.js` | `frontend` |
| Carpeta | `frontend/lib` | `frontend` |
| Carpeta | `frontend/lib/api` | `frontend/lib` |
| Archivo | `frontend/lib/api/avatars.ts` | `frontend/lib/api` |
| Archivo | `frontend/lib/api/client.ts` | `frontend/lib/api` |
| Archivo | `frontend/lib/api/content.ts` | `frontend/lib/api` |
| Archivo | `frontend/lib/api/costs.ts` | `frontend/lib/api` |
| Archivo | `frontend/lib/api/index.ts` | `frontend/lib/api` |
| Archivo | `frontend/lib/errors.ts` | `frontend/lib` |
| Archivo | `frontend/lib/transformers.ts` | `frontend/lib` |
| Archivo | `frontend/lib/utils.ts` | `frontend/lib` |
| Archivo | `frontend/next.config.js` | `frontend` |
| Archivo | `frontend/next-env.d.ts` | `frontend` |
| Archivo | `frontend/package.json` | `frontend` |
| Archivo | `frontend/package-lock.json` | `frontend` |
| Archivo | `frontend/QUICK_START.md` | `frontend` |
| Archivo | `frontend/README.md` | `frontend` |
| Archivo | `frontend/tailwind.config.ts` | `frontend` |
| Archivo | `frontend/tsconfig.json` | `frontend` |
| Archivo | `frontend/tsconfig.tsbuildinfo` | `frontend` |
| Carpeta | `frontend/types` | `frontend` |
| Archivo | `frontend/types/api.ts` | `frontend/types` |
| Archivo | `frontend/types/avatar.ts` | `frontend/types` |
| Archivo | `frontend/types/content.ts` | `frontend/types` |
| Archivo | `frontend/types/lora.ts` | `frontend/types` |
| Archivo | `frontend/UX_IMPROVEMENTS.md` | `frontend` |
| Carpeta | `llm-service` | `.` |
| Archivo | `MODAL_SDXL_LORA_INTEGRATION.md` | `.` |
| Archivo | `MODAL_SUMMARY.md` | `.` |
| Archivo | `README.md` | `.` |
| Archivo | `SETUP.md` | `.` |
