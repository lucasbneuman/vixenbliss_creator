# S1 LoRA Train

Servicio neutral para entrenamiento LoRA sobre `Flux` sin cuantizacion.

Rol operativo actual:

- consumir `dataset_manifest` o `dataset_package`
- ejecutar training compatible con familia `Flux`
- devolver `lora_model` y `training_manifest`
- exponer `HTTP` para jobs y `WebSocket` opcional para progreso

## Contrato esperado desde `S1 image`

`S1 lora train` debe aceptar dos modos de entrada:

1. `dataset_manifest`
- fuente de verdad minima del dataset
- suficiente cuando el worker de training sabe resolver el package desde storage externo

2. `dataset_package`
- paquete materializado con las imagenes o referencias finales
- recomendado durante etapa de validacion y QA

Direccion recomendada del handoff:

- el runtime/orquestador en `Coolify` recibe el resultado de `S1 image`
- registra `dataset_manifest` y `dataset_package` en `Directus Files` o storage `S3-compatible`
- dispara `S1 lora train` con referencias persistentes

No usar `Modal Volume` como fuente de verdad del dataset entre servicios salvo para staging efimero.

Estructura esperada:

- `runtime/` job runner comun de entrenamiento
- `providers/modal/` wrapper activo por elasticidad de hardware
- `providers/beam/` placeholder futuro portable

Proveedor por defecto recomendado:

- activo: `Modal`
