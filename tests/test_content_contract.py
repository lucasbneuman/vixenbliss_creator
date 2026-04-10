from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from vixenbliss_creator.contracts.content import Content


def build_image_content_payload() -> dict:
    timestamp = datetime(2026, 4, 10, 15, 0, tzinfo=timezone.utc).isoformat()
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
        "model_version_used": "2026-04-08",
        "provider": "modal",
        "workflow_id": "content-image-flux-lora",
        "prompt": "editorial portrait with dramatic lighting",
        "negative_prompt": "bad anatomy, low quality",
        "seed": 42,
        "metadata_json": {"artifact_role": "generated_image"},
        "created_at": timestamp,
        "updated_at": timestamp,
    }


def build_video_content_payload() -> dict:
    payload = build_image_content_payload()
    payload.update(
        {
            "content_mode": "video",
            "video_generation_mode": "text_to_video",
            "workflow_id": "video-image-to-video-prep",
            "duration_seconds": 4.0,
            "frame_count": 96,
            "frame_rate": 24.0,
        }
    )
    return payload


def test_content_accepts_valid_image_payload() -> None:
    content = Content.model_validate(build_image_content_payload())

    assert content.content_mode == "image"
    assert content.generation_status == "generated"
    assert content.duration_seconds is None


def test_content_accepts_valid_video_payload() -> None:
    content = Content.model_validate(build_video_content_payload())

    assert content.content_mode == "video"
    assert content.video_generation_mode == "text_to_video"
    assert content.frame_rate == 24.0


def test_content_rejects_image_with_video_fields() -> None:
    payload = build_image_content_payload()
    payload["duration_seconds"] = 2.5

    with pytest.raises(ValidationError):
        Content.model_validate(payload)


def test_content_requires_complete_traceability_for_generated_image() -> None:
    payload = build_image_content_payload()
    payload["job_id"] = None

    with pytest.raises(ValidationError):
        Content.model_validate(payload)


def test_content_rejects_non_utc_timestamps() -> None:
    payload = build_image_content_payload()
    payload["created_at"] = "2026-04-10T12:00:00-03:00"

    with pytest.raises(ValidationError):
        Content.model_validate(payload)


def test_content_requires_full_video_metrics_when_generated() -> None:
    payload = build_video_content_payload()
    payload["frame_rate"] = None

    with pytest.raises(ValidationError):
        Content.model_validate(payload)


def test_content_accepts_pending_image_to_video_request() -> None:
    payload = build_video_content_payload()
    payload.update(
        {
            "generation_status": "pending",
            "video_generation_mode": "image_to_video",
            "source_artifact_id": "artifact-source-001",
            "duration_seconds": None,
            "frame_count": None,
            "frame_rate": None,
        }
    )

    content = Content.model_validate(payload)

    assert content.video_generation_mode == "image_to_video"
    assert content.source_artifact_id == "artifact-source-001"


def test_content_rejects_image_to_video_without_source_reference() -> None:
    payload = build_video_content_payload()
    payload.update(
        {
            "generation_status": "pending",
            "video_generation_mode": "image_to_video",
            "source_artifact_id": None,
            "duration_seconds": None,
            "frame_count": None,
            "frame_rate": None,
        }
    )

    with pytest.raises(ValidationError):
        Content.model_validate(payload)


def test_content_rejects_text_to_video_with_source_reference() -> None:
    payload = build_video_content_payload()
    payload["source_content_id"] = "content-source-001"

    with pytest.raises(ValidationError):
        Content.model_validate(payload)
