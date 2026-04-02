# S1 LoRA Train

Servicio neutral para entrenamiento LoRA sobre `Flux` sin cuantizacion.

Rol operativo actual:

- consumir `dataset_manifest` o `dataset_package`
- ejecutar training compatible con familia `Flux`
- devolver `lora_model` y `training_manifest`
- exponer `HTTP` para jobs y `WebSocket` opcional para progreso

Estructura esperada:

- `runtime/` job runner comun de entrenamiento
- `providers/modal/` wrapper activo por elasticidad de hardware
- `providers/beam/` placeholder futuro portable

Proveedor por defecto recomendado:

- activo: `Modal`
