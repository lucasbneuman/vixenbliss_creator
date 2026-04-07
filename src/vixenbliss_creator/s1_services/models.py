from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field, model_validator

from vixenbliss_creator.contracts.common import ContractBaseModel, JsonObject, utc_now


class SeedBundle(ContractBaseModel):
    portrait_seed: int = Field(ge=0, le=2**31 - 1)
    variation_seed: int = Field(ge=0, le=2**31 - 1)
    dataset_seed: int = Field(ge=0, le=2**31 - 1)


class GenerationManifest(ContractBaseModel):
    schema_version: str = "1.0.0"
    identity_id: UUID
    prompt: str = Field(min_length=8, max_length=1200)
    negative_prompt: str = Field(min_length=3, max_length=1200)
    seed_bundle: SeedBundle
    workflow_id: str = Field(min_length=2, max_length=120)
    workflow_version: str = Field(min_length=1, max_length=64)
    base_model_id: str = Field(min_length=3, max_length=120)
    model_family: Literal["flux"] = "flux"
    comfy_parameters: JsonObject = Field(default_factory=dict)
    artifact_path: str = Field(min_length=3, max_length=255)
    created_at: datetime = Field(default_factory=utc_now)


class GenerationServiceInput(ContractBaseModel):
    identity_id: UUID
    identity_context: JsonObject = Field(default_factory=dict)
    workflow_id: str = Field(min_length=2, max_length=120)
    workflow_version: str = Field(min_length=1, max_length=64)
    base_model_id: str = Field(min_length=3, max_length=120)
    reference_face_image_url: str | None = Field(default=None, min_length=8, max_length=500)
    image_width: int = Field(default=1024, ge=256, le=2048)
    image_height: int = Field(default=1024, ge=256, le=2048)
    prompt_hints: JsonObject = Field(default_factory=dict)
    negative_prompt_hints: JsonObject = Field(default_factory=dict)
    ip_adapter: JsonObject = Field(default_factory=lambda: {"enabled": True, "model_name": "plus_face", "weight": 0.9})
    seed_basis: str | None = Field(default=None, min_length=3, max_length=255)

    @model_validator(mode="after")
    def validate_context(self) -> "GenerationServiceInput":
        if not self.identity_context:
            raise ValueError("identity_context is required before generation manifest preparation")
        return self


class DatasetServiceInput(ContractBaseModel):
    identity_id: UUID
    generation_manifest: GenerationManifest
    reference_face_image_url: str | None = Field(default=None, min_length=8, max_length=500)
    samples_target: int = Field(default=24, ge=20, le=50)
    face_detection_confidence: float | None = Field(default=0.91, ge=0.0, le=1.0)
    artifact_root: str = Field(default="identities", min_length=3, max_length=255)
    metadata_json: JsonObject = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_ip_adapter(self) -> "DatasetServiceInput":
        ip_adapter = self.generation_manifest.comfy_parameters.get("ip_adapter", {})
        if ip_adapter.get("enabled", False) and not self.reference_face_image_url:
            raise ValueError("reference_face_image_url is required when ip_adapter is enabled")
        return self


class LoraTrainingServiceInput(ContractBaseModel):
    identity_id: UUID
    dataset_manifest: JsonObject | None = None
    dataset_package_path: str | None = Field(default=None, min_length=3, max_length=255)
    base_model_id: str = Field(min_length=3, max_length=120)
    model_family: Literal["flux"] = "flux"
    training_config: JsonObject = Field(default_factory=dict)
    artifact_root: str = Field(default="artifacts/s1-lora-train", min_length=3, max_length=255)

    @model_validator(mode="after")
    def validate_dataset_source(self) -> "LoraTrainingServiceInput":
        if self.dataset_manifest is None and self.dataset_package_path is None:
            raise ValueError("dataset_manifest or dataset_package_path is required for lora training")
        return self


class ProgressEvent(ContractBaseModel):
    job_id: str = Field(min_length=3, max_length=120)
    stage: str = Field(min_length=2, max_length=120)
    message: str = Field(min_length=3, max_length=280)
    progress: float = Field(ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=utc_now)
