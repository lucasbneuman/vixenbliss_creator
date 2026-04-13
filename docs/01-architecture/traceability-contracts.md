# Traceability Contracts

## Audiencia

- developers
- agentes que tocan persistencia y trazabilidad

## Vigencia

- `vivo`

## Objetivo

Definir los contratos canonicos y persistibles de `Job`, `Artifact`, `ModelRegistry` y `Content` para trazabilidad operativa del MVP de `VixenBliss Creator`.

Este documento fija:

- tipos y estados minimos de ejecucion asincrona
- artefactos tecnicos obligatorios por flujo
- catalogo minimo de modelos base, LoRAs y placeholders de video
- contrato canonico del output catalogado de negocio
- relaciones principales hacia `Identity`

## Version vigente

- `Job.schema_version`: `1.0.0`
- `Artifact.schema_version`: `1.0.0`
- `ModelRegistry.schema_version`: `1.0.0`
- `Content.schema_version`: `1.0.0`
- contratos fuente Python: `src/vixenbliss_creator/contracts/job.py`, `artifact.py`, `model_registry.py`, `content.py`

## Contrato `Job`

### Tipos de job MVP

- `create_identity`
- `identity_image_generation`
- `build_dataset`
- `validate_dataset`
- `lora_training`
- `content_image_generation`
- `video_generation`
- `qa_review`

### Estados y transiciones minimas

- `pending -> running | cancelled`
- `running -> succeeded | failed | cancelled | timed_out`
- estados terminales sin reapertura implicita

### Campos operativos minimos

| Campo | Tipo | Req. | Razon |
|---|---|---|---|
| `id` | UUID | si | identidad estable del job |
| `identity_id` | UUID | si | relacion principal hacia `Identity` |
| `job_type` | enum | si | routing de workers |
| `status` | enum | si | monitoreo y orquestacion |
| `timeout_seconds` | entero | si | fail-fast operativo |
| `attempt_count` | entero | si | control de retries |
| `payload_json` | json | si | entrada persistible |
| `metadata_json` | json | si | contexto tecnico adicional |
| `error_message` | string nullable | no | diagnostico persistible |
| `queued_at` | timestamp UTC | si | auditoria de cola |
| `started_at` | timestamp UTC nullable | no | inicio efectivo |
| `finished_at` | timestamp UTC nullable | no | cierre efectivo |
| `created_at` | timestamp UTC | si | auditoria |
| `updated_at` | timestamp UTC | si | sincronizacion |

## Contrato `Artifact`

### Tipos de artefacto MVP

- `base_image`
- `dataset_manifest`
- `dataset_package`
- `lora_model`
- `workflow_json`
- `generated_image`
- `thumbnail`
- `qa_report`

### Relaciones principales

- todo `Artifact` requiere `identity_id`
- `source_job_id` enlaza el job que produjo el output cuando aplica
- `base_model_id` y `model_version_used` preservan trazabilidad de inferencia o entrenamiento

### Campos operativos minimos

| Campo | Tipo | Req. | Razon |
|---|---|---|---|
| `id` | UUID | si | identificador estable |
| `identity_id` | UUID | si | particion por identidad |
| `artifact_type` | enum | si | clasificacion operativa |
| `storage_path` | string | si | fuente de verdad de ubicacion |
| `source_job_id` | UUID nullable | no | trazabilidad de origen |
| `base_model_id` | string nullable | no | modelo base asociado |
| `model_version_used` | string nullable | no | version efectiva usada |
| `checksum_sha256` | string nullable | no | integridad de dataset/modelo |
| `content_type` | string nullable | no | manejo tecnico de archivos |
| `size_bytes` | entero nullable | no | auditoria basica |
| `metadata_json` | json | si | extensibilidad futura |
| `created_at` | timestamp UTC | si | auditoria |
| `updated_at` | timestamp UTC | si | sincronizacion |

## Contrato `ModelRegistry`

