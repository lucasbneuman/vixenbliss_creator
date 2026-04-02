# S1 LoRA Train

Servicio neutral para entrenamiento LoRA sobre `Flux` sin cuantizacion.

Estructura esperada:

- `runtime/` job runner comun de entrenamiento
- `providers/modal/` wrapper principal por elasticidad de hardware
- `providers/beam/` wrapper secundario portable

Proveedor por defecto recomendado:

- principal: `Modal`
- secundario: `Beam`
