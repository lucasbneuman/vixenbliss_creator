# AGENTS Router (Entrypoint Unico)

Este archivo es el entrypoint de contexto para Codex en este repositorio.
Objetivo: enrutamiento rapido por sistema, reglas non-breaking y control de riesgo.

## Ambito

- Aplica a todo el repo salvo que un AGENTS local indique reglas adicionales.
- Prioridad de lectura:
1. `/AGENTS.md` (router global)
2. `backend/AGENTS.md` o `frontend/AGENTS.md` (reglas locales)
3. `docs/context/*` (gobernanza y playbooks)
4. `docs/api-contracts/*` (contratos congelados)
5. `docs/SYSTEM_MAP.md` (arquitectura + mapeo funcional)
6. `docs/external-systems/*` (dependencias externas)

## Reglas Inviolables (Always-On)

- No romper contratos existentes de `/api/v1/*`.
- No eliminar endpoints, campos o status codes contratados sin versionado.
- No cambiar semantica observable sin `feature flag` o nuevo endpoint.
- No commitear secretos (`.env`, API keys, tokens, credenciales).
- No hacer cambios de schema sin migracion revisada y reversible.
- No mezclar cambios de gobernanza con cambios runtime no solicitados.
- No usar comandos destructivos de git o filesystem sin aprobacion explicita.

## Non-Breaking Discipline

- Si hay duda de compatibilidad:
1. Crear endpoint nuevo (`/api/v2/*` o `/api/experimental/*`).
2. O introducir flag con default seguro (`false`).
3. Probar camino actual y nuevo (`flag off/on`).
4. Documentar rollback y compatibilidad en docs.

## Seguridad Minima

- Validar input externo en backend (tipos, rango, formato, authz).
- Sanitizar/supervisar payloads que vienen de providers externos y webhooks.
- Evitar logs con PII o secretos; enmascarar valores sensibles.
- Revisar permisos y alcance de tokens (principio de menor privilegio).
- Para cambios en auth/pagos/webhooks: ejecutar review de seguridad.

## Regla de Testing

- Todo cambio de codigo debe intentar validacion local minima.
- Backend: `pytest`, y si aplica `mypy` + `flake8`.
- Frontend: `npm test` y `npm run lint`.
- Si no se pudo correr pruebas, explicitar motivo y riesgo residual.
- No declarar "done" sin evidencia de verificacion o limitacion documentada.

## Ruteo por Sistema (S1/S2 Prioridad)

Referencia principal: `docs/SYSTEM_MAP.md`

Prioridad operativa sugerida para triage:
1. `S1` Generacion de Identidades
2. `S2` Produccion de Contenido
3. `S3` Distribucion Automatizada
4. `S4` Monetizacion Multi-capa
5. `S5` Chatbot Lead Generation

### Router rapido (que abrir primero)

- Si toca avatar, LoRA training, dataset, identity schema:
  - Sistema: `S1`
  - Abrir: `docs/SYSTEM_MAP.md`, `docs/api-contracts/v1_endpoints.md`
- Si toca content generation, prompts, inferencia LoRA, batch:
  - Sistema: `S2`
  - Abrir: `docs/SYSTEM_MAP.md`, `docs/api-contracts/v1_endpoints.md`, `docs/external-systems/modal-sdxl-lora.md`
- Si toca publicaciones sociales, scheduler, webhooks de redes:
  - Sistema: `S3`
  - Abrir: `docs/SYSTEM_MAP.md`, `docs/api-contracts/v1_endpoints.md`
- Si toca pagos, suscripciones, revenue o Stripe:
  - Sistema: `S4`
  - Abrir: `docs/SYSTEM_MAP.md`, `docs/api-contracts/v1_endpoints.md`
- Si toca DMs, conversaciones, funnel, LangGraph:
  - Sistema: `S5`
  - Abrir: `docs/SYSTEM_MAP.md`, `docs/api-contracts/v1_endpoints.md`

## Contratos y Politicas

Leer siempre antes de tocar APIs:

- `docs/api-contracts/v1_endpoints.md`
- `docs/api-contracts/breaking-change-policy.md`

Regla de precedencia contractual:
1. `docs/api-contracts/v1_endpoints.md` (freeze contractual)
2. `docs/api-contracts/breaking-change-policy.md` (criterio de cambio)

## Contexto Operativo

- `docs/context/README.md`
- `docs/context/governance.md`
- `docs/external-systems/README.md`

Uso esperado:
- `governance.md` define modos, checklists y politica de ejecucion.
- `external-systems/*` documenta contratos con proveedores externos.
- Este `/AGENTS.md` enruta y fija guardrails globales.

## Flujo Recomendado de Ejecucion

1. Identificar sistema afectado (S1..S5).
2. Revisar contrato aplicable en `docs/api-contracts/*`.
3. Revisar dependencia externa si aplica (`docs/external-systems/*`).
4. Ejecutar cambios pequenos y reversibles.
5. Validar con tests/lint/type-check segun stack.
6. Actualizar docs operativas (`docs/TASK.md`, `docs/BUGS.md` si aplica).

## Cambio Seguro (Checklist breve)

- Alcance confirmado y acotado.
- Contrato v1 preservado.
- Riesgo de seguridad evaluado.
- Tests ejecutados o bloqueo explicado.
- Documentacion actualizada.

## AGENTS Locales

- `backend/AGENTS.md`: reglas locales de backend (sin duplicar global).
- `frontend/AGENTS.md`: reglas locales de frontend (sin duplicar global).
- `.codex/AGENTS.md`: stub de compatibilidad para redirigir aqui.

## Archivo Archivado

Historial de consolidacion:
- `docs/_archive/AGENTS.root.2026-02-12.md`
- `docs/_archive/AGENTS.codex.2026-02-12.md`


## Integridad Documental (Obligatorio)

- `docs/DOCS_POLICY.md` es regla obligatoria para cualquier cambio de documentacion.
- Toda documentacion nueva debe quedar linkeada en `docs/DOCS_INDEX.md` o en su router (`AGENTS.md`, `docs/context/*`, `docs/external-systems/*`).
- No recrear `docs/ARCHITECTURE.md` ni `docs/API_DOCUMENTATION.md`; usar fuentes activas (`docs/SYSTEM_MAP.md`, `docs/api-contracts/v1_endpoints.md`).
## Mantenimiento

- Mantener este archivo entre 100 y 250 lineas.
- Evitar duplicar playbooks largos; enlazar en su lugar.
- Toda regla nueva debe indicar archivo fuente y alcance.

---
Version: 3.2
Ultima actualizacion: 2026-02-12
Owner: Governance

