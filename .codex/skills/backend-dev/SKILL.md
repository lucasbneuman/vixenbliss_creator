---
name: backend-dev
description: Ejecutar cambios backend FastAPI/Python de forma incremental y reversible para VixenBliss. Usar cuando la tarea involucre endpoints, servicios, schemas o logica de backend.
---

# Backend Dev

## Checklist
- [ ] Do not break API contracts.
- [ ] Run tests.
- [ ] Ejecutar lint y typecheck antes de cerrar.
- [ ] Si el cambio es sensible, usar feature flag o endpoint versionado.

## Referencias
- [`.ai/context/*`](../../../.ai/context/)
- [`docs/*`](../../../docs/)
- [`docs/api-contracts/v1_endpoints.md`](../../../docs/api-contracts/v1_endpoints.md)
- [`docs/api-contracts/breaking-change-policy.md`](../../../docs/api-contracts/breaking-change-policy.md)
