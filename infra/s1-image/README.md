# S1 Image

Servicio neutral de `S1 image` para `DEV-8`, con orquestacion HTTP en `Coolify` y worker GPU activo en `Modal`.

## Objetivo operativo

- generar imagenes base de identidad con `FLUX.1-schnell`
- mantener consistencia facial con `IP Adapter Plus` cuando exista una referencia visual/facial
- corregir degradaciones faciales con `Impact Pack FaceDetailer`
- exponer un runtime neutral consumible por `runtime_providers`
- dejar explicitamente a `FastAPI` y `LangGraph` fuera de `Modal`

## Contrato del servicio

- `POST /jobs`
- `GET /jobs/{id}`
- `GET /jobs/{id}/result`
- `GET /healthcheck`
- `GET /ws/jobs/{id}`
- `GET /`
- `GET /app`
- `GET /lab`
- `GET /web/assets/{path}`
- `POST /lab/langgraph`
- `POST /lab/s1-image`

El runtime devuelve payloads compatibles con el motor visual actual:

- `provider`
- `workflow_id`
- `workflow_version`
- `provider_job_id`
- `artifacts`
- `successful_node_ids`
- `face_detection_confidence`
- `ip_adapter_used`
- `regional_inpaint_triggered`
- `metadata`
- `error_code`
- `error_message`

## LangGraph Lab

El runtime ahora sirve la puerta de entrada web del monorepo desde `apps/web/`, manteniendo la UI separada del backend aunque siga deployada junto al orquestador actual.

Capacidades iniciales:

- landing inicial en `/` como entrada de la aplicacion
- chat simple para mandar una idea del operador a `LangGraph`
- panel derecho con identidad base, trazabilidad, perfil visual y recomendacion tecnica
- preview del `identity_context` y del payload de handoff para `S1 Image`
- boton para disparar el job real de `S1 Image` usando el ultimo `GraphState` exitoso

Rutas del lab:

- `GET /`: home actual de la aplicacion web
- `GET /app`: alias de la entrada web
- `GET /lab`: alias tecnico del workspace web
- `GET /web/assets/{path}`: assets del front desde `apps/web/public/assets/`
- `POST /lab/langgraph`: ejecuta `LangGraph` con runner determinista
- `POST /lab/s1-image`: toma el ultimo resultado valido y crea el job de `S1 Image`

Uso local minimo:

1. levantar el runtime `FastAPI` de `S1 image`
2. abrir `/` o `/app`
3. escribir un prompt de operador y correr `LangGraph`
4. revisar el panel derecho
5. usar `Probar S1 Image` para disparar el handoff

Default operativo del lab:

- usa `run_agentic_brain` por defecto
- no persiste conversaciones fuera de memoria
- usa `LAB_REFERENCE_FACE_IMAGE_URL` si se quiere cambiar la URL default de referencia facial
- la referencia visual es una imagen facial opcional para guiar `IP-Adapter`; si no existe, el handoff a `S1 Image` sigue siendo valido
- sirve el front desde `apps/web/` para dejar listo el camino a un desacople posterior de front y back

## Estructura

- `runtime/` contiene el runtime `FastAPI` que debe correr en `Coolify` como orquestador del servicio
- `providers/modal/` contiene el worker GPU activo para deploy en `Modal`
- `providers/beam/` queda como placeholder futuro

## Baseline técnico actual

El runtime nuevo porta el comportamiento útil del bundle legacy `infra/runpod-s1-image-serverless/`, pero deja a `Runpod` fuera del camino crítico:

- `FastAPI` y `LangGraph` corren en `Coolify` como capa de orquestacion
- `Modal` solo despierta el worker GPU con `ComfyUI` embebido
- workflow canonico de dataset `lora-dataset-ipadapter-batch.json`
- fallback de identidad base `base-image-ipadapter-impact.json`
- alias lógico `plus_face` resuelto al asset real `ip-adapter.bin`
- fail-fast para `REFERENCE_IMAGE_NOT_FOUND`, `FACE_CONFIDENCE_UNAVAILABLE`, `RESUME_STATE_INCOMPLETE` y `COMFYUI_EXECUTION_FAILED`
- `runtime_stage=identity_image`
- `lora_supported=false`

