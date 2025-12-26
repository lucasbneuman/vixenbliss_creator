# Feature Development Workflow

## Descripción
Flujo para desarrollo de nuevas features en VixenBliss Creator.

## Trigger
- Nueva tarea en Notion con estado "Sin empezar" y tipo "Feature"
- Scrum Master detecta y asigna

## Participants
- **Scrum Master**: Orquestador
- **Architect**: Diseño de arquitectura (si feature es compleja)
- **Backend Dev**: Implementación backend
- **Frontend Dev**: Implementación frontend
- **LLM Specialist**: Si involucra AI/LLM
- **Database Engineer**: Si requiere cambios en DB
- **QA Tester**: Testing
- **DevOps**: Deployment

## Steps

### 1. Planning (Scrum Master + Architect)
```
[SM] Obtiene tarea de Notion
[SM] Evalúa complejidad
[SM] Si es compleja → delega a Architect para diseño
[ARCH] Diseña arquitectura, actualiza ARCHITECTURE.md
[ARCH] Define APIs necesarias en API_DOCUMENTATION.md
[ARCH] Output: [ARCH-###] Feature X diseñado - endpoints, schemas, dependencias
```

### 2. Database (Database Engineer)
```
[SM] Si requiere cambios en DB → delega a DB Engineer
[DB] Crea migration up/down
[DB] Agrega índices necesarios
[DB] Output: [DB-###] Migration XXX creada - tablas, relaciones, índices
```

### 3. Backend Implementation (Backend Dev)
```
[SM] Delega implementación backend
[BE] Implementa endpoints según API_DOCUMENTATION.md
[BE] Agrega validaciones con Pydantic
[BE] Implementa business logic
[BE] Output: [BE-###] Endpoint /api/v1/X implementado con validaciones
```

### 4. LLM Integration (LLM Specialist)
```
[SM] Si feature involucra AI → delega a LLM Specialist
[LLM] Diseña workflow en LangGraph
[LLM] Escribe prompts optimizados
[LLM] Implementa RAG si es necesario
[LLM] Output: [LLM-###] Agent X con workflow 5 nodos implementado
```

### 5. Frontend Implementation (Frontend Dev)
```
[SM] Delega implementación frontend
[FE] Crea componentes React/Next.js
[FE] Integra con backend API
[FE] Implementa UI según diseño
[FE] Output: [FE-###] Componente X implementado con integración API
```

### 6. Testing (QA Tester)
```
[SM] Delega testing
[QA] Escribe unit tests (backend/frontend)
[QA] Escribe integration tests
[QA] Escribe E2E tests si es critical flow
[QA] Ejecuta test suite
[QA] Output: [QA-###] Tests para feature X (12 tests, 95% coverage)
```

### 7. Deployment (DevOps)
```
[SM] Delega deployment
[OPS] Actualiza docker-compose si necesario
[OPS] Configura secrets/env vars
[OPS] Deploys a staging via Coolify
[OPS] Verifica health checks
[OPS] Output: [OPS-###] Feature X deployed a staging, health checks OK
```

### 8. Completion (Scrum Master)
```
[SM] Verifica que todos los pasos se completaron
[SM] Actualiza tarea en Notion: estado = "Completado"
[SM] Registra en TASK.md todas las entradas de agentes
[SM] Output: [SM-###] Feature X completado - 7 agentes, 15 tasks registradas
```

## Output Format
Cada agente documenta en TASK.md (2 líneas):
```
[PREFIX-###] Acción realizada con detalles específicos
```

## Success Criteria
- ✅ Tests passing (>80% coverage)
- ✅ Documentation actualizada
- ✅ Deployed a staging
- ✅ Health checks OK
- ✅ Tarea en Notion = "Completado"

## Cost Optimization
- Solo involucrar agentes necesarios (SM evalúa primero)
- Usar context mínimo al delegar
- Output estructurado y conciso
- No tests innecesarios (solo critical paths)
