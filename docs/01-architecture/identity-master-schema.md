# Identity Master Schema

## Objetivo

Definir el contrato canonico y versionado de `Identity` y `technical_sheet_json` para `Sistema 1`, incorporando personalidad estructurada, metadata comercial y trazabilidad por campo.

Contrato fuente:

- `src/vixenbliss_creator/contracts/identity.py`
- ensamblado canonico desde `LangGraph`: `src/vixenbliss_creator/s1_control/identity_service.py`

## Cambios relevantes del contrato

### Metadata de identidad

`TechnicalSheet` ahora incluye `identity_metadata` con:

- `avatar_id`
- `category`
- `vertical`
- `style`
- `occupation_or_content_basis`

Estos campos dejan de ser simple contexto narrativo y pasan a sesgar la personalidad y la ficha final.

### Personalidad estructurada

`personality_profile` ahora contempla:

- `archetype`
- `voice_tone`
- `primary_traits`
- `secondary_traits`
- `interaction_style`
- `axes`
- `communication_style`
- `social_behavior`

#### Axes

- `dominance`
- `warmth`
- `playfulness`
- `mystery`
- `flirtiness`
- `intelligence`
- `sarcasm`

Todos usan escala uniforme:

- `very_low`
- `low`
- `medium`
- `high`
- `very_high`

#### Communication style

- `speech_style`
- `message_length`
- `emoji_usage`
- `emoji_style`
- `punctuation_style`

#### Social behavior

- `fan_relationship_style`
- `attention_strategy`
- `response_energy`
- `jealousy_play`

### Narrativa minima viable

`narrative_profile` incorpora `minimal_viable_profile` con:

- `origin`
- `interests`
- `daily_life`
- `motivation`
- `relationship_with_fans`

### Trazabilidad por campo

`traceability.field_traces` registra la procedencia de campos relevantes mediante:

- `field_path`
- `origin`
- `source_text`
- `confidence`
- `rationale`

Orígenes soportados:

- `manual`
- `inferred`
- `defaulted`
- `derived`

## Invariantes de consistencia

- `allowed_content_modes` top-level y `technical_sheet_json.operational_limits.allowed_content_modes` deben coincidir exactamente
- `fictional_age_years >= 18`
- `field_traces` no reemplaza el valor del campo; solo registra procedencia
- una identidad final de `Sistema 1` debe poder reconstruir:
  - que fijo el operador
  - que infirio el sistema
  - que autocompleto el LLM
- `vertical`, `category`, `style` y `occupation_or_content_basis` deben ser coherentes con la personalidad y la narrativa

## Materializacion del payload persistible

El repo ahora define un ensamblado canonico `GraphState -> Identity` para evitar que cada caller reconstruya la entidad final con reglas propias.

Reglas actuales:

- solo se materializa una `Identity` cuando `GraphState.completion_status = succeeded`
- `base_model_id` se toma desde `CopilotRecommendation` salvo override explicito
- `alias` se deriva de `identity_core.display_name` con normalizacion ASCII y formato `snake_case`
- el estado inicial por defecto queda en `pipeline_state = identity_created`
- el resultado queda listo para persistirse sin transformaciones adicionales

## Slots listos para Sistema 5

Quedan preparados para consumo futuro:

- `identity_core.display_name`
- `identity_core.tagline`
- `identity_metadata.category`
- `identity_metadata.style`
- `personality_profile.archetype`
- `personality_profile.axes`
- `personality_profile.communication_style`
- `personality_profile.social_behavior`
- `narrative_profile.minimal_viable_profile`
- `system5_slots.*`

## Ejemplo resumido

```json
{
  "schema_version": "1.0.0",
  "identity_metadata": {
    "avatar_id": "avatar_velvet_ember",
    "category": "lifestyle_premium",
    "vertical": "lifestyle",
    "style": "premium",
    "occupation_or_content_basis": "luxury lifestyle creator"
  },
  "identity_core": {
    "display_name": "Velvet Ember",
    "fictional_age_years": 25,
    "locale": "es-AR",
    "primary_language": "spanish",
    "secondary_languages": ["english"],
    "tagline": "Identidad premium con personalidad consistente."
  },
  "personality_profile": {
    "archetype": "luxury_muse",
    "voice_tone": "authoritative",
    "axes": {
      "dominance": "medium",
      "warmth": "high",
      "playfulness": "medium",
      "mystery": "high",
      "flirtiness": "high",
      "intelligence": "high",
      "sarcasm": "medium"
    },
    "communication_style": {
      "speech_style": "refined",
      "message_length": "medium",
      "emoji_usage": "moderate",
      "emoji_style": "sparkles",
      "punctuation_style": "polished"
    },
    "social_behavior": {
      "fan_relationship_style": "aspirational_muse",
      "attention_strategy": "balanced",
      "response_energy": "medium",
      "jealousy_play": "light"
    }
  },
  "traceability": {
    "field_traces": [
      {
        "field_path": "metadata.vertical",
        "origin": "manual",
        "source_text": "Quiero lifestyle premium",
        "confidence": 1.0,
        "rationale": "Constraint explicito del operador"
      }
    ]
  }
}
```
