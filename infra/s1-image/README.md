# S1 Image

Servicio neutral para generacion de set de imagenes de identidad.

Estructura esperada:

- `runtime/` contenedor comun `ComfyUI + Flux + IPAdapter + FaceDetailer`
- `providers/beam/` wrapper de deploy a Beam
- `providers/modal/` wrapper de deploy a Modal

Proveedor por defecto recomendado:

- principal: `Beam`
- secundario: `Modal`
