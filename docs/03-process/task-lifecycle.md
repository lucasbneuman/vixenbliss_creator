# Task Lifecycle

## Audiencia

- developers
- agentes

## Vigencia

- `vivo`

## Flujo estandar

1. `Seleccion`
   La tarea se crea o se toma desde `YouTrack`.
   Tambien puede existir un pedido ad hoc o mejora puntual, pero `YouTrack` sigue siendo el faro operativo y la evidencia debe quedar trazable.
2. `In Progress`
   La tarea tomada se mueve a `In Progress` antes de empezar la ejecucion.
3. `Brief`
   Se define objetivo, alcance, restricciones y criterio de done.
4. `Plan`
   Se pide a Codex un plan concreto para esa tarea.
5. `Aprobacion`
   Solo se avanza con `IMPLEMENTAR PLAN` o `PLAN OK`.
6. `Implementacion`
   Se trabaja sobre `develop`, salvo pedido explicito de crear una rama nueva.
7. `Verificacion`
   Se ejecutan checks, tests y revision de impacto.
8. `Comentario`
   Se deja comentario en la tarea con evidencia resumida. Si hay dependencia externa, error, bloqueo o inquietud, tambien se documenta ahi.
9. `Cierre`
   La tarea se cierra en `YouTrack` cuando el trabajo termina.
10. `Commit`
   Toda tarea o cambio cerrado deja al menos un commit trazable.
11. `Pull Request`
   Se abre PR con checklist y evidencia si corresponde.
12. `Merge`
   Solo se integra con `MERGE OK`.
13. `Cierre administrativo`
   Se enlaza evidencia adicional y se usa `CLOSE OK` solo si hace falta validacion administrativa externa.

## Estados recomendados

- `Backlog`
- `Ready`
- `Planned`
- `In Progress`
- `In Review`
- `Blocked`
- `Done`

## Definition of Ready

Una tarea esta lista para planificar si tiene:

- objetivo concreto
- alcance acotado
- criterio de done
- dependencia explicita si existe
- owner definido

## Definition of Done

Una tarea esta done si:

- el cambio cumple el objetivo pedido
- las validaciones minimas corrieron
- no deja decisiones implicitas
- la documentacion afectada quedo al dia
- existe al menos un commit o evidencia enlazada

## Evidencia minima

Segun el caso, la evidencia puede ser:

- enlace a PR
- hash de commit
- salida de test resumida
- captura o log funcional
- ADR asociada
- resumen final de implementacion con tareas hechas, validaciones y rutas criticas tocadas si aplica
- comentario en `YouTrack` con bloqueos, dependencias o inquietudes si aparecieron durante la ejecucion

## Anti-patrones

- implementar sin plan aprobado
- abrir PR sin validaciones
- cerrar tarea sin evidencia
- fusionar multiples objetivos en una sola tarea
- usar el repo como tablero manual de seguimiento
