# Traceability Contracts

## Objetivo

Definir los contratos canonicos y persistibles de `Job`, `Artifact` y `ModelRegistry` para trazabilidad operativa del MVP de `VixenBliss Creator`.

Este documento fija:

- tipos y estados minimos de ejecucion asincrona
- artefactos tecnicos obligatorios por flujo
- catalogo minimo de modelos base, LoRAs y placeholders de video
- relaciones principales hacia `Identity`

## Version vigente

- `Job.schema_version`: `1.0.0`
- `Artifact.schema_version`: `1.0.0`
- `ModelRegistry.schema_version`: `1.0.0`
- contratos fuente Python: `src/vixenbliss_creator/contracts/job.py`, `artifact.py`, `model_registry.py`

## Contrato `Job`

### Tipos de job MVP

- `create_identity`
- `generate_base_images`
- `build_dataset`
- `validate_dataset`
- `train_lora`
- `generate_content`
- `prepare_video`
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
| `storage_path` | string nullable | no | ubicacion de binario si existe |
| `parent_model_id` | UUID nullable | no | relacion LoRA -> modelo base |
| `compatibility_notes` | string nullable | no | notas de compatibilidad |
| `is_active` | bool | si | diferenciacion entre activo e historico |
| `metadata_json` | json | si | extensibilidad futura |
| `created_at` | timestamp UTC | si | auditoria |
| `updated_at` | timestamp UTC | si | sincronizacion |
| `deprecated_at` | timestamp UTC nullable | no | retiro controlado |

## Matriz flujo -> registros obligatorios

| Flujo | `Job` | `Artifact` | `ModelRegistry` |
|---|---|---|---|
| creacion de identidad | si | no obligatorio | no |
| generacion de imagen base | si | si (`base_image`, `workflow_json`) | referencia a modelo base |
| armado de dataset | si | si (`dataset_manifest`, `dataset_package`) | no |
| entrenamiento LoRA | si | si (`lora_model`) | si (`lora`) |
| generacion de contenido | si | si (`generated_image`, `thumbnail`) | referencia a modelo activo |
| QA | si | si (`qa_report`) | no |

## Reglas de consistencia

- todo timestamp debe estar en UTC
- `failed` y `timed_out` requieren `error_message` persistible en `Job`
- `dataset_package` y `lora_model` requieren `checksum_sha256`
- `lora` requiere `parent_model_id` y `storage_path`
- `video_placeholder` no persiste binario todavia

## Payloads validos de ejemplo

```json
{
  "job": {
    "schema_version": "1.0.0",
    "id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
    "identity_id": "1b4e28ba-2fa1-11d2-883f-0016d3cca427",
    "job_type": "generate_base_images",
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
    "storage_path": "models/amber_vault/lora/v1/amber-v1.safetensors",
    "parent_model_id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
    "compatibility_notes": "Compatible con Flux Schnell para identidades del MVP.",
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
