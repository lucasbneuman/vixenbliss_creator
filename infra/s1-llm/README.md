# S1 LLM

Servicio neutral del LLM que convive con la orquestacion `LangGraph`.

La infraestructura de compute del LLM queda desacoplada del proveedor del modelo/API.

Estructura esperada:

- `runtime/` servicio del modelo o gateway interno
- `providers/modal/` wrapper principal
- `providers/beam/` wrapper secundario
