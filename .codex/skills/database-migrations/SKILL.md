---
name: database-migrations
description: Definir y revisar migraciones SQL de PostgreSQL para VixenBliss con enfoque seguro, reversible y sin romper contratos expuestos por API.
---

# Database Migrations

## Checklist
- [ ] Do not break API contracts.
- [ ] Run tests.
- [ ] Toda migracion debe ser reversible (rollback definido).
- [ ] Validar impacto en staging antes de produccion.

## Referencias
- [`.ai/context/*`](../../../.ai/context/)
- [`docs/*`](../../../docs/)
- [`database/migrations/`](../../../database/migrations/)
- [`docs/api-contracts/v1_endpoints.md`](../../../docs/api-contracts/v1_endpoints.md)
