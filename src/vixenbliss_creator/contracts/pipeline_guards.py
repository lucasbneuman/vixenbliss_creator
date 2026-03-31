from __future__ import annotations

from .identity import DatasetStatus, Identity, PipelineState


def assert_lora_training_allowed(identity: Identity) -> None:
    if identity.dataset_status != DatasetStatus.READY:
        raise ValueError("lora training requires dataset_status=ready")
    if identity.pipeline_state not in {PipelineState.DATASET_READY, PipelineState.LORA_TRAINING_PENDING}:
        raise ValueError("lora training requires dataset_ready or lora_training_pending pipeline_state")


def assert_content_generation_allowed(identity: Identity) -> None:
    if identity.pipeline_state != PipelineState.LORA_VALIDATED:
        raise ValueError("content generation requires pipeline_state=lora_validated")
    if not identity.lora_version:
        raise ValueError("content generation requires a validated lora_version")
