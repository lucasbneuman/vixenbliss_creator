from __future__ import annotations

from dataclasses import dataclass

from .adapters import VisualPipelineError
from .models import (
    ErrorCode,
    ResumeCheckpoint,
    ResumePolicy,
    ResumeStage,
    StepExecutionResult,
    VisualArtifact,
    VisualArtifactRole,
    VisualGenerationRequest,
    VisualGenerationResult,
)
from .ports import VisualExecutionClient


@dataclass
class VisualGenerationOrchestrator:
    client: VisualExecutionClient

    def generate(self, request: VisualGenerationRequest) -> VisualGenerationResult:
        try:
            return self._generate(request)
        except VisualPipelineError as exc:
            return self._failure_result(request, exc.code, str(exc))
        except RuntimeError as exc:
            return self._failure_result(request, ErrorCode.COMFYUI_EXECUTION_FAILED, str(exc))

    def _generate(self, request: VisualGenerationRequest) -> VisualGenerationResult:
        if request.resume_policy == ResumePolicy.FROM_CHECKPOINT and request.resume_checkpoint is not None:
            if request.resume_checkpoint.stage in {ResumeStage.FACE_DETAIL, ResumeStage.COMPLETED}:
                return VisualGenerationResult(
                    provider=request.provider,
                    workflow_id=request.workflow_id,
                    workflow_version=request.workflow_version,
                    base_model_id=request.base_model_id,
                    seed=request.seed,
                    artifacts=request.resume_checkpoint.intermediate_artifacts,
                    intermediate_state=request.resume_checkpoint,
                    face_detection_confidence=request.resume_checkpoint.metadata_json.get("face_detection_confidence"),
                    ip_adapter_used=request.ip_adapter.enabled,
                    regional_inpaint_triggered=True,
                    metadata_json={"resumed_from_checkpoint": True},
                )
            base_step = StepExecutionResult(
                stage=request.resume_checkpoint.stage,
                artifacts=request.resume_checkpoint.intermediate_artifacts,
                provider=request.resume_checkpoint.provider,
                provider_job_id=request.resume_checkpoint.provider_job_id,
                successful_node_ids=request.resume_checkpoint.successful_node_ids,
                face_detection_confidence=request.resume_checkpoint.metadata_json.get("face_detection_confidence"),
                metadata_json=request.resume_checkpoint.metadata_json,
            )
        else:
            base_step = self.client.render_base_image(request)

        if base_step.face_detection_confidence is None:
            raise VisualPipelineError(
                ErrorCode.FACE_CONFIDENCE_UNAVAILABLE,
                "face detector did not return a usable confidence score",
            )

        threshold = request.face_detailer.confidence_threshold
        regional_inpaint_triggered = request.face_detailer.enabled and base_step.face_detection_confidence < threshold

        if not regional_inpaint_triggered:
            final_artifacts = [self._as_final_artifact(artifact) for artifact in base_step.artifacts]
            checkpoint = ResumeCheckpoint(
                workflow_id=request.workflow_id,
                workflow_version=request.workflow_version,
                base_model_id=request.base_model_id,
                seed=request.seed,
                stage=ResumeStage.COMPLETED,
                provider=request.provider,
                successful_node_ids=base_step.successful_node_ids,
                intermediate_artifacts=final_artifacts,
                metadata_json={"face_detection_confidence": base_step.face_detection_confidence},
            )
            return VisualGenerationResult(
                provider=request.provider,
                workflow_id=request.workflow_id,
                workflow_version=request.workflow_version,
                base_model_id=request.base_model_id,
                seed=request.seed,
                artifacts=final_artifacts,
                intermediate_state=checkpoint,
                face_detection_confidence=base_step.face_detection_confidence,
                ip_adapter_used=request.ip_adapter.enabled,
                regional_inpaint_triggered=False,
                metadata_json={"resumed_from_checkpoint": request.resume_policy == ResumePolicy.FROM_CHECKPOINT},
            )

        checkpoint = ResumeCheckpoint(
            workflow_id=request.workflow_id,
            workflow_version=request.workflow_version,
            base_model_id=request.base_model_id,
            seed=request.seed,
            stage=ResumeStage.BASE_RENDER,
            provider=request.provider,
            provider_job_id=base_step.provider_job_id,
            successful_node_ids=base_step.successful_node_ids,
            intermediate_artifacts=[self._as_base_artifact(artifact) for artifact in base_step.artifacts],
            metadata_json={"face_detection_confidence": base_step.face_detection_confidence},
        )
        face_detail_step = self.client.run_face_detail(request, checkpoint)
        completed_checkpoint = ResumeCheckpoint(
            workflow_id=request.workflow_id,
            workflow_version=request.workflow_version,
            base_model_id=request.base_model_id,
            seed=request.seed,
            stage=ResumeStage.COMPLETED,
            provider=request.provider,
            successful_node_ids=face_detail_step.successful_node_ids,
            intermediate_artifacts=[self._as_final_artifact(artifact) for artifact in face_detail_step.artifacts],
            metadata_json={"face_detection_confidence": base_step.face_detection_confidence},
        )
        return VisualGenerationResult(
            provider=request.provider,
            workflow_id=request.workflow_id,
            workflow_version=request.workflow_version,
            base_model_id=request.base_model_id,
            seed=request.seed,
            artifacts=completed_checkpoint.intermediate_artifacts,
            intermediate_state=completed_checkpoint,
            face_detection_confidence=base_step.face_detection_confidence,
            ip_adapter_used=request.ip_adapter.enabled,
            regional_inpaint_triggered=True,
            metadata_json={"resumed_from_checkpoint": request.resume_policy == ResumePolicy.FROM_CHECKPOINT},
        )

    def _failure_result(
        self,
        request: VisualGenerationRequest,
        code: ErrorCode,
        message: str,
    ) -> VisualGenerationResult:
        return VisualGenerationResult(
            provider=request.provider,
            workflow_id=request.workflow_id,
            workflow_version=request.workflow_version,
            base_model_id=request.base_model_id,
            seed=request.seed,
            error_code=code,
            error_message=message,
            metadata_json={},
        )

    @staticmethod
    def _as_base_artifact(artifact: VisualArtifact) -> VisualArtifact:
        if artifact.role == VisualArtifactRole.BASE_IMAGE:
            return artifact
        return artifact.model_copy(update={"role": VisualArtifactRole.BASE_IMAGE})

    @staticmethod
    def _as_final_artifact(artifact: VisualArtifact) -> VisualArtifact:
        if artifact.role == VisualArtifactRole.FINAL_IMAGE:
            return artifact
        return artifact.model_copy(update={"role": VisualArtifactRole.FINAL_IMAGE})
