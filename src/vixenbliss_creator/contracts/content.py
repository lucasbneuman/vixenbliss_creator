from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import Field, model_validator

from vixenbliss_creator.provider import Provider

from .common import ContractBaseModel, JsonObject, is_utc_datetime, utc_now


class ContentSchemaVersion(str, Enum):
    V1 = "1.0.0"


class ContentMode(str, Enum):
    IMAGE = "image"
    VIDEO = "video"


class VideoGenerationMode(str, Enum):
    TEXT_TO_VIDEO = "text_to_video"
    IMAGE_TO_VIDEO = "image_to_video"


class GenerationStatus(str, Enum):
    PENDING = "pending"
    GENERATED = "generated"
    FAILED = "failed"
    ARCHIVED = "archived"


class QAStatus(str, Enum):
    NOT_REVIEWED = "not_reviewed"
    APPROVED = "approved"
    REJECTED = "rejected"


class Content(ContractBaseModel):
    schema_version: ContentSchemaVersion = ContentSchemaVersion.V1
    id: str = Field(min_length=1, max_length=120)
    identity_id: str = Field(min_length=1, max_length=120)
    content_mode: ContentMode
    video_generation_mode: VideoGenerationMode | None = None
    generation_status: GenerationStatus = GenerationStatus.PENDING
    qa_status: QAStatus = QAStatus.NOT_REVIEWED
    job_id: str | None = Field(default=None, min_length=1, max_length=120)
    primary_artifact_id: str | None = Field(default=None, min_length=1, max_length=120)
    related_artifact_ids: list[str] = Field(default_factory=list, max_length=24)
    base_model_id: str | None = Field(default=None, min_length=3, max_length=120)
    model_version_used: str | None = Field(default=None, min_length=1, max_length=64)
    provider: Provider | None = None
    workflow_id: str | None = Field(default=None, min_length=3, max_length=120)
    prompt: str | None = Field(default=None, min_length=3, max_length=4000)
    negative_prompt: str | None = Field(default=None, min_length=3, max_length=4000)
    seed: int | None = Field(default=None, ge=0, le=2**32 - 1)
    source_content_id: str | None = Field(default=None, min_length=1, max_length=120)
    source_artifact_id: str | None = Field(default=None, min_length=1, max_length=120)
    duration_seconds: float | None = Field(default=None, gt=0.0, le=86400.0)
    frame_count: int | None = Field(default=None, ge=1, le=10_000_000)
    frame_rate: float | None = Field(default=None, gt=0.0, le=480.0)
    metadata_json: JsonObject = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def validate_consistency(self) -> "Content":
        if not is_utc_datetime(self.created_at):
            raise ValueError("created_at must be a UTC datetime")
        if not is_utc_datetime(self.updated_at):
            raise ValueError("updated_at must be a UTC datetime")
        if self.created_at > self.updated_at:
            raise ValueError("created_at cannot be later than updated_at")
        if len(set(self.related_artifact_ids)) != len(self.related_artifact_ids):
            raise ValueError("related_artifact_ids must not contain duplicates")
        if self.content_mode == ContentMode.IMAGE:
            if any(value is not None for value in (self.video_generation_mode, self.source_content_id, self.source_artifact_id)):
                raise ValueError("image content must not define video request fields")
            if any(value is not None for value in (self.duration_seconds, self.frame_count, self.frame_rate)):
                raise ValueError("image content must not define video timing fields")
        if self.content_mode == ContentMode.VIDEO:
            if self.video_generation_mode is None:
                raise ValueError("video content requires video_generation_mode")
            if self.video_generation_mode == VideoGenerationMode.TEXT_TO_VIDEO and any(
                value is not None for value in (self.source_content_id, self.source_artifact_id)
            ):
                raise ValueError("text_to_video content must not define source_content_id or source_artifact_id")
            if self.video_generation_mode == VideoGenerationMode.IMAGE_TO_VIDEO and not any(
                value is not None for value in (self.source_content_id, self.source_artifact_id)
            ):
                raise ValueError("image_to_video content requires source_content_id or source_artifact_id")
            video_metrics = (self.duration_seconds, self.frame_count, self.frame_rate)
            if any(value is not None for value in video_metrics) and not all(value is not None for value in video_metrics):
                raise ValueError("video content timing fields must be provided together")
            if self.generation_status == GenerationStatus.GENERATED and not all(value is not None for value in video_metrics):
                raise ValueError("generated video content requires duration_seconds, frame_count and frame_rate")
        if self.generation_status == GenerationStatus.GENERATED:
            required_fields = {
                "job_id": self.job_id,
                "primary_artifact_id": self.primary_artifact_id,
                "base_model_id": self.base_model_id,
                "model_version_used": self.model_version_used,
                "provider": self.provider,
                "workflow_id": self.workflow_id,
                "prompt": self.prompt,
                "negative_prompt": self.negative_prompt,
                "seed": self.seed,
            }
            missing = [field_name for field_name, value in required_fields.items() if value is None]
            if missing:
                missing_fields = ", ".join(sorted(missing))
                raise ValueError(f"generated content requires complete traceability fields: {missing_fields}")
        if self.qa_status in {QAStatus.APPROVED, QAStatus.REJECTED} and self.generation_status != GenerationStatus.GENERATED:
            raise ValueError("qa_status can only be approved or rejected after content generation")
        return self
