from __future__ import annotations

import pytest
from pydantic import ValidationError

from vixenbliss_creator.visual_pipeline import (
    BeamExecutionClient,
    ErrorCode,
    FakeVisualExecutionClient,
    ModelFamily,
    ModalExecutionClient,
    Provider,
    ResumeCheckpoint,
    ResumePolicy,
    ResumeStage,
    RoutedVisualExecutionClient,
    RuntimeStage,
    VisualArtifact,
    VisualArtifactRole,
    VisualGenerationOrchestrator,
    VisualGenerationRequest,
    VisualPipelineSettings,
    build_visual_execution_client,
)
from vixenbliss_creator.visual_pipeline.adapters import RunpodServerlessExecutionClient
from vixenbliss_creator.visual_pipeline.models import StepExecutionResult
from vixenbliss_creator.runtime_providers import RuntimeProviderSettings


def build_request(**overrides: object) -> VisualGenerationRequest:
    payload = {
        "workflow_id": "base-portrait-v1",
        "workflow_version": "2026-03-30",
        "base_model_id": "flux-schnell-v1",
        "model_family": "flux",
        "runtime_stage": "content_image",
        "prompt": "editorial portrait of a synthetic performer with premium soft lighting",
        "negative_prompt": "low quality, anatomy drift, extra limbs, text, watermark",
        "seed": 42,
        "width": 1024,
        "height": 1024,
        "provider": Provider.COMFYUI_HTTP,
        "reference_face_image_url": "https://example.com/reference-face.png",
        "ip_adapter": {"enabled": True, "model_name": "plus_face", "weight": 0.9},
        "face_detailer": {"enabled": True, "confidence_threshold": 0.8, "inpaint_strength": 0.4},
    }
    payload.update(overrides)
    return VisualGenerationRequest.model_validate(payload)


def build_artifact(role: VisualArtifactRole, uri: str) -> VisualArtifact:
    return VisualArtifact(role=role, uri=uri, content_type="image/png", metadata_json={})


def test_request_requires_reference_when_ip_adapter_is_enabled() -> None:
    with pytest.raises(ValueError, match="reference_face_image_url"):
        build_request(reference_face_image_url=None)


def test_request_rejects_non_flux_family() -> None:
    with pytest.raises(ValidationError, match="Input should be 'flux'"):
        build_request(model_family="custom_lora")


def test_content_runtime_requires_validated_lora_when_present() -> None:
    with pytest.raises(ValueError, match="content_image runtime requires explicit lora_validated=true"):
        build_request(lora_version="amber-v1", lora_validated=False)


def test_identity_runtime_rejects_lora_usage() -> None:
    with pytest.raises(ValueError, match="identity_image runtime must not consume a LoRA version"):
        build_request(runtime_stage="identity_image", lora_version="amber-v1")


def test_resume_checkpoint_rejects_incomplete_base_render_state() -> None:
    with pytest.raises(ValueError, match="base_render checkpoints require a base_image artifact"):
        ResumeCheckpoint(
            workflow_id="base-portrait-v1",
            workflow_version="2026-03-30",
            base_model_id="flux-schnell-v1",
            seed=42,
            stage=ResumeStage.BASE_RENDER,
            provider=Provider.COMFYUI_HTTP,
            provider_job_id="prompt-1",
            successful_node_ids=["ksampler"],
            intermediate_artifacts=[],
            metadata_json={},
        )


def test_orchestrator_returns_base_image_when_confidence_is_high() -> None:
    client = FakeVisualExecutionClient(
        base_result=StepExecutionResult(
            stage=ResumeStage.BASE_RENDER,
            artifacts=[build_artifact(VisualArtifactRole.BASE_IMAGE, "memory://base.png")],
            provider=Provider.COMFYUI_HTTP,
            provider_job_id="prompt-1",
            successful_node_ids=["ksampler", "decode"],
            face_detection_confidence=0.92,
            metadata_json={},
        )
    )
    result = VisualGenerationOrchestrator(client).generate(build_request())

    assert result.error_code is None
    assert result.regional_inpaint_triggered is False
    assert result.face_detection_confidence == pytest.approx(0.92)
    assert result.ip_adapter_used is True
    assert result.artifacts[0].role == VisualArtifactRole.FINAL_IMAGE
    assert client.calls == ["base_render"]