### Roles y familias minimas

- `model_role`: `base_model`, `lora`, `video_placeholder`
- `model_family`: `flux`, `custom_lora`, `future_video`
- `quantization`: `none`, `fp8`, `int8`, `int4`

### Proveedores iniciales

- `black_forest_labs`
- `comfyui`
- `modal`
- `runpod`
- `internal`

### Campos operativos minimos

| Campo | Tipo | Req. | Razon |
|---|---|---|---|
| `id` | UUID | si | identificador estable |
| `model_family` | enum | si | agrupacion tecnica |
| `model_role` | enum | si | distingue base, LoRA y placeholder |
| `provider` | enum | si | trazabilidad de proveedor |
| `version_name` | string | si | version visible |
| `display_name` | string | si | lectura operativa |
| `base_model_id` | string | si | modelo base canonico declarado |
| `storage_path` | string nullable | no | ubicacion de binario si existe |
| `parent_model_id` | UUID nullable | no | relacion LoRA -> modelo base |
| `compatibility_notes` | string nullable | no | notas de compatibilidad |
| `quantization` | enum | si | variante de precision declarada |
| `is_active` | bool | si | diferenciacion entre activo e historico |
| `metadata_json` | json | si | extensibilidad futura |
| `created_at` | timestamp UTC | si | auditoria |
| `updated_at` | timestamp UTC | si | sincronizacion |
| `deprecated_at` | timestamp UTC nullable | no | retiro controlado |

## Contrato `Content`

### Rol canonico

- `Content` representa el output catalogado de negocio
- `Artifact` representa el archivo o evidencia tecnica del output
- `Job` representa la ejecucion que produjo el output
- `ModelRegistry` representa la version y compatibilidad del modelo usado

### Modos y estados minimos

- `content_mode`: `image`, `video`
- `video_generation_mode`: `text_to_video`, `image_to_video`
- `generation_status`: `pending`, `generated`, `failed`, `archived`
- `qa_status`: `not_reviewed`, `approved`, `rejected`

### Campos operativos minimos

| Campo | Tipo | Req. | Razon |
|---|---|---|---|
| `id` | string estable | si | identificador canonico del contenido |
| `identity_id` | string estable | si | relacion principal con la identidad |
| `content_mode` | enum | si | distingue imagen y video |
| `video_generation_mode` | enum nullable | no | modalidad de video cuando `content_mode=video` |
| `generation_status` | enum | si | estado del output catalogado |
| `qa_status` | enum | si | estado de revision del contenido final |
| `job_id` | string nullable | no | job origen del output |
| `primary_artifact_id` | string nullable | no | artifact principal catalogado |
| `related_artifact_ids` | lista | no | artifacts auxiliares o vinculados |
| `base_model_id` | string nullable | no | modelo base efectivo |
| `model_version_used` | string nullable | no | version efectiva del workflow o modelo usado |
| `provider` | enum nullable | no | proveedor de ejecucion persistido como snapshot |
| `workflow_id` | string nullable | no | workflow aplicado |
| `prompt` | text nullable | no | prompt final que genero el output |
| `negative_prompt` | text nullable | no | negative prompt final |
| `seed` | entero nullable | no | semilla efectiva persistida |
| `source_content_id` | string nullable | no | contenido fuente cuando el video deriva de un contenido previo |
| `source_artifact_id` | string nullable | no | artifact fuente cuando el video deriva de una imagen o clip |
| `duration_seconds` | float nullable | no | duracion para video |
| `frame_count` | entero nullable | no | cantidad de frames para video |
| `frame_rate` | float nullable | no | frame rate para video |
| `metadata_json` | json | si | extensibilidad controlada |
| `created_at` | timestamp UTC | si | auditoria |
| `updated_at` | timestamp UTC | si | sincronizacion |

### Reglas de consistencia

