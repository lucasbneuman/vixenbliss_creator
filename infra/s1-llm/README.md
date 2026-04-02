# S1 LLM

Servicio neutral del LLM que convive con la orquestacion `LangGraph`.

Rol operativo actual:

- `LangGraph` sigue siendo el orquestador
- este servicio solo transforma el contexto reunido por `LangGraph` en prompt estructurado, negative prompt, seeds fijas y `generation_manifest`
- expone `HTTP` para jobs y `WebSocket` opcional para progreso

La infraestructura de compute del LLM queda desacoplada del proveedor del modelo/API.

Estructura esperada:

- `runtime/` servicio del modelo o gateway interno
- `providers/modal/` wrapper activo
- `providers/beam/` placeholder futuro
