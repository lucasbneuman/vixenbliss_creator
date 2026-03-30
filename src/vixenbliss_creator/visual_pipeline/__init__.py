"""Visual generation engine contracts and orchestration for ComfyUI workflows."""

from .adapters import ComfyUIExecutionHTTPClient, FakeVisualExecutionClient
from .config import VisualPipelineSettings
from .models import (
    ErrorCode,
    FaceDetailerConfig,
    IpAdapterConfig,
    Provider,
    ResumeCheckpoint,
    ResumePolicy,
    ResumeStage,
    VisualArtifact,
    VisualArtifactRole,
    VisualGenerationRequest,
    VisualGenerationResult,
)
from .service import VisualGenerationOrchestrator

__all__ = [
    "ComfyUIExecutionHTTPClient",
    "ErrorCode",
    "FaceDetailerConfig",
    "FakeVisualExecutionClient",
    "IpAdapterConfig",
    "Provider",
    "ResumeCheckpoint",
    "ResumePolicy",
    "ResumeStage",
    "VisualArtifact",
    "VisualArtifactRole",
    "VisualGenerationOrchestrator",
    "VisualGenerationRequest",
    "VisualGenerationResult",
    "VisualPipelineSettings",
]
