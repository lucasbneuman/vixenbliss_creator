# Task Lifecycle

## Flujo estandar

1. `Seleccion`
   La tarea se crea o se toma desde `YouTrack`.
2. `Brief`
   Se define objetivo, alcance, restricciones y criterio de done.
3. `Plan`
   Se pide a Codex un plan concreto para esa tarea.
4. `Aprobacion`
   Solo se avanza con `PLAN OK`.
5. `Implementacion`
   Se trabaja en rama dedicada.
6. `Verificacion`
   Se ejecutan checks, tests y revision de impacto.
7. `Pull Request`
   Se abre PR con checklist y evidencia.
8. `Merge`
   Solo se integra con `MERGE OK`.
9. `Cierre`
   Se enlaza evidencia y se cierra administrativamente con `CLOSE OK` si aplica.

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
- existe PR, commit o evidencia enlazada

## Evidencia minima

Segun el caso, la evidencia puede ser:

- enlace a PR
- hash de commit
- salida de test resumida
- captura o log funcional
- ADR asociada

## Anti-patrones

- implementar sin plan aprobado
- abrir PR sin validaciones
- cerrar tarea sin evidencia
- fusionar multiples objetivos en una sola tarea
- usar el repo como tablero manual de seguimiento
