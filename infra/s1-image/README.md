# S1 Image

Servicio neutral para generacion de set de imagenes de identidad.

Rol operativo actual:

- consumir el manifiesto preparado por `S1 llm`
- generar imagenes base de identidad
- producir `dataset_manifest` y `dataset_package`
- exponer `HTTP` para jobs y `WebSocket` opcional para progreso

Estructura esperada:

- `runtime/` contenedor comun `ComfyUI + Flux + IPAdapter + FaceDetailer`
- `providers/modal/` wrapper de deploy activo a Modal
- `providers/beam/` placeholder futuro

Proveedor por defecto recomendado:

- activo: `Modal`
