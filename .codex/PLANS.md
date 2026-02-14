# ExecPlan Template - Codex Operating System

## Propósito

Este documento define la plantilla **ExecPlan** usada por los agentes Codex para planificar y ejecutar tareas de forma segura, verificable y documentada.

Un ExecPlan es una guía **Step-by-Step** que asegura:
- ✅ Entendimiento completo del alcance
- ✅ Identificación de riesgos antes de ejecutar
- ✅ Estimación de esfuerzo y duración
- ✅ Validación incremental
- ✅ Trazabilidad de cambios

## Estructura de ExecPlan

```markdown
# ExecPlan [TICKET-ID]: [Descripción corta]

## Context
- **Assignee**: [Agent Name]
- **Type**: [Feature/Bug/Refactor/Chore]
- **Severity/Priority**: [If bug: Critical/High/Medium/Low]
- **Estimate**: [Time estimate - 1h, 4h, 1d, 3d, 1w]
- **Related**: [Links a issues, tasks, discussions]

## Objective
[1-3 párrafos explicando QUÉ se necesita lograr y POR QUÉ]

## Scope (In/Out)
### In Scope
- [ ] Item 1
- [ ] Item 2
### Out of Scope
- Item que NO se incluye (y por qué)

## Technical Approach
[Explicar cómo se implementará. Incluir:]
- Qué files se tocarán
- Qué APIs se usarán
- Qué dependencias se necesitan
- Qué assumptions se hacen

## Risk Assessment

### Breaking Changes Risk
- [ ] Cambios a APIs existentes
- [ ] Cambios a esquemas database
- [ ] Cambios a comportamiento default
- [ ] Cambios a autenticación/seguridad

**Risk Level**: [Green/Yellow/Red]
**Mitigation**: [Feature flags, versioning, review process, etc.]

### Compatibility
- **Min Python**: [3.11+]
- **Min Node.js**: [18+]
- **DB Migrations**: [Yes/No - si sí, listar]
- **Env Vars nuevas**: [Si hay, listarlas]

## Execution Plan

### Phase 1: Setup & Validation
- [ ] Crear feature branch
- [ ] Verificar que no hay conflictos de merge
- [ ] Verificar env local funciona
- [ ] Listar archivos a modificar

### Phase 2: Implementation
- [ ] Implementar feature/fix en código
- [ ] Agregar tests unitarios
- [ ] Actualizar docstrings/comentarios
- [ ] Validar syntax (black, flake8, mypy, eslint)

### Phase 3: Testing
- [ ] Tests locales pasan (`pytest`, `npm test`)
- [ ] Lint/type-check pasan
- [ ] Código coverage >80% (si es sistema crítico)
- [ ] Manual testing en navegador (si aplica)

### Phase 4: Documentation
- [ ] Actualizar `docs/API_DOCUMENTATION.md` (si hay nuevos endpoints)
- [ ] Actualizar `docs/SYSTEM_MAP.md` (si hay cambios de arquitectura)
- [ ] Agregar examples en docstrings
- [ ] Registrar en `docs/TASK.md` (2 líneas)

### Phase 5: PR & Review
- [ ] Crear PR con descripción detallada
- [ ] Referenciar issue/task de Notion
- [ ] Esperar review de especialista relevante
- [ ] Resolver comentarios de review
- [ ] Obtener approval antes de mergear

### Phase 6: Merge & Validation
- [ ] Mergear a `main` (después del approval)
- [ ] Verificar que CI/CD pipeline pasa
- [ ] Verificar que staging deploy completó
- [ ] QA tester verifica en staging (si aplica)

## Files to Modify

| File | Change | Risk | Notes |
|------|--------|------|-------|
| `backend/app/api/...py` | [Add/Modify] | [Low/Med/High] | [reason] |
| `frontend/app/...tsx` | [Add/Modify] | [Low/Med/High] | [reason] |
| `database/migrations/...sql` | [New] | [Med/High] | [reason] |

## Testing Strategy

### Unit Tests
```
pytest backend/tests/test_[module].py
# Objetivo: >80% coverage
```

### Integration Tests
```
pytest backend/tests/integration/test_[feature].py
# Objetivo: Verificar flujo end-to-end (API → DB → Response)
```

### Manual Testing Checklist
- [ ] Feature funciona en modo normal
- [ ] Feature funciona con edge cases (vacío, nulo, máximo, mínimo)
- [ ] Error handling funciona (exceptions loguean, responde con error code correcto)
- [ ] Performance aceptable (P95 < 5s para operaciones blocking)

## Rollback Plan

Si algo falla en production, pasos para rollback:
```bash
# 1. Si es código
git revert [commit-sha]
git push origin main
# (Coolify redeploy automático)

