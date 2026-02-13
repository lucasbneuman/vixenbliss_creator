---
name: security-review
description: Ejecutar revisiones de seguridad y cumplimiento para cambios en VixenBliss, incluyendo secretos, validacion de entradas y riesgo de regresiones.
---

# Security Review

## Checklist
- [ ] Do not break API contracts.
- [ ] Run tests.
- [ ] Verificar que no haya secretos hardcodeados ni en logs.
- [ ] Revisar autenticacion/autorizacion y validacion de input.

## Referencias
- [`.ai/context/*`](../../../.ai/context/)
- [`docs/*`](../../../docs/)
- [`.ai/context/security-guidelines.md`](../../../.ai/context/security-guidelines.md)
- [`docs/api-contracts/v1_endpoints.md`](../../../docs/api-contracts/v1_endpoints.md)