def test_orchestrator_triggers_face_detail_when_confidence_is_low() -> None:
    client = FakeVisualExecutionClient(
        base_result=StepExecutionResult(
            stage=ResumeStage.BASE_RENDER,
            artifacts=[build_artifact(VisualArtifactRole.BASE_IMAGE, "memory://base.png")],
            provider=Provider.COMFYUI_HTTP,
            provider_job_id="prompt-1",
            successful_node_ids=["ksampler", "decode"],
            face_detection_confidence=0.61,
            metadata_json={},
        ),
        face_detail_result=StepExecutionResult(
            stage=ResumeStage.FACE_DETAIL,
            artifacts=[build_artifact(VisualArtifactRole.FINAL_IMAGE, "memory://final.png")],
            provider=Provider.COMFYUI,
            provider_job_id="prompt-2",
            successful_node_ids=["face_detailer"],
            face_detection_confidence=None,
            metadata_json={},
        ),
    )
    result = VisualGenerationOrchestrator(client).generate(build_request())

    assert result.error_code is None
    assert result.regional_inpaint_triggered is True
    assert result.artifacts[0].uri == "memory://final.png"
    assert client.calls == ["base_render", "face_detail"]


def test_orchestrator_fails_when_face_detector_returns_no_confidence() -> None:
    client = FakeVisualExecutionClient(
        base_result=StepExecutionResult(
            stage=ResumeStage.BASE_RENDER,
            artifacts=[build_artifact(VisualArtifactRole.BASE_IMAGE, "memory://base.png")],
            provider=Provider.COMFYUI,
            provider_job_id="prompt-1",
            successful_node_ids=["ksampler"],
            face_detection_confidence=None,
            metadata_json={},
        )
    )
    result = VisualGenerationOrchestrator(client).generate(build_request())

    assert result.error_code == ErrorCode.FACE_CONFIDENCE_UNAVAILABLE
    assert result.artifacts == []
    assert client.calls == ["base_render"]


def test_orchestrator_resumes_without_repeating_base_render() -> None:
    checkpoint = ResumeCheckpoint(
        workflow_id="base-portrait-v1",
        workflow_version="2026-03-30",
        base_model_id="flux-schnell-v1",
        seed=42,
        stage=ResumeStage.BASE_RENDER,
        provider=Provider.COMFYUI_HTTP,
        provider_job_id="prompt-1",
        successful_node_ids=["ksampler", "decode"],
        intermediate_artifacts=[build_artifact(VisualArtifactRole.BASE_IMAGE, "memory://base.png")],
        metadata_json={"face_detection_confidence": 0.54},
    )
    client = FakeVisualExecutionClient(
        face_detail_result=StepExecutionResult(
            stage=ResumeStage.FACE_DETAIL,
            artifacts=[build_artifact(VisualArtifactRole.FINAL_IMAGE, "memory://final.png")],
            provider=Provider.COMFYUI,
            provider_job_id="prompt-2",
            successful_node_ids=["face_detailer"],
            face_detection_confidence=None,
            metadata_json={},
        )
    )
    result = VisualGenerationOrchestrator(client).generate(
        build_request(resume_policy=ResumePolicy.FROM_CHECKPOINT, resume_checkpoint=checkpoint)
    )

    assert result.error_code is None
    assert result.regional_inpaint_triggered is True
    assert client.calls == ["face_detail"]


