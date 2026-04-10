# Working Agreement

## Audiencia

- developers
- agentes

## Vigencia

- `vivo`

## Objetivo

Definir reglas simples y estables para que dos desarrolladores y uno o mas agentes trabajen en paralelo sin ambiguedad ni perdida de trazabilidad.

## Fuente de verdad

- `YouTrack` es la fuente de verdad operativa y evolutiva de backlog, prioridad, alcance, asignacion, estado y bugs.
- `GitHub` es la fuente de verdad del codigo, las PRs, los checks y los releases.
- El repositorio guarda proceso, arquitectura, contratos, decisiones, prompts y documentacion tecnica reusable.

No usar `tasks.md` o `bugs.md` como registro principal.
El roadmap del repo funciona como vision flexible y contexto, no como orden rigido de ejecucion.

## Reglas de colaboracion

- trabajo diario sobre `develop`
- `main` reservado para integracion estable
- no crear ramas nuevas salvo pedido explicito
- si excepcionalmente se pide una rama nueva, debe estar ligada a una tarea concreta
- no mezclar refactor y feature en la misma PR
- no mezclar multiples tareas no relacionadas en el mismo cambio
- cada PR debe referenciar una tarea
- cada tarea o cambio cerrado debe dejar al menos un commit trazable
- cada cambio que afecte contratos o arquitectura debe actualizar docs
- pueden existir mejoras o revisiones ad hoc fuera de una tarea explicita, siempre que no contradigan `YouTrack` y dejen evidencia trazable
- al tomar una tarea en `YouTrack`, pasarla primero a `In Progress`
- si aparece dependencia externa, error, bloqueo o inquietud, dejar comentario dentro de la misma tarea
- antes del commit final, dejar comentario de cierre en la tarea con evidencia resumida

## Politica de aprobacion

Usar solo estos gatillos:

- `IMPLEMENTAR PLAN`: habilita implementacion
- `PLAN OK`: tambien habilita implementacion
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
- existe al menos un commit trazable por ese cambio cerrado
