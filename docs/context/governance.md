# Governance (Absorbido de .codex/AGENTS.md)

Estado: activo
Fuente absorbida: `.codex/AGENTS.md` (version previa)
Fecha de absorcion: 2026-02-12

## Proposito

Define la gobernanza operativa en formato Codex-first.
La ejecucion se organiza por modos y skills, sin subagentes ni invocaciones automaticas.

## Sistemas

Ver mapeo completo en `docs/SYSTEM_MAP.md`.

- S1: Generacion de Identidades
- S2: Produccion de Contenido
- S3: Distribucion Automatizada
- S4: Monetizacion Multi-capa
- S5: Chatbot Lead Generation

## Modos de Colaboracion

### Delivery Mode

Checklist:
- Confirmar alcance y contrato afectado antes de editar.
- Activar skill por dominio (`backend-dev`, `frontend-dev`, `database-migrations`, `modal-lora-pipeline`).
- Revisar `docs/SYSTEM_MAP.md`, `docs/api-contracts/v1_endpoints.md`, `docs/TASK.md`, `docs/BUGS.md`.
- Revisar dependencia externa si aplica (`docs/external-systems/*`).
- Implementar cambios incrementales y reversibles.
- Correr validaciones locales aplicables.
- Documentar cualquier cambio de comportamiento.

Output esperado:
- Diff acotado.
- Resultado de tests/lint/type-check.
- Notas de rollback si aplica.

### Review Mode

Checklist:
- Revisar contra contrato y comportamiento actual.
- Priorizar hallazgos por severidad.
- Activar `qa-validation` para regresiones.
- Activar `security-review` en auth/pagos/secrets/webhooks/inputs externos.
- Verificar migraciones reversibles.
- Confirmar que no hay cambios runtime fuera de alcance.

Output esperado:
- Hallazgos con archivo/linea.
- Riesgos y supuestos abiertos.
- Recomendacion merge/no-merge condicionada.

### Docs and Governance Mode

Checklist:
- Actualizar docs cuando cambian contratos o arquitectura.
- Registrar progreso en `docs/TASK.md`.
- Registrar bugs en `docs/BUGS.md`.
- Mantener reglas en `/AGENTS.md` y evitar duplicacion.

## Non-Breaking Contract Discipline

- No romper endpoints `/api/v1/...`.
- No cambiar schemas request/response de forma incompatible.
- No remover status codes esperados por clientes.
- No alterar semantica sin versionado o flag.
- Nuevos campos deben ser backward compatible (opcionales por defecto).

## When Uncertain

- Preferir endpoint nuevo sobre mutacion de comportamiento existente.
- O usar feature flag con default seguro.
- Probar ambos caminos y documentar rollback.

## Convenciones Tecnicas

### Python
- 4 espacios.
- Type hints.
- Async para I/O.
- Pydantic en validacion.
- Pytest para testeo.

### TypeScript/React
- 2 espacios.
- `strict: true`.
- Tipos explicitos.
- Jest + RTL.

### SQL
- Migraciones reversibles.
- Indices en claves y consultas frecuentes.

## Prohibiciones

- No commitear secretos.
- No cambiar schema sin migracion + review.
- No mergear sin validaciones minimas.

## Referencias de Control

- `docs/TASK.md`
- `docs/BUGS.md`
- `docs/SYSTEM_MAP.md`
- `docs/external-systems/README.md`
- `docs/external-systems/modal-sdxl-lora.md`
- `docs/api-contracts/v1_endpoints.md`
- `docs/api-contracts/breaking-change-policy.md`
