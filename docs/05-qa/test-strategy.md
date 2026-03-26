# Test Strategy

## Objetivo

Definir el piso minimo de validacion para que una tarea pueda considerarse lista para revision o cierre.

## Validacion minima obligatoria

Toda tarea debe verificar, segun corresponda:

- que el sistema compila o levanta
- que los tests relevantes pasan
- que no rompe contratos existentes
- que la documentacion impactada fue actualizada
- que la PR o evidencia deja claro que se verifico

## Capas de validacion esperadas

- `Smoke checks`: arranque basico, imports, wiring principal
- `Unitarias`: logica aislada y contratos chicos
- `Integracion`: persistencia, APIs, workers, storage
- `End-to-end`: flujo principal del MVP reforzado
- `Revision humana`: muestras, QA funcional y consistencia visual cuando aplique

## Escenarios de proceso a cubrir

- creacion de tarea desde roadmap
- generacion y aprobacion de plan
- implementacion en rama dedicada
- apertura de PR con checklist
- ejecucion de checks automaticos
- merge con aprobacion
- cierre con evidencia enlazada

## Regla de evidencia

No alcanza con decir "probado". La PR o la tarea debe dejar evidencia resumida de que se corrio una validacion real.

## Criterio para bloquear merge

Bloquear merge si:

- faltan validaciones relevantes
- la documentacion requerida no fue actualizada
- la tarea no esta referenciada
- el cambio mezcla objetivos no relacionados
