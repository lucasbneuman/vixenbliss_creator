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

## Entorno base para validacion Python

Para cambios Python, el baseline operativo del repo es:

- crear `.venv` con `python -m venv .venv`
- activar el entorno virtual local
- instalar dependencias con `python -m pip install -r requirements.txt`
- ejecutar validaciones con `python -m pytest -q`

`requirements.txt` es la unica fuente de verdad para instalar dependencias del proyecto.

## Capas de validacion esperadas

- `Smoke checks`: arranque basico, imports, wiring principal
- `Unitarias`: logica aislada y contratos chicos
- `Integracion`: persistencia, APIs, workers, storage
- `End-to-end`: flujo principal del MVP reforzado
- `Revision humana`: muestras, QA funcional y consistencia visual cuando aplique

## Smoke reusable de S1

Para validar el handoff previo a `S1 Training` sin depender de un endpoint publico ya desplegado, el repo incorpora dos checks reutilizables:

- `python -m vixenbliss_creator.s1_control.live_smoke`
- `python -m vixenbliss_creator.s1_control.readiness_check --idea "Quiero una modelo morocha para contenido NSFW, el resto completalo de manera automatica"`
- `python -m vixenbliss_creator.s1_control.cleanup_directus`

Uso recomendado:

- `live_smoke` valida persistencia real en `Directus` con runtime local controlado
- `readiness_check` combina `LangGraph` con LLM real, `S1 llm` local, fallback local de `S1 image` y verificacion de artifacts persistidos
- cuando `MODAL_TOKEN_ID` y `MODAL_TOKEN_SECRET` estan presentes, `readiness_check` debe priorizar el worker GPU real de `S1 Image` en `Modal`
- los checks esperan que `Directus Files` reciba solo imagenes; `dataset_manifest` y `dataset_package` deben quedar en tablas y metadata tecnica
- el PNG usado por la smoke es un fixture tecnico valido mayor a `1x1`, suficiente para integridad binaria pero no para aprobar calidad de entrenamiento
- la validacion visual final para habilitar `LoRA training` sigue requiriendo revision humana sobre imagenes reales del runtime GPU
- `cleanup_directus` borra las filas y files de prueba de `S1` para dejar el control plane limpio antes de una nueva tanda de validacion

## Escenarios de proceso a cubrir

- creacion de tarea desde roadmap
- generacion y aprobacion de plan
- implementacion sobre `develop`, salvo pedido explicito de rama nueva
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
