# ADR-003: `YouTrack` como fuente operativa evolutiva y roadmap flexible

## Estado

Aprobada

## Contexto

El repo venia describiendo el roadmap como superficie ejecutable fuerte y usando `PLAN OK` como unico gatillo documental de implementacion. Eso generaba rigidez innecesaria frente a un proyecto cuyo backlog, alcance y prioridades cambian rapido a partir de aprendizaje real en `YouTrack`.

Tambien faltaba formalizar dos reglas operativas que ya resultan necesarias:

- toda tarea o cambio cerrado debe dejar commit trazable
- toda respuesta final de implementacion debe cerrar con un resumen operativo minimo

## Decision

Se adopta este modelo:

- `YouTrack` es la fuente de verdad operativa y evolutiva de backlog, prioridad, alcance y estado
- `docs/02-roadmap/` queda como vision flexible y contexto tecnico, no como agenda rigida de ejecucion
- `IMPLEMENTAR PLAN` y `PLAN OK` son gatillos validos para pasar de plan a implementacion
- toda tarea o cambio cerrado debe dejar al menos un commit trazable
- toda implementacion debe cerrar con resumen de tareas hechas, validaciones, commit, rutas criticas si aplica y riesgo abierto si existe

## Consecuencias

Positivas:

- menos conflicto entre backlog vivo y documentacion del repo
- mayor capacidad de redirigir el proyecto sin pelear contra el roadmap
- mejor trazabilidad tecnica del camino recorrido

Costos:

- obliga a mantener mejor alineados proceso, prompts y documentacion tecnica
- exige disciplina para actualizar el repo despues de cambios importantes de enfoque

## Revision futura

Revisar esta ADR si el equipo redefine el rol del roadmap, cambia el sistema de tracking principal o automatiza de otra forma el cierre documental de tareas.
