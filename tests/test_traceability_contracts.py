from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from vixenbliss_creator.contracts.artifact import Artifact
from vixenbliss_creator.contracts.content import Content
from vixenbliss_creator.contracts.identity import Identity
from vixenbliss_creator.contracts.job import Job, is_valid_job_transition
from vixenbliss_creator.contracts.model_registry import ModelRegistry
from vixenbliss_creator.contracts.pipeline_guards import (
    assert_base_model_registered,
    assert_content_generation_allowed,
    assert_lora_training_allowed,
)
from vixenbliss_creator.s1_control import default_model_catalog


def build_job_payload() -> dict:
    timestamp = datetime(2026, 3, 30, 15, 0, tzinfo=timezone.utc).isoformat()
    return {
        "id": str(uuid4()),
        "identity_id": str(uuid4()),
        "job_type": "identity_image_generation",
        "status": "succeeded",
        "timeout_seconds": 1800,
        "attempt_count": 1,
        "payload_json": {
            "prompt_bundle": {
                "positive": "editorial portrait",
                "negative": "distorted anatomy",
            }
        },
        "metadata_json": {
            "worker": "comfyui-gpu-01",
            "provider": "runpod",
        },
        "error_message": None,
        "queued_at": timestamp,
        "started_at": timestamp,
        "finished_at": timestamp,
        "created_at": timestamp,
        "updated_at": timestamp,
    }


def build_artifact_payload() -> dict:
    timestamp = datetime(2026, 3, 30, 15, 0, tzinfo=timezone.utc).isoformat()
    return {
        "id": str(uuid4()),
        "identity_id": str(uuid4()),
        "artifact_type": "lora_model",
        "storage_path": "models/amber_vault/lora/v1/amber-v1.safetensors",
        "source_job_id": str(uuid4()),
        "base_model_id": "flux-schnell-v1",
        "model_version_used": "lora-v1",
        "checksum_sha256": "a" * 64,
        "content_type": "application/octet-stream",
        "size_bytes": 2048,
        "metadata_json": {
            "provider": "runpod",
            "training_steps": 1200,
        },
        "created_at": timestamp,
        "updated_at": timestamp,
    }


def build_model_registry_payload() -> dict:
    timestamp = datetime(2026, 3, 30, 15, 0, tzinfo=timezone.utc).isoformat()
    return {
        "id": str(uuid4()),
        "model_family": "custom_lora",
        "model_role": "lora",
        "provider": "internal",
        "version_name": "amber-v1",
        "display_name": "Amber Vault LoRA v1",
        "base_model_id": "flux-schnell-v1",
        "storage_path": "models/amber_vault/lora/v1/amber-v1.safetensors",
        "parent_model_id": str(uuid4()),
        "compatibility_notes": "Compatible con Flux Schnell para identidades del MVP.",
        "quantization": "fp8",
        "is_active": True,
        "metadata_json": {
            "base_model": "flux-schnell-v1",
            "trigger_word": "amber_vault",
        },
        "created_at": timestamp,
        "updated_at": timestamp,
        "deprecated_at": None,
    }


def build_content_payload() -> dict:
    timestamp = datetime(2026, 3, 30, 15, 0, tzinfo=timezone.utc).isoformat()
    return {
        "id": str(uuid4()),
        "identity_id": str(uuid4()),
        "content_mode": "image",
        "generation_status": "generated",
        "qa_status": "not_reviewed",
        "job_id": "job-123",
        "primary_artifact_id": "artifact-123",
        "related_artifact_ids": ["artifact-123", "artifact-456"],
        "base_model_id": "flux-schnell-v1",
        "model_version_used": "content-v1",
        "provider": "modal",
        "workflow_id": "content-image-flux-lora",
        "prompt": "editorial portrait with controlled visual consistency",
        "negative_prompt": "bad anatomy, low quality, watermark",
        "seed": 2026,
        "metadata_json": {
            "artifact_role": "generated_image",
        },
        "created_at": timestamp,
        "updated_at": timestamp,
    }


