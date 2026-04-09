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


class DatasetShot(ContractBaseModel):
    shot_index: int = Field(ge=1, le=200)
    sample_id: str = Field(min_length=8, max_length=120)
    class_name: Literal["SFW", "NSFW"]
    wardrobe_state: Literal["clothed", "nude"]
    framing: Literal["close_up_face", "medium", "full_body"]
    shot_type: Literal["close_up_face", "medium", "full_body"]
    camera_angle: Literal["front", "left_three_quarter", "right_three_quarter", "left_profile", "right_profile"]
    pose_family: str = Field(min_length=3, max_length=120)
    expression: str = Field(min_length=3, max_length=120)
    prompt: str = Field(min_length=12, max_length=2400)
    negative_prompt: str = Field(min_length=12, max_length=1600)
    caption: str = Field(min_length=8, max_length=1200)
    seed: int = Field(ge=0, le=2**31 - 1)
    realism_profile: str = Field(default="photorealistic_adult_reference_v1", min_length=3, max_length=120)
    source_strategy: str = Field(default="avatar_prompt_plus_shot_plan_v1", min_length=3, max_length=120)

    @model_validator(mode="after")
    def validate_class_mapping(self) -> "DatasetShot":
        if self.wardrobe_state == "clothed" and self.class_name != "SFW":
            raise ValueError("clothed shots must map to SFW")
        if self.wardrobe_state == "nude" and self.class_name != "NSFW":
            raise ValueError("nude shots must map to NSFW")
        if self.shot_type != self.framing:
            raise ValueError("shot_type must mirror framing for dataset shots")
        return self


class GenerationManifest(ContractBaseModel):
    schema_version: str = "1.1.0"
    identity_id: UUID
    prompt: str = Field(min_length=8, max_length=1200)
    negative_prompt: str = Field(min_length=3, max_length=1200)
    seed_bundle: SeedBundle
    samples_target: int = Field(default=40, ge=8, le=50)
    workflow_id: str = Field(min_length=2, max_length=120)
    workflow_version: str = Field(min_length=1, max_length=64)
    workflow_family: str = Field(default="flux_identity_reference", min_length=3, max_length=120)
    workflow_registry_source: str = Field(default="approved_internal", min_length=3, max_length=120)
    base_model_id: str = Field(min_length=3, max_length=120)
    model_family: Literal["flux"] = "flux"
    realism_profile: str = Field(default="photorealistic_adult_reference_v1", min_length=3, max_length=120)
    source_strategy: str = Field(default="avatar_prompt_plus_shot_plan_v1", min_length=3, max_length=120)
    dataset_shot_plan: list[DatasetShot] = Field(default_factory=list, max_length=50)
    comfy_parameters: JsonObject = Field(default_factory=dict)
    artifact_path: str = Field(min_length=3, max_length=255)
    created_at: datetime = Field(default_factory=utc_now)


class GenerationServiceInput(ContractBaseModel):
    identity_id: UUID
    identity_context: JsonObject = Field(default_factory=dict)
    workflow_id: str = Field(min_length=2, max_length=120)
    workflow_version: str = Field(min_length=1, max_length=64)
    workflow_family: str = Field(default="flux_identity_reference", min_length=3, max_length=120)
    workflow_registry_source: str = Field(default="approved_internal", min_length=3, max_length=120)
    base_model_id: str = Field(min_length=3, max_length=120)
    reference_face_image_url: str | None = Field(default=None, min_length=8, max_length=500)
    image_width: int = Field(default=1024, ge=256, le=2048)
    image_height: int = Field(default=1024, ge=256, le=2048)
    samples_target: int = Field(default=40, ge=8, le=50)
    realism_profile: str = Field(default="photorealistic_adult_reference_v1", min_length=3, max_length=120)
    source_strategy: str = Field(default="avatar_prompt_plus_shot_plan_v1", min_length=3, max_length=120)
    copilot_prompt_template: str | None = Field(default=None, min_length=8, max_length=600)
    copilot_negative_prompt: str | None = Field(default=None, min_length=8, max_length=400)
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
    samples_target: int = Field(default=40, ge=8, le=50)
    dataset_shot_plan: list[DatasetShot] = Field(default_factory=list, max_length=50)
    face_detection_confidence: float | None = Field(default=0.91, ge=0.0, le=1.0)
    artifact_root: str = Field(default="identities", min_length=3, max_length=255)
    metadata_json: JsonObject = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_ip_adapter(self) -> "DatasetServiceInput":
        ip_adapter = self.generation_manifest.comfy_parameters.get("ip_adapter", {})
        if ip_adapter.get("enabled", False) and not self.reference_face_image_url:
            raise ValueError("reference_face_image_url is required when ip_adapter is enabled")
        shot_plan = self.dataset_shot_plan or self.generation_manifest.dataset_shot_plan
        if shot_plan and len(shot_plan) != self.samples_target:
            raise ValueError("dataset_shot_plan length must match samples_target")
        if self.samples_target % 2 != 0:
            raise ValueError("samples_target must be even to satisfy the 50/50 dataset balance policy")
        if shot_plan:
            sfw_count = sum(1 for shot in shot_plan if shot.class_name == "SFW")
            nsfw_count = sum(1 for shot in shot_plan if shot.class_name == "NSFW")
            if sfw_count != nsfw_count:
                raise ValueError("dataset_shot_plan must preserve a 50/50 balance between SFW and NSFW")
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
