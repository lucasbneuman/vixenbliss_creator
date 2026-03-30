from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from typing import Callable
from urllib import error, parse, request

from .config import VisualPipelineSettings
from .models import (
    ErrorCode,
    ResumeCheckpoint,
    ResumeStage,
    StepExecutionResult,
    VisualArtifact,
    VisualArtifactRole,
    VisualGenerationRequest,
)


class VisualPipelineError(RuntimeError):
    def __init__(self, code: ErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code


def _json_post(url: str, payload: dict, timeout_seconds: int, headers: dict[str, str] | None = None) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url=url,
        data=body,
        headers={"Content-Type": "application/json", **(headers or {})},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP error calling {url}: {exc.code} {detail}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Network error calling {url}: {exc.reason}") from exc
    return json.loads(raw)


def _json_get(url: str, timeout_seconds: int) -> dict:
    req = request.Request(url=url, headers={"Content-Type": "application/json"}, method="GET")
    try:
        with request.urlopen(req, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP error calling {url}: {exc.code} {detail}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Network error calling {url}: {exc.reason}") from exc
    return json.loads(raw)


@dataclass
class ComfyUIExecutionHTTPClient:
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
        face_detection_confidence = self._extract_face_confidence(payload)
        artifacts = self._extract_artifacts(payload, stage=expected_stage)
        provider_job_id = payload.get("prompt_id") or payload.get("id")
        successful_node_ids = payload.get("successful_node_ids") or list(payload.get("outputs", {}).keys())
        return StepExecutionResult(
            stage=expected_stage,
            artifacts=artifacts,
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
