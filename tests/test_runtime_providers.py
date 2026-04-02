from __future__ import annotations

import pytest

from vixenbliss_creator.runtime_providers import (
    BeamRuntimeProviderClient,
    JobStatus,
    ModalRuntimeProviderClient,
    RuntimeProviderSettings,
    ServiceRuntime,
)


def test_runtime_provider_settings_reads_service_specific_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("S1_IMAGE_PROVIDER", "beam")
    monkeypatch.setenv("S1_LORA_TRAIN_PROVIDER", "modal")
    monkeypatch.setenv("S1_LLM_PROVIDER", "modal")
    monkeypatch.setenv("S2_IMAGE_PROVIDER", "beam")
    monkeypatch.setenv("S2_VIDEO_PROVIDER", "modal")
    monkeypatch.setenv("BEAM_ENDPOINT_S1_IMAGE", "https://beam.example.com/s1-image")
    monkeypatch.setenv("MODAL_ENDPOINT_S2_VIDEO", "https://modal.example.com/s2-video")

    settings = RuntimeProviderSettings.from_env()

    assert settings.provider_for(ServiceRuntime.S1_IMAGE).value == "beam"
    assert settings.provider_for(ServiceRuntime.S2_VIDEO).value == "modal"
    assert settings.endpoint_for(settings.provider_for(ServiceRuntime.S1_IMAGE), ServiceRuntime.S1_IMAGE) == "https://beam.example.com/s1-image"
    assert settings.endpoint_for(settings.provider_for(ServiceRuntime.S2_VIDEO), ServiceRuntime.S2_VIDEO) == "https://modal.example.com/s2-video"


def test_beam_client_submits_and_fetches_result(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = RuntimeProviderSettings(
        beam_api_key="beam-secret",
        beam_endpoint_s1_image="https://beam.example.com/s1-image",
        provider_poll_interval_seconds=0,
        provider_job_timeout_seconds=5,
    )

    def fake_post(url: str, payload: dict, timeout_seconds: int, headers: dict[str, str] | None = None) -> dict:
        assert url == "https://beam.example.com/s1-image/jobs"
        assert payload["service_runtime"] == "s1_image"
        assert headers == {"Authorization": "Bearer beam-secret"}
        return {"job_id": "beam-job-1", "status": "queued"}

    get_calls: list[str] = []

    def fake_get(url: str, timeout_seconds: int, headers: dict[str, str] | None = None) -> dict:
        get_calls.append(url)
        if url.endswith("/jobs/beam-job-1"):
            return {"status": "completed", "result_url": "https://beam.example.com/s1-image/jobs/beam-job-1/result"}
        if url.endswith("/jobs/beam-job-1/result"):
            return {"artifacts": [{"role": "base_image", "uri": "https://example.com/base.png", "content_type": "image/png", "metadata_json": {}}]}
        raise AssertionError(f"unexpected GET {url}")

    monkeypatch.setattr("vixenbliss_creator.runtime_providers.adapters._json_post", fake_post)
    monkeypatch.setattr("vixenbliss_creator.runtime_providers.adapters._json_get", fake_get)

    client = BeamRuntimeProviderClient(settings)
    handle = client.submit_job(ServiceRuntime.S1_IMAGE, {"prompt": "hello"})
    result = client.fetch_result(handle)

    assert handle.status == JobStatus.QUEUED
    assert result["artifacts"][0]["uri"] == "https://example.com/base.png"
    assert get_calls[0] == "https://beam.example.com/s1-image/jobs/beam-job-1"


def test_modal_client_healthcheck_uses_modal_headers(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = RuntimeProviderSettings(
        modal_token_id="modal-id",
        modal_token_secret="modal-secret",
        modal_endpoint_s1_llm="https://modal.example.com/s1-llm",
    )

    def fake_get(url: str, timeout_seconds: int, headers: dict[str, str] | None = None) -> dict:
        assert url == "https://modal.example.com/s1-llm/healthcheck"
        assert headers == {"Modal-Key": "modal-id", "Modal-Secret": "modal-secret"}
        return {"ok": True}

    monkeypatch.setattr("vixenbliss_creator.runtime_providers.adapters._json_get", fake_get)

    client = ModalRuntimeProviderClient(settings)
    response = client.healthcheck(ServiceRuntime.S1_LLM)

    assert response == {"ok": True}
