from __future__ import annotations

from enum import Enum

from pydantic import Field, model_validator

from vixenbliss_creator.contracts.common import ContractBaseModel, JsonObject
from vixenbliss_creator.provider import Provider


class RuntimeStage(str, Enum):
    IDENTITY_IMAGE = "identity_image"
    CONTENT_IMAGE = "content_image"
    VIDEO = "video"


class ModelFamily(str, Enum):
    FLUX = "flux"


class ResumePolicy(str, Enum):
    NEVER = "never"
    FROM_CHECKPOINT = "from_checkpoint"


class ResumeStage(str, Enum):
    BASE_RENDER = "base_render"
    FACE_DETAIL = "face_detail"
    COMPLETED = "completed"


class ErrorCode(str, Enum):
    REFERENCE_IMAGE_NOT_FOUND = "REFERENCE_IMAGE_NOT_FOUND"
    FACE_CONFIDENCE_UNAVAILABLE = "FACE_CONFIDENCE_UNAVAILABLE"
    RESUME_STATE_INCOMPLETE = "RESUME_STATE_INCOMPLETE"
    COMFYUI_EXECUTION_FAILED = "COMFYUI_EXECUTION_FAILED"


class VisualArtifactRole(str, Enum):
    BASE_IMAGE = "base_image"
    FINAL_IMAGE = "final_image"
    FACE_MASK = "face_mask"


class VisualArtifact(ContractBaseModel):
    role: VisualArtifactRole
    uri: str = Field(min_length=3, max_length=500)
    content_type: str = Field(min_length=3, max_length=120)
    metadata_json: JsonObject = Field(default_factory=dict)


class IpAdapterConfig(ContractBaseModel):
    enabled: bool = False
    model_name: str = Field(default="plus_face", min_length=3, max_length=120)
    weight: float = Field(default=1.0, ge=0.0, le=2.0)
    node_id: str | None = Field(default=None, min_length=1, max_length=120)


class FaceDetailerConfig(ContractBaseModel):
    enabled: bool = True
    bbox_detector_node_id: str | None = Field(default=None, min_length=1, max_length=120)
    face_detailer_node_id: str | None = Field(default=None, min_length=1, max_length=120)
    confidence_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    inpaint_strength: float = Field(default=0.35, ge=0.0, le=1.0)


class ResumeCheckpoint(ContractBaseModel):
    workflow_id: str = Field(min_length=3, max_length=120)
    workflow_version: str = Field(min_length=1, max_length=64)
    base_model_id: str = Field(min_length=3, max_length=120)
    seed: int = Field(ge=0, le=2**32 - 1)
    stage: ResumeStage
    provider: Provider = Provider.COMFYUI_HTTP
    provider_job_id: str | None = Field(default=None, min_length=1, max_length=120)
    successful_node_ids: list[str] = Field(default_factory=list, max_length=64)
    intermediate_artifacts: list[VisualArtifact] = Field(default_factory=list, max_length=12)
    metadata_json: JsonObject = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_completeness(self) -> "ResumeCheckpoint":
        roles = {artifact.role for artifact in self.intermediate_artifacts}
        if self.stage == ResumeStage.BASE_RENDER and VisualArtifactRole.BASE_IMAGE not in roles:
            raise ValueError("base_render checkpoints require a base_image artifact")
        if self.stage in {ResumeStage.FACE_DETAIL, ResumeStage.COMPLETED} and VisualArtifactRole.FINAL_IMAGE not in roles:
            raise ValueError("face_detail and completed checkpoints require a final_image artifact")
        if self.stage != ResumeStage.COMPLETED and not self.provider_job_id:
            raise ValueError("non-terminal checkpoints require provider_job_id")
        return self


