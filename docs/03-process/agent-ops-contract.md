# Agent Ops Contract

## Objetivo

Definir el contrato operativo compartido para que multiples desarrolladores, agentes, MCPs y skills trabajen sobre el mismo repositorio sin ambiguedad, sin compartir secretos y sin duplicar tracking.

## Principios

- un solo contexto operativo compartido
- configuracion versionada, secretos no versionados
- mismos contratos para humanos y agentes
- minima friccion para conectar credenciales personales
- evidencia trazable en `YouTrack`, `GitHub` y repo

## Agentes soportados al inicio

- `Codex` como agente principal de implementacion y revision
- agentes via `MCP` para integraciones externas y contexto operativo
- subagentes para exploracion o trabajo acotado cuando la herramienta lo soporte
- skills locales para estandarizar workflows repetibles

## Clases de trabajo por actor

### Humano

Debe intervenir cuando la tarea:

- define prioridad, alcance o aprobaciones
- cambia arquitectura transversal o introduce una tecnologia nueva
- requiere acceso administrativo fuera del baseline compartido
- valida decisiones de negocio, compliance o calidad final

### Agente principal

Puede resolver:

- lectura de contexto del repo
- planificacion de tareas
- implementacion acotada a la tarea aprobada
- actualizacion de documentacion impactada
- ejecucion de validaciones y preparacion de evidencia

No debe resolver por si solo:

- aprobaciones formales
- cambios de stack no autorizados
- uso de credenciales de otra persona
- configuraciones locales no documentadas en este repo

### Subagentes

Se usan solo para:

- exploracion paralela
- verificacion focalizada
- cambios independientes con ownership claro

Siempre dependen de un agente principal responsable del resultado final.

### MCPs

Se usan para:

- leer o actualizar sistemas externos autorizados
- obtener contexto operativo que no vive en el repo
- automatizar integraciones con herramientas del equipo

Todo MCP soportado debe tener:

- plantilla versionada
- requerimientos de credenciales
- smoke check de conexion
- owner funcional definido

### Skills locales

Se usan para:

- reducir variacion en tareas repetidas
- encapsular instrucciones de tooling o dominio
- acelerar onboarding de developers y agentes

Toda skill compartida debe indicar:

- objetivo
- inputs requeridos
- outputs esperados
- dependencias locales

## Fuentes de verdad y permisos

| Superficie | Fuente de verdad | Lectura | Escritura |
| --- | --- | --- | --- |
| Backlog, estado, prioridad | `YouTrack` | humano, agentes via MCP | humano y agentes autorizados |
| Codigo, PRs, CI | `GitHub` | humano, agentes | humano y agentes autorizados |
| Arquitectura, proceso, contratos y documentacion tecnica | repo `docs/` | humano, agentes | cambios via tarea aprobada |
| Credenciales reales | entorno local o gestor externo | solo owner de la credencial | solo owner o admin |
| Plantillas de tooling | repo | humano, agentes | cambios via tarea aprobada |

## Herramientas por nivel

### Obligatorias para operar este repo

- `Git`
- shell local
- acceso al repositorio
- acceso a `YouTrack`
- acceso a `GitHub`
- lectura de `AGENTS.md` y documentos de proceso

### Obligatorias segun la tarea

- `Supabase/Postgres`
- `Supabase Storage` o `S3-compatible`
- `ComfyUI`
- `Modal` o `Runpod`
- `OpenTelemetry`

### Opcionales iniciales

- `Langfuse`
- `Llama.cpp`
- skills locales adicionales
- MCPs no criticos de apoyo

### Futuras

- tooling conversacional de Sistema 5
- nuevos proveedores solo con tarea y, si aplica, ADR

## Handoff entre humano y agentes

Todo handoff debe dejar:

- tarea o issue de referencia
- objetivo y criterio de done
- estado actual
- riesgo abierto
- evidencia ya validada
- limitaciones de tooling o credenciales

## Regla de no duplicacion de contexto

- `YouTrack` guarda backlog, estado, owner y evidencia enlazada
- el repo guarda proceso, contratos, decisiones, onboarding, prompts y documentacion tecnica
- la configuracion local guarda rutas, secretos y tokens personales
- no mover secretos al repo
- no mover tracking transaccional a archivos `.md`

## Baseline compartido obligatorio

Todo developer o agente debe poder encontrar en el repo:

- contrato operativo de agentes
- onboarding reproducible
- matriz de secretos y accesos
- checklist de tarea lista para agentes
- plantilla de entorno
- plantilla de MCPs
- manifiesto de skills compartidas

## Regla para agregar un nuevo MCP o skill

Antes de incorporar un nuevo MCP o una nueva skill compartida:

1. crear o actualizar la tarea correspondiente
2. documentar objetivo y owner funcional
3. versionar plantilla sin secretos
4. declarar credenciales requeridas
5. agregar validacion minima o smoke check documental
6. enlazar la nueva superficie desde `README.md` o `AGENTS.md` si pasa a ser critica