- una imagen generada debe poder persistirse con trazabilidad minima completa
- un video queda preparado contractualmente aunque el runtime productivo aun no exista
- `video` requiere `video_generation_mode` para que la solicitud no quede ambigua
- `text_to_video` no debe arrastrar referencias de origen visual
- `image_to_video` debe persistir al menos `source_content_id` o `source_artifact_id`
- `image` no define `duration_seconds`, `frame_count` ni `frame_rate`
- `video` puede dejar esos campos en null mientras este en estados previos, pero si queda en `generated` debe persistirlos completos
- `qa_status` solo puede aprobar o rechazar contenido ya generado

### Persistencia canonica de trazabilidad

Para `Content`, la fuente de verdad persistida debe ser explicita, no derivada implicitamente de otros registros:

- `prompt`: se persiste en `Content.prompt`
- `negative_prompt`: se persiste en `Content.negative_prompt`
- `seed`: se persiste en `Content.seed`
- `workflow_id`: se persiste en `Content.workflow_id`
- `provider`: se persiste en `Content.provider`
- `model_version_used`: se persiste en `Content.model_version_used`

Ese snapshot evita depender de reconstrucciones futuras desde `Job`, `Artifact` o manifests runtime.

### Correspondencia `Content <-> Artifact`

- `Content.primary_artifact_id` apunta al artifact principal del output catalogado
- `Content.related_artifact_ids` apunta a artifacts auxiliares persistidos en la misma corrida
- `Artifact` sigue conservando metadata tecnica del archivo, checksum, locator y content type
- `Content` conserva el significado de negocio del output final y su estado de QA

### Correspondencia `Content` -> `content_catalog` -> `contents`

La persistencia vigente del repo sigue siendo `content_catalog` en `Directus`, pero `DEV-14` agrega una representacion relacional formal en SQL para dashboard/API y trazabilidad cerrable.

Correspondencia canónica:

| Contrato Python | Directus `content_catalog` | SQL `contents` |
|---|---|---|
| `id` | `content_id` | `content_id` |
| `identity_id` | `identity_id` | `identity_id` |
| `content_mode` | `content_mode` | `content_mode` |
| `video_generation_mode` | `video_generation_mode` | `video_generation_mode` |
| `generation_status` | `generation_status` | `generation_status` |
| `qa_status` | `qa_status` | `qa_status` |
| `job_id` | `job_id` | `job_id` |
| `primary_artifact_id` | `primary_artifact_id` | `primary_artifact_id` |
| `related_artifact_ids` | `related_artifact_ids` | `related_artifact_ids` |
| `base_model_id` | `base_model_id` | `base_model_id` |
| `model_version_used` | `model_version_used` | `model_version_used` |
| `provider` | `provider` | `provider` |
| `workflow_id` | `workflow_id` | `workflow_id` |
| `prompt` | `prompt` | `prompt` |
| `negative_prompt` | `negative_prompt` | `negative_prompt` |
| `seed` | `seed` | `seed` |
| `source_content_id` | `source_content_id` | `source_content_id` |
| `source_artifact_id` | `source_artifact_id` | `source_artifact_id` |
| `duration_seconds` | `duration_seconds` | `duration_seconds` |
| `frame_count` | `frame_count` | `frame_count` |
| `frame_rate` | `frame_rate` | `frame_rate` |
| `metadata_json` | `metadata_json` | `metadata_json` |
| `created_at` | `created_at` | `created_at` |
| `updated_at` | `updated_at` | `updated_at` |

Regla operativa:

- `content_catalog` sigue siendo la fuente viva del runtime actual
- `contents` formaliza la misma entidad para persistencia relacional versionada
- `content_mode` es la resolucion canónica del concepto `media_modality` mencionado en el ticket

### Cobertura minima pedida por `DEV-13`

El contrato debe cubrir desde ahora:

- imagen final catalogable de `S2`
- thumbnail o evidencia visual asociada como artifact auxiliar
- video futuro sin rediseño del modelo, usando `content_mode=video` y metadata temporal

