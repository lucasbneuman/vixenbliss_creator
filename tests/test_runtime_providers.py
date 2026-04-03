from __future__ import annotations

import pytest

from vixenbliss_creator.runtime_providers import (
    BeamRuntimeProviderClient,
    JobStatus,
    ModalRuntimeProviderClient,
    RuntimeProviderSettings,
    ServiceRuntime,
)


def test_runtime_provider_settings_reads_modal_app_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("S1_IMAGE_PROVIDER", "modal")
    monkeypatch.setenv("S1_IMAGE_MODAL_APP_NAME", "vixenbliss-s1-image")
    monkeypatch.setenv("S1_IMAGE_MODAL_FUNCTION_NAME", "run_s1_image_job")
    monkeypatch.setenv("S1_LLM_MODAL_APP_NAME", "vixenbliss-s1-llm")
    monkeypatch.setenv("S1_LLM_MODAL_WEB_FUNCTION_NAME", "fastapi_app")

    settings = RuntimeProviderSettings.from_env()

    assert settings.provider_for(ServiceRuntime.S1_IMAGE).value == "modal"
    assert settings.modal_app_name_for(ServiceRuntime.S1_IMAGE) == "vixenbliss-s1-image"
    assert settings.modal_job_function_for(ServiceRuntime.S1_IMAGE) == "run_s1_image_job"
    assert settings.modal_web_function_for(ServiceRuntime.S1_LLM) == "fastapi_app"


def test_runtime_provider_settings_defaults_to_modal_for_all_services() -> None:
    settings = RuntimeProviderSettings()

    assert settings.provider_for(ServiceRuntime.S1_IMAGE).value == "modal"
    assert settings.provider_for(ServiceRuntime.S1_LORA_TRAIN).value == "modal"
    assert settings.provider_for(ServiceRuntime.S1_LLM).value == "modal"
    assert settings.provider_for(ServiceRuntime.S2_IMAGE).value == "modal"
    assert settings.provider_for(ServiceRuntime.S2_VIDEO).value == "modal"


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


def test_modal_client_submits_jobs_via_remote_function(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = RuntimeProviderSettings(
        modal_app_name_s1_image="vixenbliss-s1-image",
        modal_job_function_s1_image="run_s1_image_job",
    )

    class FakeRemoteFunction:
        def remote(self, payload: dict) -> dict:
            assert payload["prompt"] == "hello"
            return {"provider": "modal", "provider_job_id": "modal-job-1", "artifacts": [{"role": "base_image", "uri": "modal://base"}]}

    monkeypatch.setattr("modal.Function.from_name", lambda app_name, function_name: FakeRemoteFunction())

    client = ModalRuntimeProviderClient(settings)
    handle = client.submit_job(ServiceRuntime.S1_IMAGE, {"prompt": "hello"})
    result = client.fetch_result(handle)

    assert handle.status == JobStatus.COMPLETED
    assert result["provider"] == "modal"
    assert result["artifacts"][0]["uri"] == "modal://base"


def test_modal_client_derives_healthcheck_url_from_modal_web_function(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = RuntimeProviderSettings(
        modal_token_id="modal-id",
        modal_token_secret="modal-secret",
        modal_app_name_s1_llm="vixenbliss-s1-llm",
        modal_web_function_s1_llm="fastapi_app",
    )

    class FakeWebFunction:
        def get_web_url(self) -> str:
            return "https://modal.example.com/s1-llm"

    def fake_from_name(app_name: str, function_name: str):
        assert app_name == "vixenbliss-s1-llm"
        assert function_name == "fastapi_app"
        return FakeWebFunction()

    def fake_get(url: str, timeout_seconds: int, headers: dict[str, str] | None = None) -> dict:
        assert url == "https://modal.example.com/s1-llm/healthcheck"
        assert headers == {"Modal-Key": "modal-id", "Modal-Secret": "modal-secret"}
        return {"ok": True}

    monkeypatch.setattr("modal.Function.from_name", fake_from_name)
    monkeypatch.setattr("vixenbliss_creator.runtime_providers.adapters._json_get", fake_get)

    client = ModalRuntimeProviderClient(settings)
    response = client.healthcheck(ServiceRuntime.S1_LLM)

    assert response == {"ok": True}


def test_handle_defaults_progress_url_when_provider_uses_http_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = RuntimeProviderSettings(
        modal_endpoint_s1_image="https://modal.example.com/s1-image",
        modal_token_id="modal-id",
        modal_token_secret="modal-secret",
    )

    def fake_post(url: str, payload: dict, timeout_seconds: int, headers: dict[str, str] | None = None) -> dict:
        return {"job_id": "modal-job-2", "status": "queued"}

    monkeypatch.setattr("vixenbliss_creator.runtime_providers.adapters._json_post", fake_post)

    client = ModalRuntimeProviderClient(settings)
    handle = client.submit_job(ServiceRuntime.S1_IMAGE, {"prompt": "hello"})

    assert handle.progress_url == "wss://modal.example.com/s1-image/ws/jobs/modal-job-2"


def test_modal_client_prefers_inline_output_over_result_fetch(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = RuntimeProviderSettings(
        modal_endpoint_s1_image="https://modal.example.com/s1-image",
        provider_poll_interval_seconds=0,
        provider_job_timeout_seconds=5,
    )

    def fake_post(url: str, payload: dict, timeout_seconds: int, headers: dict[str, str] | None = None) -> dict:
        return {
            "job_id": "modal-job-inline",
            "status": "completed",
            "output": {"provider": "modal", "artifacts": [{"role": "base_image", "uri": "inline://base"}]},
        }

    def fail_get(url: str, timeout_seconds: int, headers: dict[str, str] | None = None) -> dict:
        raise AssertionError(f"fetch_result should not call GET when inline output is available: {url}")

    monkeypatch.setattr("vixenbliss_creator.runtime_providers.adapters._json_post", fake_post)
    monkeypatch.setattr("vixenbliss_creator.runtime_providers.adapters._json_get", fail_get)

    client = ModalRuntimeProviderClient(settings)
    handle = client.submit_job(ServiceRuntime.S1_IMAGE, {"prompt": "hello"})
    result = client.fetch_result(handle)

    assert handle.status == JobStatus.COMPLETED
    assert result["artifacts"][0]["uri"] == "inline://base"
