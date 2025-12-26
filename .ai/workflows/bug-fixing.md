# Bug Fixing Workflow

## Descripción
Flujo para corrección de bugs reportados en VixenBliss Creator.

## Trigger
- Bug reportado en BUGS.md
- Tarea en Notion con tipo "Bug" y estado "Sin empezar"
- Scrum Master detecta y asigna

## Participants
- **Scrum Master**: Orquestador
- **QA Tester**: Reproducción y verificación
- **Backend/Frontend/LLM/DB**: Según ubicación del bug
- **DevOps**: Si afecta deployment

## Steps

### 1. Triage (Scrum Master + QA)
```
[SM] Obtiene bug de Notion o BUGS.md
[SM] Evalúa severidad: Critical/High/Medium/Low
[SM] Delega a QA para reproducción
[QA] Reproduce bug, documenta steps
[QA] Output: [QA-###] Bug X reproducido en ambiente Y
```

### 2. Investigation (Agente Especializado)
```
[SM] Identifica agente responsable según location
[AGENT] Lee código afectado
[AGENT] Identifica root cause
[AGENT] Propone fix
```

### 3. Fix Implementation
```
[AGENT] Implementa fix
[AGENT] Si es temporal: documenta en BUGS.md "Temp Fix"
[AGENT] Si es permanente: actualiza código
[AGENT] Output: [PREFIX-###] Bug X fixed - cambio en archivo:línea
```

### 4. Testing (QA Tester)
```
[SM] Delega verificación a QA
[QA] Ejecuta regression tests
[QA] Verifica fix resuelve el bug
[QA] Verifica no introduce nuevos bugs
[QA] Output: [QA-###] Bug X verificado fixed, tests passing
```

### 5. Deployment (DevOps si es necesario)
```
[SM] Si bug es Critical/High → deployment inmediato
[OPS] Hotfix deployment a production
[OPS] Verifica health checks
[OPS] Output: [OPS-###] Hotfix bug X deployed a production
```

### 6. Completion (Scrum Master)
```
[SM] Actualiza BUGS.md con resolución
[SM] Actualiza tarea en Notion: estado = "Completado"
[SM] Output: [SM-###] Bug X resuelto y deployed
```

## BUGS.md Format (5 líneas)
```
[BUG-###] Descripción del bug
Location: archivo:línea
Impact: [Severity] - Descripción del impacto
Temp Fix: Arreglo temporal aplicado (o "Fixed permanently")
Next: N/A (si está fixed) o próximos pasos
```

## Severity Guidelines
- **Critical**: System down, data loss, security breach → Fix ASAP
- **High**: Major functionality broken → Fix within 24h
- **Medium**: Feature partially working → Fix within 1 week
- **Low**: Minor issue, cosmetic → Fix when convenient

## Cost Optimization
- Reproducción rápida sin exploraciones innecesarias
- Fix directo sin refactoring no relacionado
- Tests solo de regression, no nuevos features
- Deployment solo si es Critical/High