class VisualGenerationRequest(ContractBaseModel):
    workflow_id: str = Field(min_length=3, max_length=120)
    workflow_version: str = Field(min_length=1, max_length=64)
    base_model_id: str = Field(min_length=3, max_length=120)
    model_family: ModelFamily = ModelFamily.FLUX
    runtime_stage: RuntimeStage = RuntimeStage.CONTENT_IMAGE
    prompt: str = Field(min_length=12, max_length=1200)
    negative_prompt: str = Field(min_length=12, max_length=1200)
    seed: int = Field(ge=0, le=2**32 - 1)
    width: int = Field(ge=256, le=4096)
    height: int = Field(ge=256, le=4096)
    provider: Provider = Provider.COMFYUI_HTTP
    workflow_json: JsonObject | None = None
    reference_face_image_url: str | None = Field(default=None, min_length=3, max_length=500)
    ip_adapter: IpAdapterConfig = Field(default_factory=IpAdapterConfig)
    face_detailer: FaceDetailerConfig = Field(default_factory=FaceDetailerConfig)
    resume_policy: ResumePolicy = ResumePolicy.NEVER
    resume_checkpoint: ResumeCheckpoint | None = None
    lora_version: str | None = Field(default=None, min_length=1, max_length=64)
    lora_validated: bool = False
    metadata_json: JsonObject = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_consistency(self) -> "VisualGenerationRequest":
        if self.ip_adapter.enabled and not self.reference_face_image_url:
            raise ValueError("reference_face_image_url is required when ip_adapter is enabled")
        if self.model_family != ModelFamily.FLUX:
            raise ValueError("only Flux model_family is supported for S1 and S2 image generation")
        if self.runtime_stage == RuntimeStage.IDENTITY_IMAGE and self.lora_version is not None:
            raise ValueError("identity_image runtime must not consume a LoRA version")
        if self.runtime_stage == RuntimeStage.CONTENT_IMAGE and self.lora_version is not None and not self.lora_validated:
            raise ValueError("content_image runtime requires explicit lora_validated=true when lora_version is provided")
        if self.resume_policy == ResumePolicy.FROM_CHECKPOINT and self.resume_checkpoint is None:
            raise ValueError("resume_checkpoint is required when resume_policy is from_checkpoint")
        if self.resume_checkpoint is not None:
            if self.resume_checkpoint.workflow_id != self.workflow_id:
                raise ValueError("resume_checkpoint.workflow_id must match workflow_id")
            if self.resume_checkpoint.workflow_version != self.workflow_version:
                raise ValueError("resume_checkpoint.workflow_version must match workflow_version")
            if self.resume_checkpoint.base_model_id != self.base_model_id:
                raise ValueError("resume_checkpoint.base_model_id must match base_model_id")
            if self.resume_checkpoint.seed != self.seed:
                raise ValueError("resume_checkpoint.seed must match seed")
        return self


class StepExecutionResult(ContractBaseModel):
    stage: ResumeStage
    artifacts: list[VisualArtifact] = Field(min_length=1, max_length=12)
    provider: Provider = Provider.COMFYUI_HTTP
    provider_job_id: str | None = Field(default=None, min_length=1, max_length=120)
    successful_node_ids: list[str] = Field(default_factory=list, max_length=64)
    face_detection_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    metadata_json: JsonObject = Field(default_factory=dict)


class VisualGenerationResult(ContractBaseModel):
    provider: Provider
    workflow_id: str = Field(min_length=3, max_length=120)
    workflow_version: str = Field(min_length=1, max_length=64)
    base_model_id: str = Field(min_length=3, max_length=120)
    model_family: ModelFamily = ModelFamily.FLUX
    runtime_stage: RuntimeStage = RuntimeStage.CONTENT_IMAGE
    seed: int = Field(ge=0, le=2**32 - 1)
    artifacts: list[VisualArtifact] = Field(default_factory=list, max_length=12)
    intermediate_state: ResumeCheckpoint | None = None
    face_detection_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    ip_adapter_used: bool = False
    regional_inpaint_triggered: bool = False
    error_code: ErrorCode | None = None
    error_message: str | None = Field(default=None, min_length=8, max_length=500)
    metadata_json: JsonObject = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_consistency(self) -> "VisualGenerationResult":
        has_error = self.error_code is not None or self.error_message is not None
        if has_error and (self.error_code is None or self.error_message is None):
            raise ValueError("error_code and error_message must be provided together")
        if has_error and self.artifacts:
            raise ValueError("failed results must not expose final artifacts")
        if not has_error and not self.artifacts:
            raise ValueError("successful results require at least one artifact")
        return self