## Storage híbrido

- modelos pesados y cache caliente: `Modal Volume`
- artifacts y resultados: preparados para storage externo o persistencia fuera del repo

## Variables relevantes

- `S1_IMAGE_PROVIDER=modal`
- `S1_IMAGE_MODAL_APP_NAME`
- `S1_IMAGE_MODAL_FUNCTION_NAME`
- `S1_IMAGE_MODAL_HEALTHCHECK_FUNCTION_NAME`
- `COMFYUI_WORKFLOW_IDENTITY_ID`
- `COMFYUI_WORKFLOW_IDENTITY_VERSION`
- `DEFAULT_RENDER_SAMPLES_TARGET=80`
- `DEFAULT_TRAINING_SAMPLES_TARGET=40`
- `DEFAULT_SELECTION_POLICY=score_curated_v1`
- `COMFYUI_IP_ADAPTER_MODEL`
- `COMFYUI_FACE_CONFIDENCE_THRESHOLD`
- `COMFYUI_FLUX_DIFFUSION_MODEL_NAME`
- `COMFYUI_FLUX_AE_NAME`
- `COMFYUI_FLUX_CLIP_L_NAME`
- `COMFYUI_FLUX_T5XXL_NAME`
- `MODEL_CACHE_ROOT`
- `FLUX_DIFFUSION_MODEL_URL`
- `FLUX_AE_URL`
- `FLUX_CLIP_L_URL`
- `FLUX_T5XXL_URL`
- `IPADAPTER_FLUX_URL`
- `S1_IMAGE_EXECUTION_BACKEND=modal`
- `MODAL_TOKEN_ID` y `MODAL_TOKEN_SECRET` alcanzan para invocar la app privada `vixenbliss-s1-image`
- `MODAL_ENDPOINT_S1_IMAGE` solo como fallback legado si existe un web endpoint intermedio

## Prueba local minima

Para una prueba local realista de `S1 image`, el stack minimo queda asi:

- `FastAPI` del runtime ejecutado localmente o en `Coolify`
- acceso autenticado a `Modal` para despertar el worker GPU
- `HF_TOKEN` con acceso a `FLUX.1-schnell`
- `Modal Volume` ya primado con los assets pesados o URLs de bootstrap validas
- una `reference_face_image_url` accesible desde el worker solo si se quiere usar `IP-Adapter` con una imagen facial de referencia

Validacion minima recomendada:

1. correr `runtime_healthcheck(deep=True)` sobre el worker de `Modal`
2. levantar el runtime `FastAPI` con `S1_IMAGE_EXECUTION_BACKEND=modal`
3. ejecutar `POST /jobs` con `runtime_stage=identity_image`
4. verificar que el resultado devuelva `base_image`, `resume_checkpoint` y `face_detection_confidence`
5. si la confianza facial queda baja, validar la corrida posterior de `face_detail`

## Topologia operativa obligatoria

- `Coolify` aloja el `FastAPI` publico del servicio y el orquestador que consume `LangGraph`
- `Modal` no debe alojar el HTTP publico de `S1 image`
- `Modal` solo expone funciones GPU privadas para ejecutar `ComfyUI`, entrenamiento o inferencia pesada
- el contrato principal con `Modal` es `token + app_name + function_name`; un `MODAL_ENDPOINT_S1_IMAGE` solo aplica como compatibilidad hacia un proxy HTTP externo

## Estrategia de persistencia recomendada

La salida de `S1 image` no debe tratarse como storage permanente en `Modal`.

Direccion recomendada:

- `Modal Volume`: solo para modelos, caches de `ComfyUI` y staging efimero de muy corta vida
- `Directus Files` sobre storage `S3-compatible`: fuente de verdad para `base_image` y evidencia visual de QA
- `s1_artifacts`, `s1_generation_runs` y `s1_identities`: fuente de verdad para `dataset_manifest`, `dataset_package_path`, `character_id` y `seed_bundle`

Regla operativa del gate predeploy:

- `base_image` y evidencia visual siguen yendo a `Directus Files`
- `dataset_manifest` y `dataset_package` quedan como metadata y URIs en rows de `Directus`
- el deploy en `Coolify` no debe depender de subir artifacts no visuales a `Directus Files` para considerarse sano

