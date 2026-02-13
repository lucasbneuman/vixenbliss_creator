# Backend Local Rules

Este archivo agrega solo reglas locales para backend.
La gobernanza global vive en `/AGENTS.md`.

- Mantener compatibilidad en `/api/v1/*`.
- Cambios de schema solo via `database/migrations/` revisadas.
- Validacion minima esperada: `pytest`, `mypy app/`, `flake8 app/`.
- No tocar proveedores externos sin fallback documentado.

Referencia:
- `docs/SYSTEM_MAP.md`
- `docs/api-contracts/v1_endpoints.md`
