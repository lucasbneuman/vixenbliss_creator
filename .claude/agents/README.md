# Claude Code Agents - VixenBliss Creator

## Agentes Disponibles

### 1. scrum-master
**Cuándo usar**: Gestión de proyecto, coordinación de tareas, integración con Notion

El Scrum Master es el **orquestador principal** del proyecto. Usa este agente cuando:
- Necesites obtener tareas de Notion
- Quieras asignar trabajo a otros agentes
- Necesites actualizar el estado de tareas en Notion
- Quieras hacer seguimiento del progreso de épicas

**Ejemplo de uso**:
```
Usa el scrum-master para obtener la próxima tarea de Notion y asignarla
```

---

### 2. backend-dev
**Cuándo usar**: Desarrollo de APIs, endpoints FastAPI, lógica de negocio

Especialista en FastAPI y Python. Usa este agente cuando:
- Necesites crear endpoints REST
- Implementar validaciones con Pydantic
- Crear workers Celery para background jobs
- Implementar lógica de negocio del backend

**Ejemplo de uso**:
```
Usa backend-dev para implementar el endpoint POST /api/v1/avatars
```

---

### 3. frontend-dev
**Cuándo usar**: Componentes React, páginas Next.js, UI/UX

Especialista en Next.js 14 y TypeScript. Usa este agente cuando:
- Necesites crear componentes de UI
- Implementar páginas en Next.js
- Integrar con el backend via fetch
- Usar shadcn/ui components

**Ejemplo de uso**:
```
Usa frontend-dev para crear el componente AvatarCard con shadcn/ui
```

---

### 4. database-engineer
**Cuándo usar**: Schemas de DB, migrations, optimización de queries

Especialista en PostgreSQL/Supabase. Usa este agente cuando:
- Necesites diseñar schemas de base de datos
- Crear migrations (up/down)
- Optimizar queries lentos
- Configurar pgvector para RAG

**Ejemplo de uso**:
```
Usa database-engineer para crear la tabla avatars con relations
```

---

### 5. qa-tester
**Cuándo usar**: Tests unitarios, integración, E2E, verificación de calidad

Especialista en testing. Usa este agente cuando:
- Necesites escribir tests para nuevo código
- Verificar coverage de tests
- Reportar bugs encontrados
- Ejecutar test suites

**Ejemplo de uso**:
```
Usa qa-tester para escribir tests del avatar service
```

---

### 6. devops-engineer
**Cuándo usar**: Docker, CI/CD, deployments, infraestructura

Especialista en Docker y Coolify. Usa este agente cuando:
- Necesites configurar Docker/Docker Compose
- Crear GitHub Actions workflows
- Configurar deployments en Coolify
- Setup de infraestructura

**Ejemplo de uso**:
```
Usa devops-engineer para configurar Docker multi-stage build
```

---

## Workflow Recomendado

### Para Features Nuevas
1. **scrum-master** obtiene tarea de Notion
2. **scrum-master** asigna al agente apropiado
3. Agente especializado ejecuta la tarea
4. **qa-tester** verifica calidad
5. **devops-engineer** deploys si es necesario
6. **scrum-master** actualiza Notion a "Completado"

### Para Bugs
1. **qa-tester** reproduce el bug
2. **scrum-master** asigna al agente apropiado (backend-dev/frontend-dev/etc)
3. Agente especializado implementa fix
4. **qa-tester** verifica fix
5. **scrum-master** cierra bug en BUGS.md

---

## Cómo Usar los Agentes

### Automático (Recomendado)
Claude Code invocará automáticamente el agente apropiado basándose en la descripción de tu tarea.

Solo escribe tu solicitud naturalmente:
```
Implementa el endpoint POST /api/v1/avatars con validación
→ Claude usará backend-dev automáticamente

Crea el componente AvatarCard
→ Claude usará frontend-dev automáticamente
```

### Manual (Explícito)
Puedes solicitar un agente específico:
```
Usa backend-dev para implementar el endpoint de avatars
Usa qa-tester para revisar los tests
Usa scrum-master para obtener la próxima tarea de Notion
```

---

## Comando /agents

Puedes usar el comando `/agents` para:
- Ver todos los agentes disponibles
- Crear nuevos agentes
- Editar agentes existentes
- Gestionar permisos de herramientas

```
/agents
```

---

## Documentación de Referencia

Los agentes usan la documentación en `.ai/` como referencia:

- **`.ai/agents/`** - Guías detalladas de cada agente (documentación)
- **`.ai/workflows/`** - Flujos de trabajo (feature development, bug fixing, deployment)
- **`.ai/context/`** - Reglas del proyecto, coding standards, security guidelines
- **`docs/`** - ARCHITECTURE.md, API_DOCUMENTATION.md, TASK.md, BUGS.md

Los agentes leerán automáticamente estos archivos cuando los necesiten.

---

## Próximos Pasos

1. **Usa scrum-master** para obtener la primera tarea de Notion
2. Deja que scrum-master asigne al agente apropiado
3. El agente ejecutará la tarea y documentará en TASK.md
4. scrum-master actualizará el estado en Notion

**Comando sugerido para empezar**:
```
Usa scrum-master para obtener las próximas 3 tareas de Notion con estado "Sin empezar" y mostrarlas
```
