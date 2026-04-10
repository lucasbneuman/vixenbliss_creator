from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from fastapi.testclient import TestClient


RUNTIME_PATH = Path(__file__).resolve().parents[1] / "infra" / "comfyui-copilot" / "runtime" / "app.py"


def _load_runtime_module(monkeypatch) -> object:
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-token")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4.1-mini")
    spec = importlib.util.spec_from_file_location("test_comfyui_copilot_runtime_module", RUNTIME_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_comfyui_copilot_healthcheck_reports_registry(monkeypatch) -> None:
    module = _load_runtime_module(monkeypatch)
    client = TestClient(module.app)

    response = client.get("/healthcheck")

    assert response.status_code == 200
    payload = response.json()
    assert payload["service"] == "comfyui_copilot"
    assert payload["provider"] == "openai"
    assert payload["provider_ready"] is True
    assert payload["registry_entries"]["s1_identity_image"] >= 1


def test_comfyui_copilot_recommend_returns_openai_payload(monkeypatch) -> None:
    module = _load_runtime_module(monkeypatch)

    def fake_json_request(method: str, url: str, **kwargs) -> dict:
        assert method == "POST"
        assert url.endswith("/chat/completions")
        payload = kwargs["payload"]
        assert payload["model"] == "gpt-4.1-mini"
        return {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "stage": "s1_identity_image",
                                "workflow_id": "base-image-ipadapter-impact",
                                "workflow_version": "2026-03-31",
                                "recommended_workflow_family": "flux_identity_reference",
                                "base_model_id": "flux-schnell-v1",
                                "required_nodes": ["load_model", "ip_adapter_plus", "ksampler", "vae_decode"],
                                "optional_nodes": ["face_detector"],
                                "model_hints": ["flux", "ipadapter-face"],
                                "prompt_template": "Identity portrait optimized for premium continuity.",
                                "negative_prompt": "low quality, anatomy drift, extra limbs",
                                "reasoning_summary": "Best approved workflow for identity continuity.",
                                "risk_flags": ["identity_drift"],
                                "compatibility_notes": ["Approved for System 1 identity generation."],
                                "content_modes_supported": ["sfw", "sensual", "nsfw"],
                                "registry_source": "modal_openai",
                            }
                        )
                    }
                }
            ]
        }

    monkeypatch.setattr(module, "_json_request", fake_json_request)
    client = TestClient(module.app)

    response = client.post(
        "/recommend",
        json={
            "stage": "s1_identity_image",
            "expansion_summary": "Expansion summary for identity generation.",
            "prompt_blueprint": "Prompt blueprint for approved workflow selection.",
            "technical_sheet_payload": {"identity_metadata": {"vertical": "lifestyle"}},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["workflow_id"] == "base-image-ipadapter-impact"
    assert payload["registry_source"] == "modal_openai"


def test_comfyui_copilot_recommend_falls_back_when_openai_fails(monkeypatch) -> None:
    module = _load_runtime_module(monkeypatch)

    def fake_json_request(method: str, url: str, **kwargs) -> dict:
        raise RuntimeError("upstream timeout")

    monkeypatch.setattr(module, "_json_request", fake_json_request)
    client = TestClient(module.app)

    response = client.post(
        "/recommend",
        json={
            "stage": "s2_video",
            "expansion_summary": "Video expansion summary.",
            "prompt_blueprint": "Video prompt blueprint for approved workflow selection.",
            "technical_sheet_payload": {"identity_metadata": {"vertical": "lifestyle"}},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["workflow_id"] == "video-image-to-video-prep"
    assert payload["registry_source"] == "modal_openai_fallback"
    assert "Fallback reason:" in " ".join(payload["compatibility_notes"])
