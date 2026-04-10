from __future__ import annotations

from collections.abc import Sequence

from .identity import DatasetStatus, Identity, PipelineState
from .model_registry import ModelRegistry, ModelRole


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


def assert_base_model_registered(identity: Identity, registry_models: Sequence[ModelRegistry]) -> None:
    if not identity.base_model_id:
        raise ValueError("identity requires base_model_id before generation")
    for model in registry_models:
        if model.model_role != ModelRole.BASE_MODEL:
            continue
        if not model.is_active:
            continue
        if model.base_model_id == identity.base_model_id:
            return
    raise ValueError("identity requires a registered active base_model_id before generation")