Esto no significa que las tareas `2.5` a `2.10` ya esten implementadas hoy. Significa que el contrato de `Content` ya puede representar sus outputs esperados sin tener que cambiar estructura base cuando esas tareas se desarrollen.

### Payload minimo de video preparado

Ejemplo `text_to_video` persistible y consultable:

```json
{
  "id": "content-video-001",
  "identity_id": "identity-001",
  "content_mode": "video",
  "video_generation_mode": "text_to_video",
  "generation_status": "pending",
  "qa_status": "not_reviewed",
  "base_model_id": "future-video-placeholder-v1",
  "model_version_used": "future-video-placeholder-v1",
  "provider": "modal",
  "workflow_id": "video-image-to-video-prep",
  "prompt": "editorial slow pan with warm backlight",
  "negative_prompt": "temporal drift, low quality",
  "metadata_json": {
    "video_backend_hint": "wan2.2",
    "options": {
      "aspect_ratio": "9:16"
    }
  }
}
```

Ejemplo `image_to_video` persistible y consultable:

```json
{
  "id": "content-video-002",
  "identity_id": "identity-001",
  "content_mode": "video",
  "video_generation_mode": "image_to_video",
  "generation_status": "pending",
  "qa_status": "not_reviewed",
  "base_model_id": "future-video-placeholder-v1",
  "model_version_used": "future-video-placeholder-v1",
  "provider": "modal",
  "workflow_id": "video-image-to-video-prep",
  "prompt": "subtle motion from the hero still",
  "negative_prompt": "temporal drift, low quality",
  "source_artifact_id": "artifact-base-image-001",
  "metadata_json": {
    "video_backend_hint": "animatediff",
    "options": {
      "motion_strength": 0.45
    }
  }
}
```

## Matriz flujo -> registros obligatorios

| Flujo | `Job` | `Artifact` | `ModelRegistry` | `Content` |
|---|---|---|---|---|
| creacion de identidad | si | no obligatorio | no | no |
| generacion S1 de identidad | si (`identity_image_generation`) | si (`base_image`, `workflow_json`) | referencia a modelo base Flux | opcional si se cataloga output visual reutilizable |
| armado de dataset | si | si (`dataset_manifest`, `dataset_package`) | no | no |
| entrenamiento LoRA | si (`lora_training`) | si (`lora_model`) | si (`lora`) | no |
| generacion S2 de contenido | si (`content_image_generation`) | si (`generated_image`, `thumbnail`) | referencia a modelo activo | si, como output canonico final |
| generacion de video | si (`video_generation`) | si (`generated_image`, `thumbnail`) o artefacto futuro de video | placeholder o modelo futuro | si, preparado contractualmente |
| QA | si | si (`qa_report`) | no | actualiza `qa_status` del contenido |

## Reglas de consistencia

- todo timestamp debe estar en UTC
- `failed` y `timed_out` requieren `error_message` persistible en `Job`
- `dataset_package` y `lora_model` requieren `checksum_sha256`
- `lora` requiere `parent_model_id`, `storage_path` y `model_family=custom_lora`
- `base_model` de `S1` y `S2` debe permanecer en la familia `flux`
- `video_placeholder` no persiste binario todavia y requiere `model_family=future_video`
- `base_model_id` siempre debe persistirse para poder validar compatibilidad entre `S1`, `training` y `S2`

## Catalogo inicial registrado

El repositorio ahora define un seed minimo reusable en `src/vixenbliss_creator/s1_control/model_registry_store.py`.

Entradas iniciales:

- `flux-schnell-v1`
  - rol: `base_model`
  - familia: `flux`
  - compatibilidades declaradas: `ComfyUI`, `LoRA`, `IP-Adapter`, `ControlNet`
- `future-video-placeholder-v1`
  - rol: `video_placeholder`
  - familia: `future_video`
  - objetivo: reservar contrato de video sin persistir binario todavia

