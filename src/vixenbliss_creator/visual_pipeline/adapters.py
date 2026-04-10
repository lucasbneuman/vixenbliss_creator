from __future__ import annotations

import copy
import time
from dataclasses import dataclass, field
from typing import Callable
from urllib import parse

from vixenbliss_creator.runtime_http import json_get, json_post
from vixenbliss_creator.provider import Provider
from vixenbliss_creator.runtime_providers.adapters import BeamRuntimeProviderClient, ModalRuntimeProviderClient
from vixenbliss_creator.runtime_providers.config import RuntimeProviderSettings
from vixenbliss_creator.runtime_providers.models import JobStatus, ServiceRuntime

from .config import VisualPipelineSettings
from .models import (
    ErrorCode,
    ModelFamily,
    ResumeCheckpoint,
    ResumeStage,
    StepExecutionResult,
    RuntimeStage,
    VisualArtifact,
    VisualArtifactRole,
    VisualGenerationRequest,
)


class VisualPipelineError(RuntimeError):
    def __init__(self, code: ErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code


_json_post = json_post
_json_get = json_get


def build_visual_execution_client(settings: VisualPipelineSettings):
    if settings.visual_execution_provider == Provider.ROUTED:
        return RoutedVisualExecutionClient(settings)
    if settings.visual_execution_provider == Provider.BEAM:
        return BeamExecutionClient(settings)
    if settings.visual_execution_provider == Provider.MODAL:
        return ModalExecutionClient(settings)
    if settings.visual_execution_provider == Provider.RUNPOD:
        raise RuntimeError("runpod is no longer an active visual execution provider; migrate to beam or modal")
    return ComfyUIHTTPExecutionClient(settings)


def _raise_pipeline_error(payload: dict) -> None:
    code = payload.get("error_code")
    message = payload.get("error_message")
    if code and message:
        raise VisualPipelineError(ErrorCode(code), str(message))


@dataclass
class ComfyUIHTTPExecutionClient:
    settings: VisualPipelineSettings

    def render_base_image(self, request: VisualGenerationRequest) -> StepExecutionResult:
        if request.ip_adapter.enabled and request.reference_face_image_url and request.reference_face_image_url.startswith("missing://"):
            raise VisualPipelineError(ErrorCode.REFERENCE_IMAGE_NOT_FOUND, "reference image could not be resolved")
        payload = self._submit(request=request, mode="base_render", checkpoint=None)
        return self._parse_step_result(payload, expected_stage=ResumeStage.BASE_RENDER)

    def run_face_detail(
        self,
        request: VisualGenerationRequest,
        checkpoint: ResumeCheckpoint,
    ) -> StepExecutionResult:
        payload = self._submit(request=request, mode="face_detail", checkpoint=checkpoint)
        return self._parse_step_result(payload, expected_stage=ResumeStage.FACE_DETAIL)

    def _submit(
        self,
        *,
        request: VisualGenerationRequest,
        mode: str,
        checkpoint: ResumeCheckpoint | None,
    ) -> dict:
        if not self.settings.comfyui_base_url:
            raise RuntimeError("COMFYUI_BASE_URL is required for visual execution")

        url = parse.urljoin(self.settings.comfyui_base_url.rstrip("/") + "/", "prompt")
        workflow_payload = self._build_workflow_payload(request=request, mode=mode, checkpoint=checkpoint)
        response_payload = _json_post(
            url,
            {
                "client_id": "vixenbliss_creator",
                "prompt": workflow_payload,
                "extra_data": {
                    "workflow_id": request.workflow_id,
                    "workflow_version": request.workflow_version,
                    "base_model_id": request.base_model_id,
                    "mode": mode,
                },
            },
            timeout_seconds=self.settings.comfyui_http_timeout_seconds,
        )

        if "outputs" in response_payload:
            return response_payload
        prompt_id = response_payload.get("prompt_id")
        if not prompt_id:
            raise RuntimeError("ComfyUI did not return outputs or prompt_id")
        history_url = parse.urljoin(self.settings.comfyui_base_url.rstrip("/") + "/", f"history/{prompt_id}")
        history_payload = _json_get(history_url, timeout_seconds=self.settings.comfyui_http_timeout_seconds)
        return history_payload.get(prompt_id, history_payload)

    def _build_workflow_payload(
        self,
        *,
        request: VisualGenerationRequest,
        mode: str,
        checkpoint: ResumeCheckpoint | None,
    ) -> dict:
        workflow = copy.deepcopy(request.workflow_json or {})
        workflow.setdefault("vb_meta", {})
        workflow["vb_meta"].update(
            {
                "workflow_id": request.workflow_id,
                "workflow_version": request.workflow_version,
                "base_model_id": request.base_model_id,
                "prompt": request.prompt,
                "negative_prompt": request.negative_prompt,
                "seed": request.seed,
                "width": request.width,
                "height": request.height,
                "mode": mode,
                "provider": request.provider,
            }
        )
        if request.ip_adapter.enabled:
            workflow["vb_meta"]["ip_adapter"] = {
                "reference_face_image_url": request.reference_face_image_url,
                "model_name": request.ip_adapter.model_name,
                "weight": request.ip_adapter.weight,
            }
            node_id = request.ip_adapter.node_id or self.settings.comfyui_ip_adapter_node_id
            if node_id:
                self._update_node_inputs(
                    workflow,
                    node_id,
                    {
                        "image": request.reference_face_image_url,
                        "weight": request.ip_adapter.weight,
                        "ipadapter_file": request.ip_adapter.model_name,
                    },
                )
        if request.face_detailer.enabled:
            workflow["vb_meta"]["face_detailer"] = {
                "confidence_threshold": request.face_detailer.confidence_threshold,
                "inpaint_strength": request.face_detailer.inpaint_strength,
            }
            detector_node_id = request.face_detailer.bbox_detector_node_id or self.settings.comfyui_face_detector_node_id
            if detector_node_id:
                self._update_node_inputs(
                    workflow,
                    detector_node_id,
                    {"confidence_threshold": request.face_detailer.confidence_threshold},
                )
        if mode == "face_detail":
            workflow["vb_meta"]["resume_checkpoint"] = checkpoint.model_dump(mode="json") if checkpoint else None
            face_detailer_node_id = (
                request.face_detailer.face_detailer_node_id or self.settings.comfyui_face_detailer_node_id
            )
            if face_detailer_node_id and checkpoint:
                base_image_uri = next(
                    (artifact.uri for artifact in checkpoint.intermediate_artifacts if artifact.role == VisualArtifactRole.BASE_IMAGE),
                    None,
                )
                self._update_node_inputs(
                    workflow,
                    face_detailer_node_id,
                    {"image": base_image_uri, "inpaint_strength": request.face_detailer.inpaint_strength},
                )
        return workflow

    @staticmethod
    def _update_node_inputs(workflow: dict, node_id: str, updates: dict[str, object]) -> None:
        node = workflow.get(node_id)
        if not isinstance(node, dict):
            return
        inputs = node.setdefault("inputs", {})
        if isinstance(inputs, dict):
            inputs.update(updates)

    def _parse_step_result(self, payload: dict, *, expected_stage: ResumeStage) -> StepExecutionResult:
        _raise_pipeline_error(payload)
        face_detection_confidence = self._extract_face_confidence(payload)
        artifacts = self._extract_artifacts(payload, stage=expected_stage)
        provider_job_id = payload.get("provider_job_id") or payload.get("prompt_id") or payload.get("id")
        successful_node_ids = payload.get("successful_node_ids") or list(payload.get("outputs", {}).keys())
        return StepExecutionResult(
            stage=expected_stage,
            artifacts=artifacts,
            provider=Provider(payload.get("provider", Provider.COMFYUI.value)),
            provider_job_id=provider_job_id,
            successful_node_ids=successful_node_ids,
            face_detection_confidence=face_detection_confidence,
            metadata_json=payload.get("metadata", {}),
        )

    def _extract_face_confidence(self, payload: dict) -> float | None:
        if "face_detection_confidence" in payload:
            return payload["face_detection_confidence"]
        metadata = payload.get("metadata", {})
        if isinstance(metadata, dict):
            if "face_detection_confidence" in metadata:
                return metadata["face_detection_confidence"]
            metrics = metadata.get("metrics", {})
            if isinstance(metrics, dict) and "face_detection_confidence" in metrics:
                return metrics["face_detection_confidence"]
        return None

    def _extract_artifacts(self, payload: dict, *, stage: ResumeStage) -> list[VisualArtifact]:
        if "artifacts" in payload:
            return [VisualArtifact.model_validate(item) for item in payload["artifacts"]]

        outputs = payload.get("outputs", {})
        artifacts: list[VisualArtifact] = []
        for output in outputs.values():
            if not isinstance(output, dict):
                continue
            for image in output.get("images", []):
                filename = image.get("filename")
                if not filename:
                    continue
                query = parse.urlencode(
                    {
                        "filename": filename,
                        "subfolder": image.get("subfolder", ""),
                        "type": image.get("type", "output"),
                    }
                )
                uri = parse.urljoin(self.settings.comfyui_base_url.rstrip("/") + "/", "view") + "?" + query
                role = VisualArtifactRole.FINAL_IMAGE if stage == ResumeStage.FACE_DETAIL else VisualArtifactRole.BASE_IMAGE
                artifacts.append(
                    VisualArtifact(
                        role=role,
                        uri=uri,
                        content_type="image/png",
                        metadata_json={"filename": filename},
                    )
                )
        if artifacts:
            return artifacts
        raise RuntimeError("ComfyUI execution did not expose any artifacts")


ComfyUIExecutionHTTPClient = ComfyUIHTTPExecutionClient


@dataclass
class RoutedVisualExecutionClient:
    settings: VisualPipelineSettings

    def render_base_image(self, request: VisualGenerationRequest) -> StepExecutionResult:
        return self._client_for(request).render_base_image(request)

    def run_face_detail(
        self,
        request: VisualGenerationRequest,
        checkpoint: ResumeCheckpoint,
    ) -> StepExecutionResult:
        return self._client_for(request).run_face_detail(request, checkpoint)

    def _client_for(self, request: VisualGenerationRequest):
        provider = self.settings.provider_for_stage(request.runtime_stage.value)
        if provider == Provider.BEAM:
            return BeamExecutionClient(self.settings)
        if provider == Provider.MODAL:
            return ModalExecutionClient(self.settings)
        if provider == Provider.RUNPOD:
            raise RuntimeError("runpod is no longer an active routed provider")
        return ComfyUIHTTPExecutionClient(self.settings)


@dataclass
class ProviderRuntimeExecutionClient:
    settings: VisualPipelineSettings
    provider_settings: RuntimeProviderSettings
    provider_client: BeamRuntimeProviderClient | ModalRuntimeProviderClient

    def render_base_image(self, request: VisualGenerationRequest) -> StepExecutionResult:
        payload = self._submit(request=request, mode=ResumeStage.BASE_RENDER, checkpoint=None)
        return self._parse_step_result(payload, expected_stage=ResumeStage.BASE_RENDER)

    def run_face_detail(
        self,
        request: VisualGenerationRequest,
        checkpoint: ResumeCheckpoint,
    ) -> StepExecutionResult:
        payload = self._submit(request=request, mode=ResumeStage.FACE_DETAIL, checkpoint=checkpoint)
        return self._parse_step_result(payload, expected_stage=ResumeStage.FACE_DETAIL)

    def _submit(
        self,
        *,
        request: VisualGenerationRequest,
        mode: ResumeStage,
        checkpoint: ResumeCheckpoint | None,
    ) -> dict:
        service_runtime = self._resolve_service_runtime(request)
        handle = self.provider_client.submit_job(
            service_runtime,
            self._build_job_input(request=request, mode=mode, checkpoint=checkpoint),
        )
        if handle.status == JobStatus.COMPLETED:
            return self.provider_client.fetch_result(handle)
        return self.provider_client.fetch_result(handle)

    def _build_job_input(
        self,
        *,
        request: VisualGenerationRequest,
        mode: ResumeStage,
        checkpoint: ResumeCheckpoint | None,
    ) -> dict:
        return {
            "action": "generate",
            "mode": mode.value,
            "workflow_id": request.workflow_id,
            "workflow_version": request.workflow_version,
            "base_model_id": request.base_model_id,
            "model_family": request.model_family,
            "runtime_stage": request.runtime_stage,
            "prompt": request.prompt,
            "negative_prompt": request.negative_prompt,
            "seed": request.seed,
            "width": request.width,
            "height": request.height,
            "reference_face_image_url": request.reference_face_image_url,
            "face_confidence_threshold": request.face_detailer.confidence_threshold,
            "inpaint_strength": request.face_detailer.inpaint_strength,
            "ip_adapter": request.ip_adapter.model_dump(mode="json"),
            "face_detailer": request.face_detailer.model_dump(mode="json"),
            "lora_version": request.lora_version,
            "lora_validated": request.lora_validated,
            "resume_checkpoint": checkpoint.model_dump(mode="json") if checkpoint is not None else None,
            "metadata": request.metadata_json,
        }

    def _parse_step_result(self, payload: dict, *, expected_stage: ResumeStage) -> StepExecutionResult:
        _raise_pipeline_error(payload)
        artifacts = [VisualArtifact.model_validate(item) for item in payload.get("artifacts", [])]
        if not artifacts:
            raise RuntimeError(f"{self.provider_client.provider.value} execution did not expose any artifacts")
        return StepExecutionResult(
            stage=expected_stage,
            artifacts=artifacts,
            provider=self.provider_client.provider,
            provider_job_id=payload.get("provider_job_id") or payload.get("job_id") or payload.get("id"),
            successful_node_ids=payload.get("successful_node_ids", []),
            face_detection_confidence=payload.get("face_detection_confidence"),
            metadata_json={
                **payload.get("metadata", {}),
                "model_family": payload.get("model_family", ModelFamily.FLUX.value),
                "service_runtime": payload.get("service_runtime") or self._infer_service_runtime_from_payload(payload),
            },
        )

    @staticmethod
    def _infer_service_runtime_from_payload(payload: dict) -> str:
        runtime_stage = payload.get("runtime_stage")
        if runtime_stage == RuntimeStage.IDENTITY_IMAGE.value:
            return ServiceRuntime.S1_IMAGE.value
        if runtime_stage == RuntimeStage.VIDEO.value:
            return ServiceRuntime.S2_VIDEO.value
        return ServiceRuntime.S2_IMAGE.value

    @staticmethod
    def _resolve_service_runtime(request: VisualGenerationRequest) -> ServiceRuntime:
        if request.runtime_stage == RuntimeStage.IDENTITY_IMAGE:
            return ServiceRuntime.S1_IMAGE
        if request.runtime_stage == RuntimeStage.VIDEO:
            return ServiceRuntime.S2_VIDEO
        return ServiceRuntime.S2_IMAGE


class BeamExecutionClient(ProviderRuntimeExecutionClient):
    def __init__(self, settings: VisualPipelineSettings) -> None:
        provider_settings = settings.runtime_provider_settings
        super().__init__(
            settings=settings,
            provider_settings=provider_settings,
            provider_client=BeamRuntimeProviderClient(provider_settings),
        )


class ModalExecutionClient(ProviderRuntimeExecutionClient):
    def __init__(self, settings: VisualPipelineSettings) -> None:
        provider_settings = settings.runtime_provider_settings
        super().__init__(
            settings=settings,
            provider_settings=provider_settings,
            provider_client=ModalRuntimeProviderClient(provider_settings),
        )


@dataclass
class RunpodServerlessExecutionClient:
    settings: VisualPipelineSettings

    def render_base_image(self, request: VisualGenerationRequest) -> StepExecutionResult:
        payload = self._submit(request=request, mode=ResumeStage.BASE_RENDER, checkpoint=None)
        return self._parse_step_result(payload, expected_stage=ResumeStage.BASE_RENDER)

    def run_face_detail(
        self,
        request: VisualGenerationRequest,
        checkpoint: ResumeCheckpoint,
    ) -> StepExecutionResult:
        payload = self._submit(request=request, mode=ResumeStage.FACE_DETAIL, checkpoint=checkpoint)
        return self._parse_step_result(payload, expected_stage=ResumeStage.FACE_DETAIL)

    def _submit(
        self,
        *,
        request: VisualGenerationRequest,
        mode: ResumeStage,
        checkpoint: ResumeCheckpoint | None,
    ) -> dict:
        endpoint = self._resolve_endpoint(request).rstrip("/")
        if not endpoint:
            raise RuntimeError("a stage-specific Runpod endpoint is required for visual execution")
        if not self.settings.runpod_api_key:
            raise RuntimeError("RUNPOD_API_KEY is required for Runpod visual execution")

        headers = {"Authorization": f"Bearer {self.settings.runpod_api_key}"}
        job_input = self._build_job_input(request=request, mode=mode, checkpoint=checkpoint)
        route = "runsync" if self.settings.runpod_use_runsync else "run"
        payload = _json_post(
            f"{endpoint}/{route}",
            {"input": job_input},
            timeout_seconds=self.settings.comfyui_http_timeout_seconds,
            headers=headers,
        )
        if self.settings.runpod_use_runsync:
            return self._extract_sync_output(payload)

        job_id = payload.get("id")
        if not job_id:
            raise RuntimeError(f"Runpod did not return a job id: {payload}")
        return self._poll_job(job_id, endpoint=endpoint, headers=headers)

    def _resolve_endpoint(self, request: VisualGenerationRequest) -> str:
        if request.runtime_stage == RuntimeStage.IDENTITY_IMAGE:
            return self.settings.runpod_endpoint_image_identity or self.settings.runpod_endpoint_image_gen or ""
        if request.runtime_stage == RuntimeStage.CONTENT_IMAGE:
            return self.settings.runpod_endpoint_image_content or self.settings.runpod_endpoint_image_gen or ""
        if request.runtime_stage == RuntimeStage.VIDEO:
            return self.settings.runpod_endpoint_video_gen or ""
        return self.settings.runpod_endpoint_image_gen or ""

    def _build_job_input(
        self,
        *,
        request: VisualGenerationRequest,
        mode: ResumeStage,
        checkpoint: ResumeCheckpoint | None,
    ) -> dict:
        job_input = {
            "action": "generate",
            "mode": mode.value,
            "workflow_id": request.workflow_id,
            "workflow_version": request.workflow_version,
            "base_model_id": request.base_model_id,
            "model_family": request.model_family,
            "runtime_stage": request.runtime_stage,
            "prompt": request.prompt,
            "negative_prompt": request.negative_prompt,
            "seed": request.seed,
            "width": request.width,
            "height": request.height,
            "reference_face_image_url": request.reference_face_image_url,
            "face_confidence_threshold": request.face_detailer.confidence_threshold,
            "inpaint_strength": request.face_detailer.inpaint_strength,
            "ip_adapter": request.ip_adapter.model_dump(mode="json"),
            "face_detailer": request.face_detailer.model_dump(mode="json"),
            "lora_version": request.lora_version,
            "lora_validated": request.lora_validated,
            "metadata": request.metadata_json,
        }
        base_checkpoint_name = request.metadata_json.get("base_checkpoint_name")
        if isinstance(base_checkpoint_name, str) and base_checkpoint_name:
            job_input["base_checkpoint_name"] = base_checkpoint_name
        if checkpoint is not None:
            job_input["resume_checkpoint"] = checkpoint.model_dump(mode="json")
        return job_input

    def _extract_sync_output(self, payload: dict) -> dict:
        output = payload.get("output")
        if isinstance(output, dict):
            return output
        raise RuntimeError(f"Runpod runsync response did not include output: {payload}")

    def _poll_job(self, job_id: str, *, endpoint: str, headers: dict[str, str]) -> dict:
        deadline = time.time() + self.settings.runpod_job_timeout_seconds
        status_url = f"{endpoint}/status/{job_id}"
        while time.time() < deadline:
            payload = _json_get(status_url, timeout_seconds=self.settings.comfyui_http_timeout_seconds, headers=headers)
            status = payload.get("status")
            if status == "COMPLETED":
                output = payload.get("output")
                if isinstance(output, dict):
                    output.setdefault("provider_job_id", job_id)
                    return output
                raise RuntimeError(f"Runpod completed job without structured output: {payload}")
            if status in {"FAILED", "CANCELLED", "TIMED_OUT"}:
                error_detail = payload.get("error") or payload.get("output") or payload
                raise RuntimeError(f"Runpod job {job_id} failed with status {status}: {error_detail}")
            time.sleep(self.settings.runpod_poll_interval_seconds)
        raise RuntimeError(f"Runpod job {job_id} did not complete within {self.settings.runpod_job_timeout_seconds} seconds")

    def _parse_step_result(self, payload: dict, *, expected_stage: ResumeStage) -> StepExecutionResult:
        _raise_pipeline_error(payload)
        artifacts = [VisualArtifact.model_validate(item) for item in payload.get("artifacts", [])]
        if not artifacts:
            raise RuntimeError("Runpod execution did not expose any artifacts")
        return StepExecutionResult(
            stage=expected_stage,
            artifacts=artifacts,
            provider=Provider.RUNPOD,
            provider_job_id=payload.get("provider_job_id") or payload.get("prompt_id"),
            successful_node_ids=payload.get("successful_node_ids", []),
            face_detection_confidence=payload.get("face_detection_confidence"),
            metadata_json={
                **payload.get("metadata", {}),
                "model_family": payload.get("model_family", ModelFamily.FLUX.value),
            },
        )


@dataclass
class FakeVisualExecutionClient:
    base_result: StepExecutionResult | None = None
    face_detail_result: StepExecutionResult | None = None
    factory: Callable[[str, VisualGenerationRequest, ResumeCheckpoint | None], StepExecutionResult | dict] | None = None
    calls: list[str] = field(default_factory=list)

    def render_base_image(self, request: VisualGenerationRequest) -> StepExecutionResult:
        self.calls.append("base_render")
        return self._resolve("base_render", request, None, self.base_result)

    def run_face_detail(
        self,
        request: VisualGenerationRequest,
        checkpoint: ResumeCheckpoint,
    ) -> StepExecutionResult:
        self.calls.append("face_detail")
        return self._resolve("face_detail", request, checkpoint, self.face_detail_result)

    def _resolve(
        self,
        mode: str,
        request: VisualGenerationRequest,
        checkpoint: ResumeCheckpoint | None,
        fallback: StepExecutionResult | None,
    ) -> StepExecutionResult:
        if self.factory is not None:
            payload = self.factory(mode, request, checkpoint)
            return StepExecutionResult.model_validate(payload)
        if fallback is None:
            raise RuntimeError(f"FakeVisualExecutionClient missing result for {mode}")
        return fallback
