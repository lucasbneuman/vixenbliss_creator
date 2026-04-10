# S1 LLM

Servicio neutral del LLM que convive con la orquestacion `LangGraph`.

Rol operativo actual:

- `LangGraph` sigue siendo el orquestador
- este servicio transforma el contexto reunido por `LangGraph` en prompt estructurado, negative prompt, seeds fijas y `generation_manifest`
- el mismo runtime expone ademas un endpoint OpenAI-compatible para que `LangGraph` pueda consumir el LLM real sin cambiar de contrato
- expone `HTTP` para jobs, `WebSocket` opcional para progreso y `POST /v1/chat/completions` para inferencia

La infraestructura de compute del LLM queda desacoplada del proveedor del modelo/API.

Direccion operativa actual:

- `Modal` despliega el runtime como endpoint HTTP estable
- el backend por defecto es `OpenAI` con `gpt-4.1-mini`
- `Ollama` queda soportado como fallback opcional via `S1_LLM_BACKEND=ollama`
- el endpoint esperado para `LangGraph` es `https://<modal-endpoint>/v1`
- `AgenticSettings` puede resolver el mismo deploy via `S1_LLM_RUNTIME_BASE_URL` y `S1_LLM_RUNTIME_MODEL`, o via `LLM_SERVERLESS_*`
- para el flujo real con `LangGraph`, `S1_LLM_RUNTIME_TIMEOUT_SECONDS` debe quedar en al menos `120`
- si el backend es `OpenAI`, el deploy de `Modal` debe tener el secret `vixenbliss-s1-llm-openai`
- el provider de `Modal` expone ademas `prime_model_cache`, que solo tiene efecto real cuando el backend es `ollama`
- si se quiere registrar en `Directus`, el deploy de `Modal` debe tener el secret `vixenbliss-s1-control-plane` con `DIRECTUS_BASE_URL`, `DIRECTUS_API_TOKEN`, `DIRECTUS_TIMEOUT_SECONDS` y `DIRECTUS_ASSETS_STORAGE`

Estructura esperada:

- `runtime/` servicio del modelo o gateway interno
- `providers/modal/` wrapper activo
- `providers/beam/` placeholder futuro