def test_settings_from_env_reads_visual_pipeline_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VISUAL_EXECUTION_PROVIDER", "routed")
    monkeypatch.setenv("COMFYUI_BASE_URL", "https://comfy.example.com")
    monkeypatch.setenv("COMFYUI_WORKFLOW_IMAGE_ID", "base-portrait-v1")
    monkeypatch.setenv("COMFYUI_WORKFLOW_IMAGE_VERSION", "2026-03-30")
    monkeypatch.setenv("COMFYUI_WORKFLOW_IDENTITY_ID", "identity-workflow-v1")
    monkeypatch.setenv("COMFYUI_WORKFLOW_CONTENT_ID", "content-workflow-v1")
    monkeypatch.setenv("COMFYUI_WORKFLOW_VIDEO_ID", "video-workflow-v1")
    monkeypatch.setenv("COMFYUI_IP_ADAPTER_MODEL", "plus_face")
    monkeypatch.setenv("COMFYUI_FACE_CONFIDENCE_THRESHOLD", "0.85")
    monkeypatch.setenv("COMFYUI_RESUME_CACHE_MODE", "checkpoint")
    monkeypatch.setenv("COMFYUI_HTTP_TIMEOUT_SECONDS", "45")
    monkeypatch.setenv("S1_IMAGE_PROVIDER", "beam")
    monkeypatch.setenv("S1_LORA_TRAIN_PROVIDER", "modal")
    monkeypatch.setenv("S1_LLM_PROVIDER", "modal")
    monkeypatch.setenv("S2_IMAGE_PROVIDER", "beam")
    monkeypatch.setenv("S2_VIDEO_PROVIDER", "modal")
    monkeypatch.setenv("BEAM_API_KEY", "beam-secret")
    monkeypatch.setenv("BEAM_ENDPOINT_S1_IMAGE", "https://beam.example.com/s1-image")
    monkeypatch.setenv("BEAM_ENDPOINT_S2_IMAGE", "https://beam.example.com/s2-image")
    monkeypatch.setenv("MODAL_TOKEN_ID", "modal-id")
    monkeypatch.setenv("MODAL_TOKEN_SECRET", "modal-secret")
    monkeypatch.setenv("MODAL_ENDPOINT_S1_LORA_TRAIN", "https://modal.example.com/s1-lora-train")
    monkeypatch.setenv("MODAL_ENDPOINT_S1_LLM", "https://modal.example.com/s1-llm")
    monkeypatch.setenv("MODAL_ENDPOINT_S2_VIDEO", "https://modal.example.com/s2-video")
    monkeypatch.setenv("PROVIDER_POLL_INTERVAL_SECONDS", "2")
    monkeypatch.setenv("PROVIDER_JOB_TIMEOUT_SECONDS", "120")

    settings = VisualPipelineSettings.from_env()

    assert settings.visual_execution_provider == Provider.ROUTED
    assert settings.comfyui_base_url == "https://comfy.example.com"
    assert settings.comfyui_workflow_image_id == "base-portrait-v1"
    assert settings.comfyui_workflow_image_version == "2026-03-30"
    assert settings.comfyui_workflow_identity_id == "identity-workflow-v1"
    assert settings.comfyui_workflow_content_id == "content-workflow-v1"
    assert settings.comfyui_workflow_video_id == "video-workflow-v1"
    assert settings.comfyui_ip_adapter_model == "plus_face"
    assert settings.comfyui_face_confidence_threshold == pytest.approx(0.85)
    assert settings.comfyui_resume_cache_mode == "checkpoint"
    assert settings.comfyui_http_timeout_seconds == 45
    assert settings.runtime_provider_settings.s1_image_provider == Provider.BEAM
    assert settings.runtime_provider_settings.s1_lora_train_provider == Provider.MODAL
    assert settings.runtime_provider_settings.s1_llm_provider == Provider.MODAL
    assert settings.runtime_provider_settings.s2_image_provider == Provider.BEAM
    assert settings.runtime_provider_settings.s2_video_provider == Provider.MODAL
    assert settings.runtime_provider_settings.beam_api_key == "beam-secret"
    assert settings.runtime_provider_settings.beam_endpoint_s1_image == "https://beam.example.com/s1-image"
    assert settings.runtime_provider_settings.modal_endpoint_s1_lora_train == "https://modal.example.com/s1-lora-train"
    assert settings.runtime_provider_settings.provider_poll_interval_seconds == 2
    assert settings.runtime_provider_settings.provider_job_timeout_seconds == 120


def test_build_visual_execution_client_selects_routed_by_default() -> None:
    client = build_visual_execution_client(
        VisualPipelineSettings(
            visual_execution_provider=Provider.ROUTED,
            runtime_provider_settings=RuntimeProviderSettings(
                s1_image_provider=Provider.BEAM,
                s2_image_provider=Provider.BEAM,
                s2_video_provider=Provider.MODAL,
            ),
        )
    )

    assert isinstance(client, RoutedVisualExecutionClient)


def test_build_visual_execution_client_selects_beam() -> None:
    client = build_visual_execution_client(
        VisualPipelineSettings(
            visual_execution_provider=Provider.BEAM,
            runtime_provider_settings=RuntimeProviderSettings(beam_endpoint_s2_image="https://beam.example.com/s2-image"),
        )
    )

    assert isinstance(client, BeamExecutionClient)


def test_build_visual_execution_client_selects_modal() -> None:
    client = build_visual_execution_client(
        VisualPipelineSettings(
            visual_execution_provider=Provider.MODAL,
            runtime_provider_settings=RuntimeProviderSettings(
                modal_endpoint_s2_image="https://modal.example.com/s2-image",
                modal_token_id="id",
                modal_token_secret="secret",
            ),
        )
    )

    assert isinstance(client, ModalExecutionClient)