Politica de versionado inicial:

- modelos base: `version_name` inmutable por familia y proveedor
- LoRAs: version derivada de `base_model_id` y del entrenamiento efectivo
- placeholders de video: contrato versionado hasta reemplazo por runtime real

## Regla de persistencia para `S1 image`

Para el handoff `S1 image -> S1 lora train`:

- `dataset_manifest` es obligatorio como artifact persistido
- `dataset_package` debe persistirse mientras exista QA manual o mientras el training no pueda reconstruir el dataset solo desde el manifest
- la fuente de verdad recomendada para ambos es storage externo (`Directus Files`, `Supabase Storage` o `S3-compatible`)
- `Modal Volume` puede usarse como cache o staging efimero, pero no como registro persistente entre servicios

## Modos de handoff admitidos

### `review`

- `S1 image` genera `dataset_manifest`
- `S1 image` genera `dataset_package`
- el operador revisa calidad
- `S1 lora train` se habilita solo despues de aprobacion

### `autopromote`

- `S1 image` genera `dataset_manifest`
- `S1 image` persiste `dataset_package` con retencion corta o suficiente para retry
- el orquestador dispara `lora_training` automaticamente
- luego se aplica cleanup de artifacts temporales segun politica operativa

## Payloads validos de ejemplo

```json
{
  "job": {
    "schema_version": "1.0.0",
    "id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
    "identity_id": "1b4e28ba-2fa1-11d2-883f-0016d3cca427",
    "job_type": "identity_image_generation",
    "status": "succeeded",
    "timeout_seconds": 1800,
    "attempt_count": 1,
    "payload_json": {
      "prompt_bundle": {
        "positive": "editorial portrait",
        "negative": "distorted anatomy"
      }
    },
    "metadata_json": {
      "worker": "comfyui-gpu-01",
      "provider": "runpod"
    },
    "error_message": null,
    "queued_at": "2026-03-30T15:00:00+00:00",
    "started_at": "2026-03-30T15:00:00+00:00",
    "finished_at": "2026-03-30T15:00:00+00:00",
    "created_at": "2026-03-30T15:00:00+00:00",
    "updated_at": "2026-03-30T15:00:00+00:00"
  },
  "artifact": {
    "schema_version": "1.0.0",
    "id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
    "identity_id": "1b4e28ba-2fa1-11d2-883f-0016d3cca427",
    "artifact_type": "lora_model",
    "storage_path": "models/amber_vault/lora/v1/amber-v1.safetensors",
    "source_job_id": "7d444840-9dc0-11d1-b245-5ffdce74fad2",
    "base_model_id": "flux-schnell-v1",
    "model_version_used": "lora-v1",
    "checksum_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "content_type": "application/octet-stream",
    "size_bytes": 2048,
    "metadata_json": {
      "provider": "runpod",
      "training_steps": 1200
    },
    "created_at": "2026-03-30T15:00:00+00:00",
    "updated_at": "2026-03-30T15:00:00+00:00"
  },
  "model_registry": {
    "schema_version": "1.0.0",
    "id": "7d444840-9dc0-11d1-b245-5ffdce74fad2",
    "model_family": "custom_lora",
    "model_role": "lora",
    "provider": "internal",
    "version_name": "amber-v1",
    "display_name": "Amber Vault LoRA v1",
    "base_model_id": "flux-schnell-v1",
    "storage_path": "models/amber_vault/lora/v1/amber-v1.safetensors",
    "parent_model_id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
    "compatibility_notes": "Compatible con Flux Schnell para identidades del MVP.",
    "quantization": "fp8",
    "is_active": true,
    "metadata_json": {
      "base_model": "flux-schnell-v1",
      "trigger_word": "amber_vault"
    },
    "created_at": "2026-03-30T15:00:00+00:00",
    "updated_at": "2026-03-30T15:00:00+00:00",
    "deprecated_at": null
  }
}
```
