# Working Agreement

## Objetivo

Definir reglas simples y estables para que dos desarrolladores y uno o mas agentes trabajen en paralelo sin ambiguedad ni perdida de trazabilidad.

## Fuente de verdad

- `YouTrack` es la fuente de verdad de backlog, estado, prioridad, asignacion y bugs.
- `GitHub` es la fuente de verdad del codigo, las PRs, los checks y los releases.
- El repositorio guarda documentacion viva, decisiones y evidencia reusable.

No usar `tasks.md` o `bugs.md` como registro principal.

## Reglas de colaboracion

- una tarea activa por rama
- una rama por issue
- no compartir rama
- no mezclar refactor y feature en la misma PR
- no mezclar multiples tareas no relacionadas en el mismo cambio
- cada PR debe referenciar una tarea
- cada cambio que afecte contratos o arquitectura debe actualizar docs

## Politica de aprobacion

Usar solo estos gatillos:

- `PLAN OK`: habilita implementacion
- `MERGE OK`: habilita merge despues de validaciones
- `CLOSE OK`: habilita cierre administrativo o de release

No tomar como aprobacion palabras como "dale", "segui", "listo" o equivalentes.

## Regla de escalado

Si una tarea:

- toca mas de una superficie mayor
- no tiene criterio de done verificable
- requiere decisiones de arquitectura no resueltas
- mezcla backend, datos, infraestructura y docs en un solo bloque

entonces debe dividirse antes de implementar.

## Regla de decisiones

Crear ADR cuando una tarea:

- cambie interfaces publicas o contratos internos
- introduzca o descarte una tecnologia
- cambie una convencion de trabajo
- afecte arquitectura transversal

## Regla de handoff

Si una tarea no termina en un solo ciclo, el handoff minimo debe dejar:

- estado actual
- pendiente concreto
- riesgo abierto
- evidencia ya validada

## Regla de cierre

Una tarea solo se considera cerrada cuando:

- la implementacion esta integrada o descartada explicitamente
- las validaciones minimas estan ejecutadas
- la documentacion impactada esta actualizada
- la evidencia esta enlazada en la tarea o PR
