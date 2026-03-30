from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from vixenbliss_creator.contracts.artifact import Artifact
from vixenbliss_creator.contracts.job import Job, is_valid_job_transition
from vixenbliss_creator.contracts.model_registry import ModelRegistry


def build_job_payload() -> dict:
    timestamp = datetime(2026, 3, 30, 15, 0, tzinfo=timezone.utc).isoformat()
    return {
        "id": str(uuid4()),
        "identity_id": str(uuid4()),
        "job_type": "generate_base_images",
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
        "storage_path": "models/amber_vault/lora/v1/amber-v1.safetensors",
        "parent_model_id": str(uuid4()),
        "compatibility_notes": "Compatible con Flux Schnell para identidades del MVP.",
        "is_active": True,
        "metadata_json": {
            "base_model": "flux-schnell-v1",
            "trigger_word": "amber_vault",
        },
        "created_at": timestamp,
        "updated_at": timestamp,
        "deprecated_at": None,
    }


def test_job_accepts_valid_payload() -> None:
    job = Job.model_validate(build_job_payload())

    assert job.status == "succeeded"
    assert job.job_type == "generate_base_images"


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


def test_model_registry_accepts_valid_payload() -> None:
    model = ModelRegistry.model_validate(build_model_registry_payload())

    assert model.model_role == "lora"
    assert model.provider == "internal"


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