Modos operativos esperados:

1. modo `review`
- `S1 image` registra `dataset_manifest` y `dataset_package`
- el equipo revisa calidad del dataset
- recien despues se habilita `S1 lora train`

2. modo `autopromote`
- `S1 image` registra como minimo `dataset_manifest`
- `dataset_package` se guarda con retencion corta
- el orquestador dispara `S1 lora train` al terminar la generacion
- luego aplica limpieza automatica de artifacts temporales segun politica

Mientras el flujo este en validacion, priorizar `review`.
Cuando la calidad del dataset ya este estabilizada, pasar a `autopromote` con storage en `Directus`.

## Deploy en Modal

Worker GPU esperado:

1. primar el volume de modelos con `prime_model_cache`
2. publicar la app privada:

```powershell
modal deploy infra/s1-image/providers/modal/app.py
```

3. validar desde Modal:

```powershell
modal run infra/s1-image/providers/modal/app.py::runtime_healthcheck --deep
```

4. usar desde el orquestador en `Coolify`:

- `S1_IMAGE_PROVIDER=modal`
- `S1_IMAGE_MODAL_APP_NAME=vixenbliss-s1-image`
- `S1_IMAGE_MODAL_FUNCTION_NAME=run_s1_image_job`
- `S1_IMAGE_MODAL_HEALTHCHECK_FUNCTION_NAME=runtime_healthcheck`

El worker de Modal queda alineado al flujo curado `80 -> 40` y al workflow aprobado `lora-dataset-ipadapter-batch`.

### Diagnostico rapido de desfasaje repo vs deploy

Si el `Lab` arma el handoff con:

- `reference_face_image_url = null`
- `ip_adapter.enabled = false`

y aun asi el job remoto devuelve `REFERENCE_IMAGE_NOT_FOUND`, tratar el incidente como un desfasaje probable entre el orquestador actual y el bundle desplegado en `Modal`.

Checklist operativo recomendado:

1. consultar `GET /healthcheck?deep=true` en el runtime/orquestador
2. comparar `deployment_fingerprint` vs `remote_deployment_fingerprint`
3. si `deployment_alignment = mismatch`, redeployar el worker de `Modal`
4. repetir el mismo caso real de `POST /lab/s1-image`

Regla canonica esperada del runtime vigente:

- si `ip_adapter.enabled` es `false`, el runtime no debe descargar ni resolver `reference_face_image_url`
- si no existe `reference_face_image_url` ni `reference_face_image_name`, el workflow debe seguir por el camino sin referencia

Comando de redeploy esperado cuando el fingerprint remoto no coincide:

```powershell
modal deploy infra/s1-image/providers/modal/app.py
```

Validacion posterior recomendada:

```powershell
modal run infra/s1-image/providers/modal/app.py::runtime_healthcheck --deep
```

## Comportamiento conversacional del Lab

El draft del avatar queda congelado una vez que existe un `last_graph_state` valido en la sesion.

Regla operativa vigente:

- los cambios explicitos detectados por el parser se aplican directo sobre el avatar actual
- un prompt nuevo que no sea comando tambien puede refinar el avatar actual usando el estado vigente como base
- si un mismo mensaje mezcla cambios explicitos y una descripcion nueva, los overrides manuales tienen prioridad y el resto del texto se usa como refinamiento controlado
- `Completar automaticamente` mantiene el flujo de autofill
- `Regenerar Avatar` limpia el avatar actual y reinicia la construccion desde cero
- despues de `Regenerar Avatar`, el operador tiene que cargar de nuevo los campos o usar `Completar automaticamente`

Formato esperado del mensaje de faltantes:

- el `assistant_message` puede incluir saltos de linea
- cada campo pendiente se muestra con su etiqueta y un ejemplo del formato esperado
- ejemplo:

```text
Edad ficticia
Ejemplo: Edad ficticia = 22 años
```

El front del chat preserva esos saltos de linea para que la guia se vea como bloque legible dentro de la burbuja del asistente.

## Nota sobre Runpod

Runpod queda deprecado para S1 image.

Se conserva solo como referencia historica de la implementacion original y como contexto de migracion, pero no como provider soportado ni baseline operativo vigente.

