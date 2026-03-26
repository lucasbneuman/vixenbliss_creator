# Identity Master Schema

## Objetivo

Definir el contrato canonico y versionado de `Identity` y `technical_sheet_json` para el MVP reforzado de `VixenBliss Creator`.

Este documento fija:

- campos top-level persistibles
- estructura anidada de `technical_sheet_json`
- enums, defaults y nulabilidad
- correspondencia campo -> persistencia relacional
- slots preparados para consumo futuro por Sistema 5

## Version vigente

- `Identity.schema_version`: `1.0.0`
- `technical_sheet_json.schema_version`: `1.0.0`
- contrato fuente Python: `src/vixenbliss_creator/contracts/identity.py`

## Enums y defaults

| Campo | Valores controlados | Default |
|---|---|---|
| `status` | `draft`, `active`, `paused`, `archived` | `draft` |
| `pipeline_state` | `draft`, `identity_created`, `base_images_generated`, `base_images_registered`, `dataset_ready`, `lora_training_pending`, `lora_training_running`, `lora_trained`, `lora_validated`, `video_ready_for_future_integration` | `draft` |
| `vertical` | `adult_entertainment`, `lifestyle`, `performance`, `experimental` | sin default |
| `allowed_content_modes` | `sfw`, `sensual`, `nsfw` | sin default |
| `dataset_status` | `not_started`, `in_progress`, `ready`, `rejected` | `not_started` |
| `technical_sheet_json.personality_profile.voice_tone` | `formal`, `informal`, `playful`, `authoritative`, `seductive` | sin default |

## Modelo top-level de `Identity`

Estos campos son candidatos directos a columnas de `identities` porque se consultan, indexan o actualizan con frecuencia operativa.

| Campo | Tipo | Req. | Persistencia esperada | Razon operacional |
|---|---|---|---|---|
| `schema_version` | enum/string | si | columna | versionado del contrato |
| `id` | UUID | si | PK | identidad estable |
| `alias` | string controlado | si | unique index | lookup operativo y naming estable |
| `status` | enum | si | index | estado comercial/operativo |
| `pipeline_state` | enum | si | index | progreso del pipeline |
| `vertical` | enum | si | index | segmentacion de audiencia y flujo |
| `allowed_content_modes` | enum list | si | array o jsonb | gating rapido de capacidades |
| `reference_face_image_url` | URL nullable | no | columna nullable | referencia primaria de consistencia |
| `base_image_urls` | URL list | no | jsonb | referencias base iniciales |
| `dataset_storage_path` | string nullable | no | columna nullable | path estable para dataset |
| `dataset_status` | enum | si | columna/index | readiness de dataset |
| `base_model_id` | string nullable | no | FK futura | modelo base asociado |
| `lora_model_path` | string nullable | no | columna nullable | artefacto LoRA vigente |
| `lora_version` | string nullable | no | columna nullable | version visible del LoRA |
| `technical_sheet_json` | objeto estructurado | si | jsonb | ficha tecnica versionada |
| `created_at` | timestamp UTC | si | columna/index | auditoria |
| `updated_at` | timestamp UTC | si | columna/index | auditoria y sincronizacion |

## Estructura de `technical_sheet_json`

`technical_sheet_json` concentra informacion rica y relativamente estable que no conviene desnormalizar como columnas tempranas.

| Slot | Contenido | Uso principal |
|---|---|---|
| `identity_core` | nombre visible, edad ficticia adulta, locale, idiomas, tagline | consumo de producto y prompts |
| `visual_profile` | arquetipo, rasgos, vestuario, restricciones visuales | consistencia visual, prompts, QA |
| `personality_profile` | tono de voz, rasgos, ejes de interacción | captions, chat, respuestas automatizadas |
| `narrative_profile` | origen, motivaciones, intereses, hooks conversacionales | storytelling y Sistema 5 |
| `operational_limits` | modos permitidos, límites duros/blandos, triggers | fail-fast, moderación y orquestación |
| `system5_slots` | resumen de persona, estilo de saludo, memoria y upsell | consumo directo por chatbot |
| `traceability` | issue, épica, owner, fecha de revisión, sistemas destino | evidencia y gobierno del contrato |

## Reglas de consistencia

- `status` inicial por defecto: `draft`.
- `pipeline_state` inicial por defecto: `draft`.
- `created_at` y `updated_at` deben estar en UTC y `created_at <= updated_at`.
- `traceability.last_reviewed_at` no puede ser posterior a `updated_at`.
- `allowed_content_modes` top-level y `technical_sheet_json.operational_limits.allowed_content_modes` deben coincidir exactamente.
- `technical_sheet_json` no admite campos extra fuera del contrato.
- `fictional_age_years` debe ser `>= 18`.

## Slots listos para Sistema 5

Los siguientes campos quedan diseñados para consumo directo o transformación trivial por un motor conversacional:

