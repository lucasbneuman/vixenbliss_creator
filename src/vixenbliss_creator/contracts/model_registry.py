from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import Field, model_validator

from .common import ContractBaseModel, JsonObject, is_utc_datetime, utc_now


class ModelRegistrySchemaVersion(str, Enum):
    V1 = "1.0.0"


class ModelRole(str, Enum):
    BASE_MODEL = "base_model"
    LORA = "lora"
    VIDEO_PLACEHOLDER = "video_placeholder"


class ModelFamily(str, Enum):
    FLUX = "flux"
    CUSTOM_LORA = "custom_lora"
    FUTURE_VIDEO = "future_video"


class ModelProvider(str, Enum):
    BLACK_FOREST_LABS = "black_forest_labs"
    COMFYUI = "comfyui"
    MODAL = "modal"
    RUNPOD = "runpod"
    INTERNAL = "internal"


class ModelRegistry(ContractBaseModel):
    schema_version: ModelRegistrySchemaVersion = ModelRegistrySchemaVersion.V1
    id: UUID
    model_family: ModelFamily
    model_role: ModelRole
    provider: ModelProvider
    version_name: str = Field(min_length=2, max_length=80)
    display_name: str = Field(min_length=3, max_length=120)
    storage_path: str | None = Field(default=None, min_length=3, max_length=255)
    parent_model_id: UUID | None = None
    compatibility_notes: str | None = Field(default=None, min_length=8, max_length=280)
    is_active: bool = True
    metadata_json: JsonObject = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    deprecated_at: datetime | None = None

    @model_validator(mode="after")
    def validate_consistency(self) -> "ModelRegistry":
        if not is_utc_datetime(self.created_at):
            raise ValueError("created_at must be a UTC datetime")
        if not is_utc_datetime(self.updated_at):
            raise ValueError("updated_at must be a UTC datetime")
        if self.deprecated_at is not None and not is_utc_datetime(self.deprecated_at):
            raise ValueError("deprecated_at must be a UTC datetime")
        if self.created_at > self.updated_at:
            raise ValueError("created_at cannot be later than updated_at")
        if self.deprecated_at is not None and self.deprecated_at < self.created_at:
            raise ValueError("deprecated_at cannot be earlier than created_at")
        if self.model_role == ModelRole.LORA:
            if self.parent_model_id is None:
                raise ValueError("lora models require parent_model_id")
            if self.storage_path is None:
                raise ValueError("lora models require storage_path")
        if self.model_role == ModelRole.BASE_MODEL and self.parent_model_id is not None:
            raise ValueError("base_model cannot define parent_model_id")
        if self.model_role == ModelRole.VIDEO_PLACEHOLDER and self.storage_path is not None:
            raise ValueError("video_placeholder should not define storage_path yet")
        return self
