from __future__ import annotations

from dataclasses import dataclass

from pydantic import Field

from vixenbliss_creator.contracts.common import ContractBaseModel

from .models import CopilotRecommendation, CopilotStage


class ApprovedWorkflow(ContractBaseModel):
    stage: CopilotStage
    workflow_id: str = Field(min_length=3, max_length=120)
    workflow_version: str = Field(min_length=2, max_length=40)
    workflow_family: str = Field(min_length=3, max_length=80)
    base_model_id: str = Field(min_length=3, max_length=120)
    required_nodes: list[str] = Field(min_length=1, max_length=24)
    optional_nodes: list[str] = Field(default_factory=list, max_length=24)
    model_hints: list[str] = Field(default_factory=list, max_length=12)
    input_contract: list[str] = Field(default_factory=list, max_length=16)
    content_modes_supported: list[str] = Field(min_length=1, max_length=3)
    risk_flags: list[str] = Field(default_factory=list, max_length=12)
    compatibility_notes: list[str] = Field(default_factory=list, max_length=12)


def _approved_workflows() -> tuple[ApprovedWorkflow, ...]:
    return (
        ApprovedWorkflow(
            stage=CopilotStage.S1_IDENTITY_IMAGE,
            workflow_id="base-image-ipadapter-impact",
            workflow_version="2026-03-31",
            workflow_family="flux_identity_reference",
            base_model_id="flux-schnell-v1",
            required_nodes=["load_model", "ip_adapter_plus", "ksampler", "vae_decode"],
            optional_nodes=["face_detector", "face_detailer"],
            model_hints=["flux", "ipadapter-face", "impact-pack"],
            input_contract=["identity_metadata", "prompt_template", "reference_face_image_url"],
            content_modes_supported=["sfw", "sensual", "nsfw"],
            risk_flags=["identity_drift", "face_confidence_low"],
            compatibility_notes=[
                "Approved for System 1 identity generation.",
                "Consumes reference face image when IP Adapter is enabled.",
            ],
        ),
        ApprovedWorkflow(
            stage=CopilotStage.S2_CONTENT_IMAGE,
            workflow_id="content-image-flux-lora",
            workflow_version="2026-04-08",
            workflow_family="flux_content_lora",
            base_model_id="flux-schnell-v1",
            required_nodes=["load_model", "load_lora", "ksampler", "vae_decode"],
            optional_nodes=["ip_adapter_plus", "regional_inpaint"],
            model_hints=["flux", "validated-lora", "content-stage"],
            input_contract=["identity_metadata", "prompt_template", "lora_version"],
            content_modes_supported=["sfw", "sensual", "nsfw"],
            risk_flags=["lora_mismatch", "prompt_overfit"],
            compatibility_notes=[
                "Must stay in the Flux family to preserve S1/S2 compatibility.",
                "LoRA use requires validated content-image runtime inputs.",
            ],
        ),
        ApprovedWorkflow(
            stage=CopilotStage.S2_VIDEO,
            workflow_id="video-image-to-video-prep",
            workflow_version="2026-04-08",
            workflow_family="flux_video_prep",
            base_model_id="flux-schnell-v1",
            required_nodes=["load_model", "frame_conditioning", "video_sampler"],
            optional_nodes=["ip_adapter_plus", "temporal_consistency"],
            model_hints=["flux", "image-to-video", "temporal-consistency"],
            input_contract=["identity_metadata", "prompt_template", "source_image_or_clip"],
            content_modes_supported=["sfw", "sensual", "nsfw"],
            risk_flags=["temporal_drift", "runtime_unstable"],
            compatibility_notes=[
                "Stage prepared for video planning only; not a production render dependency.",
                "Adoption should wait for a stabilized text-to-video or image-to-video contract.",
            ],
        ),
    )


@dataclass(frozen=True)
class WorkflowRegistry:
    entries: tuple[ApprovedWorkflow, ...]

    @classmethod
    def default(cls) -> "WorkflowRegistry":
        return cls(entries=_approved_workflows())

    def for_stage(self, stage: CopilotStage) -> list[ApprovedWorkflow]:
        return [entry for entry in self.entries if entry.stage == stage]

    def get(self, workflow_id: str) -> ApprovedWorkflow | None:
        for entry in self.entries:
            if entry.workflow_id == workflow_id:
                return entry
        return None

    def build_fallback_recommendation(self, stage: CopilotStage) -> CopilotRecommendation:
        entry = self.for_stage(stage)[0]
        return CopilotRecommendation.model_validate(
            {
                "stage": entry.stage,
                "workflow_id": entry.workflow_id,
                "workflow_version": entry.workflow_version,
                "recommended_workflow_family": entry.workflow_family,
                "base_model_id": entry.base_model_id,
                "required_nodes": entry.required_nodes,
                "optional_nodes": entry.optional_nodes,
                "model_hints": entry.model_hints,
                "prompt_template": "Approved internal workflow fallback selected for controlled ComfyUI evolution.",
                "negative_prompt": "low quality, anatomy drift, incompatible nodes, unsafe content",
                "reasoning_summary": "Fallback recommendation selected from the internal approved workflow registry.",
                "risk_flags": entry.risk_flags,
                "compatibility_notes": entry.compatibility_notes,
                "content_modes_supported": entry.content_modes_supported,
                "registry_source": "approved_internal_fallback",
            }
        )
