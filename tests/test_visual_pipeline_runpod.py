from __future__ import annotations

import pytest

from vixenbliss_creator.visual_pipeline import Provider, ResumeCheckpoint, ResumeStage, VisualArtifact, VisualArtifactRole
from vixenbliss_creator.visual_pipeline.adapters import RunpodServerlessExecutionClient
from vixenbliss_creator.visual_pipeline.config import VisualPipelineSettings
from vixenbliss_creator.visual_pipeline.models import VisualGenerationRequest


def build_request(**overrides: object) -> VisualGenerationRequest:
    payload = {
        "workflow_id": "base-image-ipadapter-impact",
        "workflow_version": "2026-03-30",
        "base_model_id": "base-image-model.safetensors",
        "prompt": "editorial portrait of a synthetic performer with premium soft lighting",
        "negative_prompt": "low quality, anatomy drift, extra limbs, text, watermark",
        "seed": 42,
        "width": 1024,
        "height": 1024,
        "provider": Provider.RUNPOD,
        "reference_face_image_url": "https://example.com/reference.png",
        "ip_adapter": {"enabled": True, "model_name": "plus_face", "weight": 0.9},
        "face_detailer": {"enabled": True, "confidence_threshold": 0.8, "inpaint_strength": 0.4},
    }
    payload.update(overrides)
    return VisualGenerationRequest.model_validate(payload)


def build_checkpoint() -> ResumeCheckpoint:
    return ResumeCheckpoint(
        workflow_id="base-image-ipadapter-impact",
        workflow_version="2026-03-30",
        base_model_id="base-image-model.safetensors",
        seed=42,
        stage=ResumeStage.BASE_RENDER,
        provider=Provider.RUNPOD,
        provider_job_id="job-1",
        successful_node_ids=["ksampler", "save_base_image"],
        intermediate_artifacts=[
            VisualArtifact(
                role=VisualArtifactRole.BASE_IMAGE,
                uri="https://example.com/base.png",
                content_type="image/png",
                metadata_json={},
            )
        ],
        metadata_json={"face_detection_confidence": 0.62},
    )


def build_settings(**overrides: object) -> VisualPipelineSettings:
    payload = {
        "visual_execution_provider": Provider.RUNPOD,
        "runpod_api_key": "secret",
        "runpod_endpoint_image_gen": "https://api.runpod.ai/v2/endpoint",
        "runpod_poll_interval_seconds": 0,
        "runpod_job_timeout_seconds": 5,
        "comfyui_http_timeout_seconds": 5,
    }
    payload.update(overrides)
    return VisualPipelineSettings(**payload)


def test_runpod_client_completes_base_render_job(monkeypatch: pytest.MonkeyPatch) -> None:
    posts: list[tuple[str, dict, dict[str, str] | None]] = []

    def fake_post(url: str, payload: dict, timeout_seconds: int, headers: dict[str, str] | None = None) -> dict:
        posts.append((url, payload, headers))
        assert timeout_seconds == 5
        if url.endswith("/run"):
            return {"id": "job-123", "status": "IN_QUEUE"}
        raise AssertionError(f"unexpected POST {url}")

    def fake_get(url: str, timeout_seconds: int, headers: dict[str, str] | None = None) -> dict:
        assert url.endswith("/status/job-123")
        assert timeout_seconds == 5
        return {
            "status": "COMPLETED",
            "output": {
                "provider_job_id": "job-123",
                "artifacts": [
                    {
                        "role": "base_image",
                        "uri": "https://example.com/base.png",
                        "content_type": "image/png",
                        "metadata_json": {},
                    }
                ],
                "face_detection_confidence": 0.91,
                "metadata": {"mode": "base_render"},
            },
        }

    monkeypatch.setattr("vixenbliss_creator.visual_pipeline.adapters._json_post", fake_post)
    monkeypatch.setattr("vixenbliss_creator.visual_pipeline.adapters._json_get", fake_get)

    result = RunpodServerlessExecutionClient(build_settings()).render_base_image(build_request())

    assert result.provider == Provider.RUNPOD
    assert result.provider_job_id == "job-123"
    assert result.face_detection_confidence == pytest.approx(0.91)
    assert posts[0][0] == "https://api.runpod.ai/v2/endpoint/run"
    assert posts[0][2] == {"Authorization": "Bearer secret"}
    assert posts[0][1]["input"]["mode"] == "base_render"


def test_runpod_client_completes_face_detail_job(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_post(url: str, payload: dict, timeout_seconds: int, headers: dict[str, str] | None = None) -> dict:
        return {
            "output": {
                "provider_job_id": "job-456",
                "artifacts": [
                    {
                        "role": "final_image",
                        "uri": "https://example.com/final.png",
                        "content_type": "image/png",
                        "metadata_json": {},
                    }
                ],
                "metadata": {"mode": "face_detail"},
            }
        }

    monkeypatch.setattr("vixenbliss_creator.visual_pipeline.adapters._json_post", fake_post)

    result = RunpodServerlessExecutionClient(build_settings(runpod_use_runsync=True)).run_face_detail(
        build_request(),
        build_checkpoint(),
    )

    assert result.provider == Provider.RUNPOD
    assert result.provider_job_id == "job-456"
    assert result.artifacts[0].role == VisualArtifactRole.FINAL_IMAGE


def test_runpod_client_times_out(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_post(url: str, payload: dict, timeout_seconds: int, headers: dict[str, str] | None = None) -> dict:
        return {"id": "job-timeout"}

    def fake_get(url: str, timeout_seconds: int, headers: dict[str, str] | None = None) -> dict:
        return {"status": "IN_PROGRESS"}

    monkeypatch.setattr("vixenbliss_creator.visual_pipeline.adapters._json_post", fake_post)
    monkeypatch.setattr("vixenbliss_creator.visual_pipeline.adapters._json_get", fake_get)

    client = RunpodServerlessExecutionClient(build_settings(runpod_job_timeout_seconds=0))
    with pytest.raises(RuntimeError, match="did not complete"):
        client.render_base_image(build_request())


def test_runpod_client_raises_on_failed_job(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_post(url: str, payload: dict, timeout_seconds: int, headers: dict[str, str] | None = None) -> dict:
        return {"id": "job-failed"}

    def fake_get(url: str, timeout_seconds: int, headers: dict[str, str] | None = None) -> dict:
        return {"status": "FAILED", "error": "worker crashed"}

    monkeypatch.setattr("vixenbliss_creator.visual_pipeline.adapters._json_post", fake_post)
    monkeypatch.setattr("vixenbliss_creator.visual_pipeline.adapters._json_get", fake_get)

    client = RunpodServerlessExecutionClient(build_settings())
    with pytest.raises(RuntimeError, match="FAILED"):
        client.render_base_image(build_request())
