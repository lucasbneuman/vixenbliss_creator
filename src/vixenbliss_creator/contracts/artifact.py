from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import Field, model_validator

from .common import ContractBaseModel, JsonObject, is_utc_datetime, utc_now


class ArtifactSchemaVersion(str, Enum):
    V1 = "1.0.0"


class ArtifactType(str, Enum):
    BASE_IMAGE = "base_image"
    DATASET_MANIFEST = "dataset_manifest"
    DATASET_PACKAGE = "dataset_package"
    LORA_MODEL = "lora_model"
    WORKFLOW_JSON = "workflow_json"
    GENERATED_IMAGE = "generated_image"
    THUMBNAIL = "thumbnail"
    QA_REPORT = "qa_report"


class Artifact(ContractBaseModel):
    schema_version: ArtifactSchemaVersion = ArtifactSchemaVersion.V1
    id: UUID
    identity_id: UUID
    artifact_type: ArtifactType
    storage_path: str = Field(min_length=3, max_length=255)
    source_job_id: UUID | None = None
    base_model_id: str | None = Field(default=None, min_length=3, max_length=120)
    model_version_used: str | None = Field(default=None, min_length=1, max_length=64)
    checksum_sha256: str | None = Field(default=None, pattern=r"^[A-Fa-f0-9]{64}$")
    content_type: str | None = Field(default=None, min_length=3, max_length=120)
    size_bytes: int | None = Field(default=None, ge=1)
    metadata_json: JsonObject = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def validate_consistency(self) -> "Artifact":
        if not is_utc_datetime(self.created_at):
            raise ValueError("created_at must be a UTC datetime")
        if not is_utc_datetime(self.updated_at):
            raise ValueError("updated_at must be a UTC datetime")
        if self.created_at > self.updated_at:
            raise ValueError("created_at cannot be later than updated_at")
        if self.artifact_type in {ArtifactType.BASE_IMAGE, ArtifactType.GENERATED_IMAGE, ArtifactType.THUMBNAIL}:
            if self.content_type is None:
                raise ValueError("image artifacts require content_type")
        if self.artifact_type in {ArtifactType.DATASET_PACKAGE, ArtifactType.LORA_MODEL} and self.checksum_sha256 is None:
            raise ValueError("dataset_package and lora_model artifacts require checksum_sha256")
        return self
