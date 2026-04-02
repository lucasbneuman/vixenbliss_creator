# Migracion de infraestructura a Modal + Beam

## Objetivo

Sacar a `Runpod` del camino critico y dejar la infraestructura desacoplada del proveedor.

La estrategia actual del repo queda:

- `Beam` como proveedor principal para inferencia visual cuantizada
- `Modal` como proveedor principal para `LoRA train`, `video` y `S1 llm`
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
- soporte inicial para `Beam` y `Modal`

2. `service runtimes`
- estructura `infra/` por servicio
- contenedor comun por servicio
- wrappers por proveedor en `providers/beam/` y `providers/modal/`

## Seleccion por defecto

- `S1_IMAGE_PROVIDER=beam`
- `S1_LORA_TRAIN_PROVIDER=modal`
- `S1_LLM_PROVIDER=modal`
- `S2_IMAGE_PROVIDER=beam`
- `S2_VIDEO_PROVIDER=modal`

## Nota sobre Runpod

`Runpod` queda como referencia historica y puede seguir existiendo temporalmente en codigo y tests legacy, pero no debe usarse como baseline nuevo ni como direccion de crecimiento del repo.
