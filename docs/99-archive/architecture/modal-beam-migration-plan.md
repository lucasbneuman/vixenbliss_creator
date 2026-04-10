# Migracion de infraestructura a Modal

> Estado: `archivado`
> Fecha de archivo: `2026-04-10`
> Motivo: plan de migracion historico que ya no debe competir con la estructura real de `infra/` y `runtime_providers/`.
> Reemplazo vigente: `docs/01-architecture/technical-base.md`.

## Objetivo

Sacar a `Runpod` del camino critico y dejar la infraestructura desacoplada del proveedor.

La estrategia actual del repo queda:

- `Modal` como proveedor activo para los 5 servicios
- la capa neutral de proveedores se preserva para reintroducir un segundo proveedor cuando haya una opcion operable sin friccion
- cambio de proveedor por configuracion, no por cambio de contrato de negocio

## Servicios objetivo

- `S1 image`
- `S1 lora train`
- `S1 llm`
- `S2 image`
- `S2 video`

## Decision de arquitectura

La capa nueva se separa en dos niveles:

1. `runtime_providers`
- capacidades neutrales de `submit job`, `get status`, `fetch result`, `healthcheck`
- progreso en tiempo real opcional por `WebSocket`, sin reemplazar el contrato HTTP base
- soporte inicial para `Modal` y capacidad de sumar otro proveedor despues

2. `service runtimes`
- estructura `infra/` por servicio
- contenedor/orquestador por servicio alojado en `Coolify`
- wrapper activo en `providers/modal/`
- `providers/beam/` queda solo como placeholder futuro mientras `Beam` siga sin disponibilidad operativa
- `LangGraph` sigue siendo el orquestador central y consume estos runtimes como workers externos

## Regla operativa de despliegue

- `FastAPI` y `LangGraph` viven en `Coolify`
- `Modal` no debe exponer el HTTP publico del orquestador
- `Modal` solo despierta workers GPU para `ComfyUI`, entrenamiento y otras tareas pesadas
- si un servicio usa `Modal`, el endpoint publico sigue siendo el runtime publicado en `Coolify`

## Estado operativo S1

- `S1 llm` prepara prompt estructurado, negative prompt, seeds fijas y manifiesto tecnico consumible por `S1 image`
- `S1 image` genera imagenes base y produce `dataset_manifest` + `dataset_package`
- `S1 lora train` consume el dataset y devuelve `lora_model` + manifest tecnico de entrenamiento
- mientras la DB no este lista, la persistencia intermedia se resuelve con artifacts JSON fuera del repo

## Seleccion por defecto

- `S1_IMAGE_PROVIDER=modal`
- `S1_LORA_TRAIN_PROVIDER=modal`
- `S1_LLM_PROVIDER=modal`
- `S2_IMAGE_PROVIDER=modal`
- `S2_VIDEO_PROVIDER=modal`

## Nota sobre Runpod

`Runpod` queda como referencia historica y puede seguir existiendo temporalmente en codigo y tests legacy, pero no debe usarse como baseline nuevo ni como direccion de crecimiento del repo.

`Beam` queda fuera del camino critico actual por lista de espera, aunque la abstraccion se conserva para retomarlo mas adelante sin rediseñar la app.
