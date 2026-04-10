# Technical Base

## Audiencia

- developers
- agentes que implementan o revisan cambios tecnicos

## Vigencia

- `vivo`

## Objetivo

Describir la base tecnica vigente del repositorio y sus superficies reales de codigo, para que la documentacion siga al sistema implementado y no a una vision historica mas amplia.

## Estado actual del repo

La implementacion viva hoy se concentra en `Sistema 1`, contratos compartidos, pipeline visual y runtimes desacoplados. El repo todavia conserva contexto de producto y direccion futura, pero no implementa todos los sistemas historicamente imaginados.

Las superficies principales son:

- `src/vixenbliss_creator/agentic/`
- `src/vixenbliss_creator/contracts/`
- `src/vixenbliss_creator/s1_control/`
- `src/vixenbliss_creator/s1_services/`
- `src/vixenbliss_creator/visual_pipeline/`
- `src/vixenbliss_creator/runtime_providers/`
- `infra/`
- `tests/`

## Modulos vigentes

### `agentic`

Implementa el flujo de orquestacion para convertir una instruccion del operador en un estado final de identidad con validacion y recomendacion tecnica.

Responsabilidades actuales:

- deteccion de intencion y modo
- extraccion y normalizacion de constraints
- expansion de identidad estructurada
- validacion fail-fast
- integracion HTTP con `LLM serverless` y `ComfyUI Copilot`
- fallback controlado a workflows aprobados

Documentos relacionados:

- `agentic-brain.md`
- `agentic-brain-system1-implementation-guide.md`

### `contracts`

Define contratos reutilizables y persistibles para identidad, jobs, artefactos, modelos y guards de pipeline.

Archivos clave:

- `contracts/identity.py`
- `contracts/job.py`
- `contracts/artifact.py`
- `contracts/model_registry.py`
- `contracts/pipeline_guards.py`

Documentos relacionados:

- `identity-master-schema.md`
- `traceability-contracts.md`

### `s1_control`

Agrupa la logica de control operativo de `Sistema 1`.

Responsabilidades actuales:

- bootstrap de esquema y readiness
- integracion opcional con `Directus`
- registro de imagenes base y reportes
- validacion de dataset
- servicios de identidad y stores

### `s1_services`

Expone logica y runtime de servicios de `Sistema 1` desacoplados del control plane.

### `visual_pipeline`

Define el contrato request/response y la capa de servicio para generacion visual sobre `ComfyUI`.

Responsabilidades actuales:

- request reproducible con workflow aprobado
- soporte de `IP Adapter`
- correccion facial regional
- checkpoints para resume
- compatibilidad con `S1 image` y preparacion para `content_image` o `video`

Documento relacionado:

- `visual-generation-engine.md`

### `runtime_providers`

Abstrae configuracion, modelos, puertos y adapters de proveedor para mantener desacoplo entre contrato tecnico y plataforma de ejecucion.

## Infraestructura versionada

`infra/` esta organizada por servicio, no por una sola plataforma:

- `infra/s1-image/`
- `infra/s1-llm/`
- `infra/s1-lora-train/`
- `infra/s2-image/`
- `infra/s2-video/`
- `infra/comfyui-copilot/`

Tambien sobreviven bundles historicos de `Runpod` que hoy funcionan como referencia tecnica transicional:

- `infra/runpod-s1-image-serverless/`
- `infra/runpod-s1-model-loader/`
- `infra/runpod-visual-serverless/`

## Integraciones y dependencias vigentes

- `Python`
- `Docker`
- `Modal` y/o `Runpod`, segun runtime
- `ComfyUI`
- `Directus` como control plane opcional
- `Supabase/Postgres` y storage compatible
- `OpenTelemetry`

## Fuera del estado implementado actual

Estos frentes pueden existir como vision o direccion futura, pero no deben describirse como implementados si no estan respaldados por codigo vigente:

- distribucion automatizada multicanal
- monetizacion operativa
- chatbot conversacional productivo
- SaaS multi-tenant

Para contexto historico o analisis previos, revisar `docs/99-archive/` sin tratarlo como fuente de verdad activa.