def build_identity_payload() -> dict:
    timestamp = datetime(2026, 3, 30, 15, 0, tzinfo=timezone.utc).isoformat()
    return {
        "id": str(uuid4()),
        "alias": "amber_vault",
        "status": "draft",
        "pipeline_state": "lora_validated",
        "vertical": "adult_entertainment",
        "allowed_content_modes": ["sfw", "sensual", "nsfw"],
        "reference_face_image_url": "https://example.com/reference-face.png",
        "base_image_urls": ["https://example.com/base-01.png"],
        "dataset_storage_path": "datasets/amber_vault/v1",
        "dataset_status": "ready",
        "base_model_id": "flux-schnell-v1",
        "lora_model_path": "models/amber_vault/lora/v1/amber-v1.safetensors",
        "lora_version": "amber-v1",
        "technical_sheet_json": {
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
                "dominant_features": ["defined_jawline", "freckles"],
                "wardrobe_styles": ["lingerie_editorial"],
                "visual_must_haves": ["soft_gold_lighting"],
                "visual_never_do": ["cartoon_style"],
            },
            "personality_profile": {
                "voice_tone": "seductive",
                "primary_traits": ["confident", "playful"],
                "secondary_traits": ["warm", "strategic"],
                "interaction_style": "Coquetea con precision, sin perder claridad ni control de la escena.",
                "axes": {
                    "formality": "medium",
                    "warmth": "high",
                    "dominance": "medium",
                    "provocation": "high",
                    "accessibility": "medium",
                },
            },
            "narrative_profile": {
                "archetype_summary": "Anfitriona digital premium que mezcla glamour editorial con cercania medida.",
                "origin_story": "Construyo su audiencia convirtiendo sesiones intimas curadas en una marca de alto valor visual.",
                "motivations": ["grow_premium_audience", "protect_brand_consistency"],
                "interests": ["fashion", "fitness"],
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
                "persona_summary": "Figura segura, elegante y provocadora que responde con precision emocional.",
                "greeting_style": "Abre la conversacion con curiosidad segura y una invitacion breve.",
                "reply_style_keywords": ["flirty", "direct"],
                "memory_tags": ["style_preferences", "favorite_scenarios"],
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


def test_job_accepts_valid_payload() -> None:
    job = Job.model_validate(build_job_payload())

    assert job.status == "succeeded"
    assert job.job_type == "identity_image_generation"


def test_job_accepts_legacy_job_type_aliases() -> None:
    payload = build_job_payload()
    payload["job_type"] = "generate_base_images"

    job = Job.model_validate(payload)

    assert job.job_type == "identity_image_generation"


def test_job_requires_error_message_for_failed_state() -> None:
    payload = build_job_payload()
    payload["status"] = "failed"
    payload["error_message"] = None

    with pytest.raises(ValidationError):
        Job.model_validate(payload)


def test_job_rejects_non_utc_timestamps() -> None:
    payload = build_job_payload()
    payload["created_at"] = "2026-03-30T12:00:00-03:00"

    with pytest.raises(ValidationError):
        Job.model_validate(payload)


def test_job_transition_matrix() -> None:
    assert is_valid_job_transition("pending", "running") is True
    assert is_valid_job_transition("running", "succeeded") is True
    assert is_valid_job_transition("succeeded", "running") is False


def test_artifact_accepts_valid_payload() -> None:
    artifact = Artifact.model_validate(build_artifact_payload())

    assert artifact.artifact_type == "lora_model"
    assert artifact.checksum_sha256 == "a" * 64


def test_artifact_requires_checksum_for_lora() -> None:
    payload = build_artifact_payload()
    payload["checksum_sha256"] = None

    with pytest.raises(ValidationError):
        Artifact.model_validate(payload)


def test_content_accepts_valid_payload() -> None:
    content = Content.model_validate(build_content_payload())

    assert content.content_mode == "image"
    assert content.provider == "modal"


def test_content_rejects_generated_image_without_job_id() -> None:
    payload = build_content_payload()
    payload["job_id"] = None

    with pytest.raises(ValidationError):
        Content.model_validate(payload)


def test_content_accepts_prepared_image_to_video_payload() -> None:
    payload = build_content_payload()
    payload.update(
        {
            "content_mode": "video",
            "video_generation_mode": "image_to_video",
            "generation_status": "pending",
            "job_id": None,
            "primary_artifact_id": None,
            "source_artifact_id": "artifact-123",
            "duration_seconds": None,
            "frame_count": None,
            "frame_rate": None,
        }
    )

    content = Content.model_validate(payload)

    assert content.video_generation_mode == "image_to_video"
    assert content.source_artifact_id == "artifact-123"


def test_model_registry_accepts_valid_payload() -> None:
    model = ModelRegistry.model_validate(build_model_registry_payload())

    assert model.model_role == "lora"
    assert model.provider == "internal"
    assert model.base_model_id == "flux-schnell-v1"
    assert model.quantization == "fp8"


def test_model_registry_backfills_base_model_id_from_metadata_for_legacy_records() -> None:
    payload = build_model_registry_payload()
    payload.pop("base_model_id")

    model = ModelRegistry.model_validate(payload)

    assert model.base_model_id == "flux-schnell-v1"


def test_model_registry_requires_parent_model_for_lora() -> None:
    payload = build_model_registry_payload()
    payload["parent_model_id"] = None

    with pytest.raises(ValidationError):
        ModelRegistry.model_validate(payload)


def test_model_registry_rejects_storage_for_video_placeholder() -> None:
    payload = build_model_registry_payload()
    payload["model_role"] = "video_placeholder"
    payload["model_family"] = "future_video"
    payload["storage_path"] = "video/placeholders/v1"
    payload["parent_model_id"] = None

    with pytest.raises(ValidationError):
        ModelRegistry.model_validate(payload)


def test_model_registry_rejects_base_models_outside_flux_family() -> None:
    payload = build_model_registry_payload()
    payload["model_role"] = "base_model"
    payload["model_family"] = "custom_lora"
    payload["parent_model_id"] = None

    with pytest.raises(ValidationError):
        ModelRegistry.model_validate(payload)


def test_model_registry_rejects_lora_with_wrong_family() -> None:
    payload = build_model_registry_payload()
    payload["model_family"] = "flux"

    with pytest.raises(ValidationError):
        ModelRegistry.model_validate(payload)


def test_registered_base_model_allows_identity_to_advance() -> None:
    identity = Identity.model_validate(build_identity_payload())

    assert_base_model_registered(identity, default_model_catalog())


def test_identity_rejects_unknown_base_model_against_registry() -> None:
    payload = build_identity_payload()
    payload["base_model_id"] = "unknown-base-model"
    identity = Identity.model_validate(payload)

    with pytest.raises(ValueError, match="registered active base_model_id"):
        assert_base_model_registered(identity, default_model_catalog())


def test_lora_training_requires_ready_dataset() -> None:
    payload = build_identity_payload()
    payload["dataset_status"] = "in_progress"
    identity = Identity.model_validate(payload)

    with pytest.raises(ValueError, match="dataset_status=ready"):
        assert_lora_training_allowed(identity)


def test_content_generation_requires_validated_lora() -> None:
    payload = build_identity_payload()
    payload["pipeline_state"] = "lora_trained"
    identity = Identity.model_validate(payload)

    with pytest.raises(ValueError, match="pipeline_state=lora_validated"):
        assert_content_generation_allowed(identity)
