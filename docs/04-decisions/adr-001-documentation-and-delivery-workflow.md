# ADR-001: Documentacion viva y workflow de entrega

## Estado

Aceptada

## Contexto

El proyecto arranca desde cero, con dos desarrolladores y uso intensivo de agentes. El mayor riesgo inicial no es tecnico sino operativo: duplicacion de tracking, ambiguedad en aprobaciones, tareas demasiado grandes y falta de trazabilidad entre plan, implementacion y cierre.

## Decision

Se adopta este modelo:

- `YouTrack` como fuente de verdad operativa
- `GitHub` como fuente de verdad del codigo y de integracion
- `AGENTS.md` como router principal para agentes
- `docs/` como arquitectura documental viva por dominio
- flujo obligatorio `brief -> plan -> PLAN OK -> implementacion -> verificacion -> PR -> MERGE OK -> cierre`

## Consecuencias

Positivas:

- menor ambiguedad para agentes y humanos
- menor friccion para trabajo en paralelo
- mejor trazabilidad entre roadmap, tarea, cambio y evidencia

Costos:

- disciplina documental minima obligatoria
- mayor rigor en aprobaciones y tamano de tareas

## Revision futura

Revisar esta ADR cuando:

- el equipo supere dos desarrolladores activos
- se incorpore CI/CD productiva completa
- se formalicen convenciones adicionales de release o ambientes
