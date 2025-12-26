# BUGS.md - VixenBliss Creator

## Registro de Bugs

### Formato
Cada bug debe registrarse en **5 líneas**:
```
[BUG-PREFIX-###] Descripción breve del bug
Location: ruta/archivo.ext:línea_número
Impact: [Severity] - Descripción detallada del impacto
Temp Fix: Arreglo temporal aplicado (o N/A si no hay)
Next: Próximos pasos para solución permanente (o N/A si ya está fixed)
```

### Prefijos por Agente
- `[BUG-SM-###]` - Scrum Master
- `[BUG-BE-###]` - Backend
- `[BUG-FE-###]` - Frontend
- `[BUG-LLM-###]` - LLM Service
- `[BUG-DB-###]` - Database
- `[BUG-OPS-###]` - DevOps
- `[BUG-QA-###]` - QA Tester

### Severity Levels
- **Critical**: System down, data loss, security breach → Fix ASAP
- **High**: Major functionality broken, blocking work → Fix within 24h
- **Medium**: Feature partially working, workaround exists → Fix within 1 week
- **Low**: Minor issue, cosmetic, edge case → Fix when convenient

### Ejemplos

#### Bug Activo
```
[BUG-FE-001] Login form acepta passwords <8 caracteres
Location: frontend/app/(auth)/login/page.tsx:45
Impact: Medium - Security concern, pero no permite bypass completo
Temp Fix: N/A - requiere fix en validación del form
Next: Agregar validación client-side mínimo 8 chars en LoginForm component
```

#### Bug con Temp Fix
```
[BUG-DB-002] Slow query en content_pieces JOIN avatars
Location: backend/app/services/content/queries.py:78
Impact: High - Query time 2.3s, timeout en producción
Temp Fix: Cache de 5 min agregado para mitigar
Next: Crear composite index (avatar_id, created_at) para optimizar query
```

#### Bug Resuelto
```
[BUG-BE-003] Avatar creation falla con nombres duplicados
Location: backend/app/services/avatar_service.py:42
Impact: Medium - Error 500 en vez de 409 Conflict
Temp Fix: N/A
Next: Fixed - Agregado unique constraint check, retorna 409 correctamente
```

---

## Bugs Activos

<!-- Los bugs activos se listan aquí -->

---

## Bugs Resueltos

<!-- Los bugs resueltos se archivan aquí para referencia -->
