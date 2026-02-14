---
name: qa-validation
description: Validar calidad y regresiones en VixenBliss con pruebas unitarias, de contrato y smoke checks antes de merge o release.
---

# QA Validation

## Checklist
- [ ] Do not break API contracts.
- [ ] Run tests.
- [ ] Ejecutar smoke/regression para flujos afectados.
- [ ] Verificar status codes y payloads segun contrato.

## Referencias
- [`.ai/context/*`](../../../.ai/context/)
- [`docs/*`](../../../docs/)
- [`backend/tests/test_api_contracts.py`](../../../backend/tests/test_api_contracts.py)
- [`docs/api-contracts/v1_endpoints.md`](../../../docs/api-contracts/v1_endpoints.md)