- `technical_sheet_json.identity_core.display_name`
- `technical_sheet_json.identity_core.tagline`
- `technical_sheet_json.personality_profile.voice_tone`
- `technical_sheet_json.personality_profile.axes`
- `technical_sheet_json.narrative_profile.audience_role`
- `technical_sheet_json.narrative_profile.conversational_hooks`
- `technical_sheet_json.system5_slots.persona_summary`
- `technical_sheet_json.system5_slots.greeting_style`
- `technical_sheet_json.system5_slots.reply_style_keywords`
- `technical_sheet_json.system5_slots.memory_tags`
- `technical_sheet_json.system5_slots.prohibited_topics`
- `technical_sheet_json.system5_slots.upsell_style`

## Correspondencia campo -> persistencia

### Va en tabla `identities`

- identidad primaria y lookup: `id`, `alias`
- estado y coordinación de pipeline: `status`, `pipeline_state`, `dataset_status`
- segmentación y gating: `vertical`, `allowed_content_modes`
- referencias operativas: `reference_face_image_url`, `dataset_storage_path`, `base_model_id`, `lora_model_path`, `lora_version`
- auditoría: `created_at`, `updated_at`
- contenedor estructurado: `technical_sheet_json`

### Vive dentro de `technical_sheet_json`

- descripción rica de personaje
- rasgos visuales y restricciones de estilo
- personalidad y tono
- narrativa y hooks
- límites operacionales detallados
- slots orientados a chatbot
- metadata de trazabilidad contractual

## Payload valido de ejemplo

```json
{
  "schema_version": "1.0.0",
  "id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
  "alias": "amber_vault",
  "status": "draft",
  "pipeline_state": "draft",
  "vertical": "adult_entertainment",
  "allowed_content_modes": ["sfw", "sensual", "nsfw"],
  "reference_face_image_url": "https://example.com/reference-face.png",
  "base_image_urls": [
    "https://example.com/base-01.png",
    "https://example.com/base-02.png"
  ],
  "dataset_storage_path": null,
  "dataset_status": "not_started",
  "base_model_id": "flux-schnell-v1",
  "lora_model_path": null,
  "lora_version": null,
  "technical_sheet_json": {
    "schema_version": "1.0.0",
    "identity_core": {
      "display_name": "Amber Vault",
      "fictional_age_years": 24,
      "locale": "es-AR",
      "primary_language": "spanish",
      "secondary_languages": ["english"],
      "tagline": "Performer elegante con tono seguro y cercano."
    },
    "visual_profile": {
      "archetype": "glam urbana",
      "body_type": "athletic",
      "skin_tone": "olive",
      "eye_color": "hazel",
      "hair_color": "dark_brown",
      "hair_style": "long_soft_waves",
      "dominant_features": ["defined_jawline", "freckles", "confident_gaze"],
      "wardrobe_styles": ["lingerie_editorial", "street_glam"],
      "visual_must_haves": ["soft_gold_lighting", "clean_makeup"],
      "visual_never_do": ["cartoon_style", "heavy_face_distortion"]
    },
    "personality_profile": {
      "voice_tone": "seductive",
      "primary_traits": ["confident", "playful", "observant"],
      "secondary_traits": ["warm", "strategic"],
      "interaction_style": "Coquetea con precisión, sin perder claridad ni control de la escena.",
      "axes": {
        "formality": "medium",
        "warmth": "high",
        "dominance": "medium",
        "provocation": "high",
        "accessibility": "medium"
      }
    },
    "narrative_profile": {
      "archetype_summary": "Anfitriona digital premium que mezcla glamour editorial con cercanía medida.",
      "origin_story": "Construyó su audiencia convirtiendo sesiones íntimas curadas en una marca de alto valor visual.",
      "motivations": ["grow_premium_audience", "protect_brand_consistency"],
      "interests": ["fashion", "fitness", "nightlife"],
      "audience_role": "fantasy_guide",
      "conversational_hooks": ["after_hours_stories", "style_breakdowns"]
    },
    "operational_limits": {
      "allowed_content_modes": ["sfw", "sensual", "nsfw"],
      "hard_limits": [
        {
          "code": "no_minors",
          "label": "No underage framing",
          "severity": "hard",
          "rationale": "El personaje siempre se representa como adulto ficticio."
        }
      ],
      "soft_limits": [
        {
          "code": "avoid_body_horror",
          "label": "Avoid body horror aesthetics",
          "severity": "soft",
          "rationale": "Mantener consistencia aspiracional del personaje."
        }
      ],
      "escalation_triggers": ["identity_drift", "unsafe_request"]
    },
    "system5_slots": {
      "persona_summary": "Figura segura, elegante y provocadora que responde con precisión emocional.",
      "greeting_style": "Abre la conversación con curiosidad segura y una invitación breve.",
      "reply_style_keywords": ["flirty", "direct", "premium"],
      "memory_tags": ["style_preferences", "favorite_scenarios", "upsell_readiness"],
      "prohibited_topics": ["illegal_content", "real_world_personal_data"],
      "upsell_style": "Escala desde complicidad ligera hacia ofertas premium sin romper personaje."
    },
    "traceability": {
      "source_issue_id": "DEV-6",
      "source_epic_id": "DEV-3",
      "contract_owner": "Codex",
      "future_systems_ready": ["system_2", "system_5"],
      "last_reviewed_at": "2026-03-26T15:00:00+00:00"
    }
  },
  "created_at": "2026-03-26T15:00:00+00:00",
  "updated_at": "2026-03-26T15:00:00+00:00"
}
```
