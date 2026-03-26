from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from vixenbliss_creator.contracts.identity import Identity


def build_valid_payload() -> dict:
    timestamp = datetime(2026, 3, 26, 15, 0, tzinfo=timezone.utc).isoformat()
    return {
        "id": str(uuid4()),
        "alias": "amber_vault",
        "status": "draft",
        "pipeline_state": "draft",
        "vertical": "adult_entertainment",
        "allowed_content_modes": ["sfw", "sensual", "nsfw"],
        "reference_face_image_url": "https://example.com/reference-face.png",
        "base_image_urls": [
            "https://example.com/base-01.png",
            "https://example.com/base-02.png",
        ],
        "dataset_storage_path": None,
        "dataset_status": "not_started",
        "base_model_id": "flux-schnell-v1",
        "lora_model_path": None,
        "lora_version": None,
        "technical_sheet_json": {
            "schema_version": "1.0.0",
            "identity_core": {
                "display_name": "Amber Vault",
                "fictional_age_years": 24,
                "locale": "es-AR",
                "primary_language": "spanish",
                "secondary_languages": ["english"],
                "tagline": "Performer elegante con tono seguro y cercano.",
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
                "visual_never_do": ["cartoon_style", "heavy_face_distortion"],
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
                    "accessibility": "medium",
                },
            },
            "narrative_profile": {
                "archetype_summary": "Anfitriona digital premium que mezcla glamour editorial con cercanía medida.",
                "origin_story": "Construyó su audiencia convirtiendo sesiones íntimas curadas en una marca de alto valor visual.",
                "motivations": ["grow_premium_audience", "protect_brand_consistency"],
                "interests": ["fashion", "fitness", "nightlife"],
                "audience_role": "fantasy_guide",
                "conversational_hooks": ["after_hours_stories", "style_breakdowns"],
            },
            "operational_limits": {
                "allowed_content_modes": ["sfw", "sensual", "nsfw"],
                "hard_limits": [
                    {
                        "code": "no_minors",
                        "label": "No underage framing",
                        "severity": "hard",
                        "rationale": "El personaje siempre se representa como adulto ficticio.",
                    }
                ],
                "soft_limits": [
                    {
                        "code": "avoid_body_horror",
                        "label": "Avoid body horror aesthetics",
                        "severity": "soft",
                        "rationale": "Mantener consistencia aspiracional del personaje.",
                    }
                ],
                "escalation_triggers": ["identity_drift", "unsafe_request"],
            },
            "system5_slots": {
                "persona_summary": "Figura segura, elegante y provocadora que responde con precisión emocional.",
                "greeting_style": "Abre la conversación con curiosidad segura y una invitación breve.",
                "reply_style_keywords": ["flirty", "direct", "premium"],
                "memory_tags": ["style_preferences", "favorite_scenarios", "upsell_readiness"],
                "prohibited_topics": ["illegal_content", "real_world_personal_data"],
                "upsell_style": "Escala desde complicidad ligera hacia ofertas premium sin romper personaje.",
            },
            "traceability": {
                "source_issue_id": "DEV-6",
                "source_epic_id": "DEV-3",
                "contract_owner": "Codex",
                "future_systems_ready": ["system_2", "system_5"],
                "last_reviewed_at": timestamp,
            },
        },
        "created_at": timestamp,
        "updated_at": timestamp,
    }


def test_identity_accepts_valid_payload() -> None:
    identity = Identity.model_validate(build_valid_payload())

    assert identity.status == "draft"
    assert identity.pipeline_state == "draft"
    assert identity.technical_sheet_json.identity_core.display_name == "Amber Vault"


def test_identity_rejects_mismatched_allowed_content_modes() -> None:
    payload = build_valid_payload()
    payload["technical_sheet_json"]["operational_limits"]["allowed_content_modes"] = ["sfw", "sensual"]

    with pytest.raises(ValidationError):
        Identity.model_validate(payload)


def test_identity_rejects_duplicate_allowed_content_modes() -> None:
    payload = build_valid_payload()
    payload["allowed_content_modes"] = ["sfw", "sfw"]
    payload["technical_sheet_json"]["operational_limits"]["allowed_content_modes"] = ["sfw", "sfw"]

    with pytest.raises(ValidationError):
        Identity.model_validate(payload)


def test_identity_rejects_non_utc_timestamps() -> None:
    payload = build_valid_payload()
    payload["created_at"] = "2026-03-26T12:00:00-03:00"
    payload["updated_at"] = "2026-03-26T12:00:00-03:00"
    payload["technical_sheet_json"]["traceability"]["last_reviewed_at"] = "2026-03-26T12:00:00-03:00"

    with pytest.raises(ValidationError):
        Identity.model_validate(payload)