# 2. Si es DB
# Ejecutar migrations down.sql correspondientes
psql $DATABASE_URL < database/migrations/000X_[name].down.sql

# 3. Comunicación
# Notificar a Scrum Master y stakeholders
```

## Timeline

| Phase | Est. Duration | Start | End |
|-------|---------------|-------|-----|
| Setup & Validation | [time] | | |
| Implementation | [time] | | |
| Testing | [time] | | |
| Documentation | [time] | | |
| PR & Review | [time] | | |
| Merge & Validation | [time] | | |
| **TOTAL** | [time] | | |

## Sign-Off

- [ ] Implementador (agent) completó todas las fases
- [ ] Tests pasan con coverage >80%
- [ ] Lint/type-check pasan
- [ ] PR aprobado por especialista relevante
- [ ] Mergead a main
- [ ] Registrado en TASK.md

**Completado por**: [Agent Name]  
**Fecha**: [YYYY-MM-DD]  
**PR Link**: [https://github.com/.../pull/XXX]  

---

## Examples

### Ejemplo 1: Nuevo Endpoint API

```markdown
# ExecPlan E02-001: Implementar POST /api/v1/avatars/generate

## Context
- **Assignee**: Backend Dev
- **Type**: Feature
- **Priority**: High
- **Estimate**: 1d
- **Related**: Notion E02-001

## Objective
Implementar endpoint para generar avatares usando Replicate SDXL con presigned URLs de R2.
El endpoint debe:
1. Recibir prompt + niche en request
2. Consultar R2 para obtener LoRA del avatar
3. Llamar a modal_sdxl_lora provider con LoRA presigned URL
4. Retornar PNG base64 o URL a R2

## Scope (In/Out)
### In Scope
- [ ] POST /api/v1/avatars/{avatar_id}/generate endpoint
- [ ] Request schema validation (Pydantic)
- [ ] Response schema (image_base64 o image_url)
- [ ] Error handling (invalid avatar, LoRA not found, timeout)
- [ ] Unit tests (5 tests, >80% coverage)
### Out of Scope
- Batch generation (= E02-002)
- Presigned URL generation (= ya existe en R2 service)

## Technical Approach
- Agregar nuevo route en `backend/app/api/content.py`
- Usar `lora_inference_engine.generate_image_with_lora()` existente
- Provider: `modal_sdxl_lora` (ya implementado)
- Request timeout: 300s (5 min)

## Risk Assessment

### Breaking Changes Risk
- [ ] No hay cambios a APIs existentes
- [ ] Nuevo endpoint (no breaking)

**Risk Level**: Green
**Mitigation**: Endpoint es versionado como /v1 (compatible forward)

## Files to Modify

| File | Change | Risk |
|------|--------|------|
| `backend/app/schemas/content.py` | Add GenerateImageRequest | Low |
| `backend/app/api/content.py` | Add POST /avatars/{id}/generate | Low |
| `backend/tests/test_...` | Add 5 unit tests | Low |

## Testing Strategy

### Unit Tests
- test_generate_image_valid_avatar
- test_generate_image_invalid_avatar
- test_generate_image_timeout
- test_generate_image_lora_not_found
- test_generate_image_response_schema

### Manual Testing
- [ ] Endpoint responde en <300s con avatar válido
- [ ] Endpoint retorna 404 si avatar_id no existe
- [ ] Endpoint retorna 408 si timeout

## Timeline
- Setup: 30min
- Implementation: 4h
- Testing: 2h
- Docs: 30min
- Review: 1h
- **Total**: 8h ~ 1 day
```

---

**Plantilla última actualización**: 2026-02-11  
**Versión**: 1.0  
**Mantendedor**: Scrum Master Agent
