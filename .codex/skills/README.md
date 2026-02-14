# Skills - Codex Operating System

## Propósito

La carpeta `.codex/skills/` es un repositorio centralizado de **templates, patterns, y utilities reusables** que los agentes Codex pueden aplicar a múltiples tareas sin reinventar la rueda.

Una "Skill" es un fragmento de conocimiento codificado que:
- ✅ Resuelve un problema común (ej: "cómo hacer presigned URLs seguros")
- ✅ Es agnóstico a la tarea específica (reutilizable en múltiples contextos)
- ✅ Incluye ejemplos de uso
- ✅ Sigue best practices de seguridad y performance
- ✅ Provee tests que verifica el skill funciona

## Estructura de Carpetas

```
.codex/skills/
├── README.md                          # Este archivo
├── backend/
│   ├── pydantic-validation.md         # Validación Pydantic patterns
│   ├── async-database-queries.md      # Async DB queries con SQLAlchemy
│   ├── error-handling.md              # Error handling patterns
│   ├── rate-limiting.md               # Rate limiting implementations
│   └── presigned-urls-r2.md           # Presigned URLs con Cloudflare R2
├── frontend/
│   ├── react-error-boundary.md        # Error boundaries en React
│   ├── form-validation.md             # Form validation con zod
│   ├── api-integration.md             # Integración con APIs desde React
│   └── loading-states.md              # Loading state patterns
├── database/
│   ├── migration-template.md          # Plantilla para migraciones SQL
│   ├── index-strategy.md              # Estrategia de índices
│   └── pgvector-optimization.md       # Optimización pgvector para RAG
├── devops/
│   ├── docker-multistage.md           # Docker builds multi-stage
│   ├── github-actions-ci.md           # GitHub Actions CI/CD patterns
│   └── coolify-deployment.md          # Deployment patterns con Coolify
├── llm/
│   ├── prompt-engineering.md          # Prompt engineering best practices
│   ├── langraph-workflow.md           # LangGraph agent patterns
│   ├── cost-optimization.md           # Cost optimization tips
│   └── token-counting.md              # Token counting y budgeting
└── testing/
    ├── pytest-fixtures.md             # Pytest fixtures avanzados
    ├── integration-tests.md           # Integration testing patterns
    └── mock-external-services.md      # Mocking servicios externos
```

## Cómo Usar Skills

### 1. Encontrar un Skill

Buscar si existe skill para el problema:
```bash
# Navegando a carpeta relevante (backend, frontend, etc.)
# O usando semantic search en workspace
```

### 2. Leer el Skill

Skill típicamente incluye:
```markdown
# [Nombre del Skill]

## Problema
[Qué problema resuelve]

## Solución
[Cómo resolverlo - código + explicación]

## Best Practices
[Tips para usar correctamente]

## Tests
[Tests que verifican que funciona]

## Related Skills
[Links a otros skills relacionados]
```

### 3. Aplicar a tu Tarea

Adaptar el ejemplo al contexto específico:
```python
# Ejemplo de skill: error-handling.md
# Tu código adaptado:
try:
    result = await some_async_operation()
except DatabaseError as e:
    logger.error(f"DB error: {e}")
    raise HTTPException(status_code=500, detail="Database unavailable")
except ValueError as e:
    logger.warning(f"Validation error: {e}")
    raise HTTPException(status_code=400, detail=str(e))
```

### 4. Crear Tests

Agregar tests que verifiquen el skill funciona:
```python
def test_error_handling_logs_correctly():
    """Verify errors are logged before being raised"""
    with pytest.raises(HTTPException):
        raise_error_properly()
    # Verify logging happened
```

## Crear un Nuevo Skill

Si detectás un patrón reutilizable, crear skill nuevo:

1. **Identificar el problema**: ¿Qué resuelve?
2. **Generalizar**: ¿Se aplica a múltiples contextos?
3. **Documentar**: Crear archivo en carpeta relevante
4. **Ejemplificar**: Agregar 1-2 ejemplos de uso
5. **Testear**: Verificar con tests que funciona
6. **Proponer**: Hacer PR con el nuevo skill

### Plantilla para Nuevo Skill

```markdown
# [Nombre del Skill]

## Problema
[Descripción concisa del problema que resuelve]

## Solución

### Opción 1: [Approach Name]
```[código]
```
[Explicación]

### Opción 2: [Alternative Approach]
```[código]
```
[Explicación]

## Best Practices
- ✅ Hacer X porque...
- ✅ Evitar Y porque...
- ⚠️ Si aplica Z, entonces...

## Examples

### Example 1: [Scenario]
```[código]
```

### Example 2: [Scenario]
```[código]
```

## Tests

```python
def test_[scenario]():
    """Verify [behavior]"""
    # Arrange
    # Act
    # Assert
```

## Related Skills
- [Link a otro skill]
- [Link a otro skill]

## References
- [External link]
```

## Curation & Maintenance

Skills se mantienen actualizado por:
- **Backend Dev**: Skills en `backend/`, `database/`, `testing/backend`
- **Frontend Dev**: Skills en `frontend/`, `testing/frontend`
- **LLM Specialist**: Skills en `llm/`
- **DevOps Engineer**: Skills en `devops/`

Si un skill se vuelve obsoleto:
- Marcar con ⚠️ **DEPRECATED** al inicio
- Proponer skill alternativo
- Remover después de todos los proyectos migraron

## Convención de Nombres

Nombres de skills:
- Descriptivos y en nivel función/patrón (ej: `async-database-queries.md`, no `db.md`)
- Formato: `kebab-case.md`
- Prefijo de tipo en algunos casos (ej: `pattern-`, `template-`)

## Ejemplos de Skills (Stubs)

> Nota: Estos son templates de ejemplo. Los skills actuales se crearán según se identifiquen patrones reutilizables.

### Backend Examples
- `pydantic-validation.md` - Validación robusta con Pydantic enums, validators, custom types
- `async-database-queries.md` - SQLAlchemy async patterns, connection pooling, retries
- `error-handling.md` - Try/except patterns, logging, HTTP exceptions

### Frontend Examples
- `react-error-boundary.md` - Error boundaries para capturar errores en componentes
- `form-validation.md` - Zod + React Hook Form patterns
- `api-integration.md` - useEffect + API calls, caching, stale-while-revalidate

### LLM Examples
- `prompt-engineering.md` - Few-shot learning, chain-of-thought, token optimization
- `langraph-workflow.md` - Agents multi-nodo, state management, tool calling
- `cost-optimization.md` - Model selection (Haiku vs Sonnet), prompt compression

---

**Última actualización**: 2026-02-11  
**Versión**: 1.0  
**Mantendedor**: Agentes Codex
