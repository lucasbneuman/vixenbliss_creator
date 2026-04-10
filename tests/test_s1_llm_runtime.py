from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from urllib.parse import urlparse

from fastapi.testclient import TestClient

from vixenbliss_creator.agentic.config import AgenticSettings
from vixenbliss_creator.agentic.models import CompletionStatus
from vixenbliss_creator.agentic.runner import run_agentic_brain_with_real_llm
from tests.test_agentic_brain import build_expansion_payload


RUNTIME_PATH = Path(__file__).resolve().parents[1] / "infra" / "s1-llm" / "runtime" / "app.py"


def _build_expansion_payload() -> dict:
    return build_expansion_payload(with_hard_limits=True, vertical="lifestyle", style="premium")


def _load_runtime_module(monkeypatch) -> object:
    monkeypatch.setenv("S1_LLM_BACKEND", "openai")
    monkeypatch.setenv("OPEN_AI_TOKEN", "test-openai-token")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4.1-mini")
    monkeypatch.setenv("OLLAMA_STARTUP_ENABLED", "0")
    monkeypatch.setenv("DIRECTUS_BASE_URL", "http://example.com")
    monkeypatch.setenv("DIRECTUS_API_TOKEN", "secret")
    spec = importlib.util.spec_from_file_location("test_s1_llm_runtime_module", RUNTIME_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_s1_llm_runtime_proxies_chat_and_records_directus(monkeypatch) -> None:
    module = _load_runtime_module(monkeypatch)
    calls: list[dict] = []

    class Recorder:
        def record_job(self, **kwargs):
            calls.append(kwargs)
            return {"id": "run-1"}

    def fake_json_request(method: str, url: str, **kwargs) -> dict:
        if url.endswith("/v1/chat/completions"):
            payload = kwargs["payload"]
            assert payload["model"] == "gpt-4.1-mini"
            return {
                "id": "chatcmpl-test",
                "object": "chat.completion",
                "model": "gpt-4.1-mini",
                "choices": [{"index": 0, "message": {"role": "assistant", "content": json.dumps(_build_expansion_payload())}}],
            }
        if url.endswith("/models"):
            return {"data": [{"id": "gpt-4.1-mini"}]}
        raise AssertionError(f"unexpected url {url}")

    monkeypatch.setattr(module, "_directus_recorder", Recorder())
    monkeypatch.setattr(module, "_json_request", fake_json_request)
    client = TestClient(module.app)

    response = client.post(
        "/v1/chat/completions",
        json={
            "messages": [{"role": "user", "content": "hola"}],
            "metadata": {"identity_id": "identity-1", "directus_run_id": "run-1"},
        },
    )

    assert response.status_code == 200
    assert response.json()["model"] == "gpt-4.1-mini"
    assert calls[0]["service_name"] == "s1_llm_completion"
    assert calls[0]["input_payload"]["directus_run_id"] == "run-1"


def test_s1_llm_runtime_healthcheck_reports_ollama_status(monkeypatch) -> None:
    module = _load_runtime_module(monkeypatch)

    def fake_json_request(method: str, url: str, **kwargs) -> dict:
        assert method == "GET"
        assert url.endswith("/models")
        assert kwargs["headers"]["Authorization"] == "Bearer test-openai-token"
        return {"data": [{"id": "gpt-4.1-mini"}]}

    monkeypatch.setattr(module, "_json_request", fake_json_request)
    client = TestClient(module.app)

    response = client.get("/healthcheck")

    assert response.status_code == 200
    assert response.json()["provider_ready"] is True
    assert response.json()["llm_backend"] == "openai"
    assert response.json()["openai_api_model"] == "gpt-4.1-mini"


def test_langgraph_smoke_can_use_s1_llm_runtime_openai_endpoint(monkeypatch) -> None:
    module = _load_runtime_module(monkeypatch)

    def fake_json_request(method: str, url: str, **kwargs) -> dict:
        if url.endswith("/v1/chat/completions"):
            return {
                "id": "chatcmpl-test",
                "object": "chat.completion",
                "model": "gpt-4.1-mini",
                "choices": [{"index": 0, "message": {"role": "assistant", "content": json.dumps(_build_expansion_payload())}}],
            }
        if url.endswith("/models"):
            return {"data": [{"id": "gpt-4.1-mini"}]}
        raise AssertionError(f"unexpected url {url}")

    monkeypatch.setattr(module, "_json_request", fake_json_request)
    monkeypatch.setattr(module, "_directus_recorder", None)
    client = TestClient(module.app)

    def fake_post(url: str, payload: dict, headers: dict[str, str], **kwargs) -> dict:
        path = urlparse(url).path
        response = client.post(path, json=payload, headers=headers)
        assert response.status_code == 200, response.text
        return response.json()

    monkeypatch.setattr("vixenbliss_creator.agentic.adapters._json_post", fake_post)

    settings = AgenticSettings(
        s1_llm_runtime_base_url="http://testserver",
        s1_llm_runtime_model="gpt-4.1-mini",
    )

    result = run_agentic_brain_with_real_llm("Crea un avatar lifestyle", settings=settings)

    assert result.completion_status == CompletionStatus.SUCCEEDED
    assert result.identity_draft is not None
    assert result.identity_draft.metadata.style == "premium"


def test_s1_llm_runtime_normalizes_partial_langgraph_payload(monkeypatch) -> None:
    module = _load_runtime_module(monkeypatch)

    def fake_json_request(method: str, url: str, **kwargs) -> dict:
        if url.endswith("/v1/chat/completions"):
            return {
                "id": "chatcmpl-test",
                "object": "chat.completion",
                "model": "gpt-4.1-mini",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": json.dumps(
                                {
                                    "identity_draft": {
                                        "name": "Velvet Ember",
                                    }
                                }
                            ),
                        },
                    }
                ],
            }
        if url.endswith("/models"):
            return {"data": [{"id": "gpt-4.1-mini"}]}
        raise AssertionError(f"unexpected url {url}")

    monkeypatch.setattr(module, "_json_request", fake_json_request)
    monkeypatch.setattr(module, "_directus_recorder", None)
    client = TestClient(module.app)

    response = client.post(
        "/v1/chat/completions",
        json={
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": json.dumps(
                        {
                            "instructions": "You are generating a VixenBliss ExpansionResult object.",
                        }
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps({"idea": "Crea un avatar lifestyle premium"}),
                },
            ],
        },
    )

    assert response.status_code == 200
    content = json.loads(response.json()["choices"][0]["message"]["content"])
    assert content["normalized_constraints"]["vertical"] == "lifestyle"
    assert content["identity_draft"]["metadata"]["style"] == "premium"
    assert content["technical_sheet_payload"]["identity_core"]["display_name"] == "Velvet Ember"


def test_s1_llm_runtime_keeps_generic_chat_payload_unchanged(monkeypatch) -> None:
    module = _load_runtime_module(monkeypatch)
    proxied_payloads: list[dict] = []

    def fake_json_request(method: str, url: str, **kwargs) -> dict:
        if url.endswith("/v1/chat/completions"):
            proxied_payloads.append(kwargs["payload"])
            return {
                "id": "chatcmpl-test",
                "object": "chat.completion",
                "model": "gpt-4.1-mini",
                "choices": [{"index": 0, "message": {"role": "assistant", "content": "hola"}}],
            }
        if url.endswith("/models"):
            return {"data": [{"id": "gpt-4.1-mini"}]}
        raise AssertionError(f"unexpected url {url}")

    monkeypatch.setattr(module, "_json_request", fake_json_request)
    monkeypatch.setattr(module, "_directus_recorder", None)
    client = TestClient(module.app)

    response = client.post(
        "/v1/chat/completions",
        json={
            "messages": [{"role": "user", "content": "hola"}],
        },
    )

    assert response.status_code == 200
    assert response.json()["choices"][0]["message"]["content"] == "hola"
    assert proxied_payloads[0]["messages"] == [{"role": "user", "content": "hola"}]
