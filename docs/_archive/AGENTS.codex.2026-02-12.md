# ARCHIVED

Archivo archivado el 2026-02-12 durante consolidacion de entrypoint de contexto.
Fuente original: /.codex/AGENTS.md

---
# Codex Operating System - Governance

## Proposito

Este documento define la gobernanza de VixenBliss Creator en formato Codex-first.
La ejecucion se organiza por modos de trabajo y skills, sin subagentes ni invocacion automatica de agentes.

## Sistemas Codex

El repositorio se organiza en 5 sistemas independientes (ver `docs/SYSTEM_MAP.md`):

1. Sistema de Generacion de Identidades
2. Sistema de Produccion de Contenido
3. Sistema de Distribucion Automatizada
4. Sistema de Monetizacion Multi-capa
5. Sistema de Chatbot Lead Generation

## Collaboration Modes

### 1) Delivery Mode

**Proposito**: Implementar cambios de producto de forma incremental y verificable, sin romper contratos existentes.

**Checklist**:
- Confirmar alcance y contratos afectados antes de editar.
- Activar skills segun dominio del cambio:
  - `backend-dev` para endpoints/servicios/schemas en `backend/app/`.
  - `frontend-dev` para UI e integracion en `frontend/app/`, `frontend/components/`, `frontend/lib/`.
  - `database-migrations` para cambios SQL en `database/migrations/`.
  - `modal-lora-pipeline` para flujo SDXL + LoRA en `backend/app/services/` y docs relacionadas.
- Leer primero los archivos de contrato relevantes:
  - `docs/API_DOCUMENTATION.md`
  - `docs/ARCHITECTURE.md`
  - `docs/TASK.md`
  - `docs/BUGS.md` (si hay regresion o fix)
- Implementar con cambios pequenos y reversibles.
- Ejecutar validaciones locales aplicables (tests/lint/type-check).
- Documentar cambios contractuales o de comportamiento en docs.

**Outputs esperados**:
- Diff acotado y legible.
- Tests/lint/type-check reportados.
- Notas de compatibilidad y rollback cuando aplique.

### 2) Review Mode

**Proposito**: Evaluar riesgo tecnico, regresiones y cumplimiento de contratos antes de merge.

**Checklist**:
- Revisar cambios contra contratos API y comportamiento actual.
- Priorizar hallazgos por severidad (critical/high/medium/low).
- Activar `qa-validation` para cobertura funcional y regresiones.
- Activar `security-review` si hay auth, pagos, secretos, inputs externos o permisos.
- Verificar que toda migracion sea reversible y segura.
- Confirmar que no hay cambios runtime ocultos fuera del alcance declarado.

**Outputs esperados**:
- Lista de hallazgos con archivo y linea.
- Riesgos abiertos y supuestos explicitados.
- Recomendacion de merge/no-merge con condiciones concretas.

### 3) Docs and Governance Mode

**Proposito**: Mantener documentacion operativa, contratos y politicas del repo alineadas con el estado real.

**Checklist**:
- Actualizar `docs/API_DOCUMENTATION.md` si se agregan endpoints o campos.
- Actualizar `docs/ARCHITECTURE.md` si cambia diseno de sistema.
- Registrar progreso en `docs/TASK.md` y bugs en `docs/BUGS.md`.
- Si se ajustan reglas operativas, actualizar `.codex/AGENTS.md`.
- Evitar instrucciones de subagentes; usar siempre modos + skills.

**Outputs esperados**:
- Documentacion consistente con el codigo.
- Historial de decisiones y cambios trazable.
- Politicas claras y ejecutables por Codex.

## Non-breaking Contract Discipline (always)

Estas reglas aplican siempre, sin excepcion:

- No romper endpoints existentes en `/api/v1/...`.
- No cambiar request/response schema de forma incompatible.
- No remover status codes esperados por clientes.
- No cambiar semantica observable sin versionado o flag.
- Si hay cambio de contrato, crear nuevo endpoint versionado (`/api/v2/...` o `/api/experimental/...`).
- Mantener compatibilidad backward en campos nuevos (opcionales por defecto).

## When Uncertain: Add New Endpoint or Feature Flag

Si existe duda tecnica o de impacto:

- Preferir nuevo endpoint en lugar de alterar comportamiento existente.
- O introducir feature flag con default seguro (`false`) y fallback al flujo actual.
- Probar ambos caminos (flag off/on) y documentar rollback.
- Escalar para decision solo despues de proponer opcion no-ruptura.

## Convenciones de Codigo

### Python (Backend + LLM)
- 4 espacios de indentacion.
- Type hints en todas las funciones.
- Async/await para I/O.
- Pydantic para schemas/validacion.
- Tests con pytest (objetivo >80% coverage).

### TypeScript/React (Frontend)
- 2 espacios de indentacion.
- `strict: true` en `tsconfig`.
- Tipos explicitos en componentes y utilidades.
- Tests con Jest + React Testing Library.

### SQL (Database)
- Migraciones reversibles (up/down).
- Indices para claves foraneas y consultas frecuentes.
- Cambios de schema solo via migraciones revisadas.

## Prohibiciones Explicitas

- No commitear `.env` ni secretos.
- No cambiar schema de database sin migracion y review.
- No mergear sin tests/lint/type-check en estado valido.
- No deploy a produccion sin proceso de release definido.

## Archivos de Control

- `docs/TASK.md`: registro de tareas.
- `docs/BUGS.md`: registro de bugs y fix.
- `docs/ARCHITECTURE.md`: decisiones de arquitectura.
- `docs/API_DOCUMENTATION.md`: contratos API.
- `docs/SYSTEM_MAP.md`: mapeo sistemas -> modulos.
- `.codex/AGENTS.md`: governance Codex-first.
- `.codex/PLANS.md`: plantilla de ejecucion.
- `.codex/skills/`: skills reutilizables.

---

Ultima actualizacion: 2026-02-12
Version: 2.0
Mantenedor: Codex Governance
