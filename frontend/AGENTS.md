# Frontend Local Rules

Este archivo agrega solo reglas locales para frontend.
La gobernanza global vive en `/AGENTS.md`.

- No romper contratos consumidos desde `frontend/lib/api/*`.
- Mantener typing estricto y componentes tipados.
- Validacion minima esperada: `npm run lint`, `npm test`.
- Evitar cambios visuales globales fuera de alcance acordado.

Referencia:
- `docs/SYSTEM_MAP.md`
- `docs/api-contracts/v1_endpoints.md`
