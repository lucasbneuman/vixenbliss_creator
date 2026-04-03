from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from urllib.parse import urlparse

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PATH = ROOT / "infra" / "s1-image" / "runtime" / "app.py"


def _load_runtime_module(tmp_path: Path, monkeypatch) -> object:
    comfy_home = tmp_path / "comfyui"
    models_dir = comfy_home / "models"
    output_dir = comfy_home / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("COMFYUI_HOME", str(comfy_home))
    monkeypatch.setenv("COMFYUI_CUSTOM_NODES_DIR", str(comfy_home / "custom_nodes"))
    monkeypatch.setenv("COMFYUI_MODELS_DIR", str(models_dir))
    monkeypatch.setenv("COMFYUI_USER_DIR", str(comfy_home / "user" / "default"))
    monkeypatch.setenv("COMFYUI_INPUT_DIR", str(comfy_home / "input"))
    monkeypatch.setenv("MODEL_CACHE_ROOT", str(tmp_path / "model-cache"))
    monkeypatch.setenv("DIRECTUS_BASE_URL", "http://example.com")
    monkeypatch.setenv("DIRECTUS_API_TOKEN", "secret")

    spec = importlib.util.spec_from_file_location("test_s1_image_runtime_module", RUNTIME_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["test_s1_image_runtime_module"] = module
    spec.loader.exec_module(module)
    return module


def _create_required_flux_assets(module: object) -> None:
    for path in module._required_runtime_paths().values():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"stub")


def _base_job_input(**overrides: object) -> dict:
    payload = {
        "action": "generate",
        "mode": "base_render",
        "workflow_id": "base-image-ipadapter-impact",
        "workflow_version": "2026-03-31",
        "base_model_id": "flux-schnell-v1",
        "runtime_stage": "identity_image",
        "prompt": "editorial portrait of a synthetic premium performer",
        "negative_prompt": "low quality, anatomy drift, extra limbs, text, watermark",
        "seed": 42,
        "width": 1024,
        "height": 1024,
        "reference_face_image_url": "https://example.com/ref.png",
        "ip_adapter": {"enabled": True, "model_name": "plus_face", "weight": 0.9},
        "face_detailer": {"enabled": True, "confidence_threshold": 0.8, "inpaint_strength": 0.35},
    }
    payload.update(overrides)
    return payload


def test_s1_image_runtime_healthcheck_reports_identity_contract(tmp_path: Path, monkeypatch) -> None:
    module = _load_runtime_module(tmp_path, monkeypatch)
    monkeypatch.setattr(module, "_ensure_comfyui_running", lambda: None)
    monkeypatch.setattr(module, "_healthcheck", lambda timeout_seconds=2: True)
    _create_required_flux_assets(module)
    client = TestClient(module.app)

    response = client.get("/healthcheck")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["runtime_contract"]["runtime_stage"] == "identity_image"
    assert payload["runtime_contract"]["workflow_scope"] == "s1_image"
    assert payload["runtime_contract"]["lora_supported"] is False


def test_s1_image_runtime_reports_reference_image_not_found(tmp_path: Path, monkeypatch) -> None:
    module = _load_runtime_module(tmp_path, monkeypatch)
    monkeypatch.setattr(module, "_ensure_comfyui_running", lambda: None)
    monkeypatch.setattr(module, "_download_remote_file", lambda *_args, **_kwargs: (_ for _ in ()).throw(FileNotFoundError("reference_face_image_url could not be resolved")))
    _create_required_flux_assets(module)
    client = TestClient(module.app)

    submit = client.post("/jobs", json={"input": _base_job_input()})
    assert submit.status_code == 200
    result = client.get(submit.json()["result_url"])

    assert result.status_code == 200
    assert result.json()["error_code"] == "REFERENCE_IMAGE_NOT_FOUND"


def test_s1_image_runtime_rejects_non_identity_stage(tmp_path: Path, monkeypatch) -> None:
    module = _load_runtime_module(tmp_path, monkeypatch)
    monkeypatch.setattr(module, "_ensure_comfyui_running", lambda: None)
    _create_required_flux_assets(module)
    client = TestClient(module.app)

    submit = client.post("/jobs", json={"input": _base_job_input(runtime_stage="content_image")})
    result = client.get(submit.json()["result_url"])

    assert result.json()["error_code"] == "COMFYUI_EXECUTION_FAILED"
    assert "unsupported runtime_stage content_image" in result.json()["error_message"]


def test_s1_image_runtime_rejects_lora_usage(tmp_path: Path, monkeypatch) -> None:
    module = _load_runtime_module(tmp_path, monkeypatch)
    monkeypatch.setattr(module, "_ensure_comfyui_running", lambda: None)
    _create_required_flux_assets(module)
    client = TestClient(module.app)

    submit = client.post("/jobs", json={"input": _base_job_input(lora_version="amber-v1")})
    result = client.get(submit.json()["result_url"])

    assert result.json()["error_code"] == "COMFYUI_EXECUTION_FAILED"
    assert "must not consume a LoRA version" in result.json()["error_message"]


def test_s1_image_runtime_reports_face_confidence_unavailable(tmp_path: Path, monkeypatch) -> None:
    module = _load_runtime_module(tmp_path, monkeypatch)
    monkeypatch.setattr(module, "_ensure_comfyui_running", lambda: None)
    monkeypatch.setattr(module, "_download_remote_file", lambda *_args, **_kwargs: "reference.png")
    monkeypatch.setattr(module, "_submit_prompt", lambda *_args, **_kwargs: "prompt-1")
    monkeypatch.setattr(
        module,
        "_poll_history",
        lambda _prompt_id: {
            "outputs": {
                "save_base_image": {
                    "images": [{"filename": "base.png", "subfolder": "vb", "type": "output"}],
                }
            }
        },
    )
    _create_required_flux_assets(module)
    (Path(module.COMFYUI_OUTPUT_DIR) / "vb").mkdir(parents=True, exist_ok=True)
    (Path(module.COMFYUI_OUTPUT_DIR) / "vb" / "base.png").write_bytes(b"png")
    client = TestClient(module.app)

    submit = client.post("/jobs", json={"input": _base_job_input()})
    result = client.get(submit.json()["result_url"])

    assert result.json()["error_code"] == "FACE_CONFIDENCE_UNAVAILABLE"


def test_s1_image_runtime_base_render_exposes_checkpoint_and_progress(tmp_path: Path, monkeypatch) -> None:
    module = _load_runtime_module(tmp_path, monkeypatch)
    monkeypatch.setattr(module, "_ensure_comfyui_running", lambda: None)
    monkeypatch.setattr(module, "_download_remote_file", lambda *_args, **_kwargs: "reference.png")
    monkeypatch.setattr(module, "_submit_prompt", lambda *_args, **_kwargs: "prompt-1")
    monkeypatch.setattr(
        module,
        "_poll_history",
        lambda _prompt_id: {
            "outputs": {
                "save_base_image": {
                    "images": [{"filename": "base.png", "subfolder": "vb", "type": "output"}],
                },
                "face_detector": {"metrics": {"bbox_confidence": 0.61}},
            }
        },
    )
    _create_required_flux_assets(module)
    (Path(module.COMFYUI_OUTPUT_DIR) / "vb").mkdir(parents=True, exist_ok=True)
    (Path(module.COMFYUI_OUTPUT_DIR) / "vb" / "base.png").write_bytes(b"png")
    client = TestClient(module.app)

    submit = client.post("/jobs", json={"input": _base_job_input()})
    assert submit.status_code == 200
    assert submit.json()["progress_url"].endswith("/ws/jobs/" + submit.json()["job_id"])
    result = client.get(submit.json()["result_url"])

    payload = result.json()
    assert payload["provider"] == "modal"
    assert payload["face_detection_confidence"] == 0.61
    assert payload["artifacts"][0]["role"] == "base_image"
    assert payload["resume_checkpoint"]["stage"] == "base_render"
    assert payload["resume_checkpoint"]["intermediate_artifacts"][0]["role"] == "base_image"


def test_s1_image_runtime_face_detail_fails_on_incomplete_resume_state(tmp_path: Path, monkeypatch) -> None:
    module = _load_runtime_module(tmp_path, monkeypatch)
    monkeypatch.setattr(module, "_ensure_comfyui_running", lambda: None)
    monkeypatch.setattr(module, "_download_remote_file", lambda *_args, **_kwargs: "reference.png")
    _create_required_flux_assets(module)
    client = TestClient(module.app)

    submit = client.post(
        "/jobs",
        json={
            "input": _base_job_input(
                mode="face_detail",
                resume_checkpoint={
                    "workflow_id": "base-image-ipadapter-impact",
                    "workflow_version": "2026-03-31",
                    "base_model_id": "flux-schnell-v1",
                    "seed": 42,
                    "stage": "base_render",
                    "provider": "modal",
                    "provider_job_id": "prompt-1",
                    "successful_node_ids": ["save_base_image"],
                    "intermediate_artifacts": [],
                    "metadata_json": {"face_detection_confidence": 0.61},
                },
            )
        },
    )
    result = client.get(submit.json()["result_url"])

    assert result.json()["error_code"] == "RESUME_STATE_INCOMPLETE"


def test_modal_runtime_provider_can_consume_s1_image_runtime_locally(tmp_path: Path, monkeypatch) -> None:
    module = _load_runtime_module(tmp_path, monkeypatch)
    monkeypatch.setattr(module, "_ensure_comfyui_running", lambda: None)
    monkeypatch.setattr(module, "_download_remote_file", lambda *_args, **_kwargs: "reference.png")
    monkeypatch.setattr(module, "_submit_prompt", lambda *_args, **_kwargs: "prompt-1")
    monkeypatch.setattr(
        module,
        "_poll_history",
        lambda _prompt_id: {
            "outputs": {
                "save_base_image": {
                    "images": [{"filename": "base.png", "subfolder": "vb", "type": "output"}],
                },
                "face_detector": {"metrics": {"bbox_confidence": 0.84}},
            }
        },
    )
    _create_required_flux_assets(module)
    (Path(module.COMFYUI_OUTPUT_DIR) / "vb").mkdir(parents=True, exist_ok=True)
    (Path(module.COMFYUI_OUTPUT_DIR) / "vb" / "base.png").write_bytes(b"png")
    client = TestClient(module.app)

    def fake_post(url: str, payload: dict, timeout_seconds: int, headers: dict[str, str] | None = None) -> dict:
        response = client.post(urlparse(url).path, json=payload)
        assert response.status_code == 200, response.text
        return response.json()

    def fake_get(url: str, timeout_seconds: int, headers: dict[str, str] | None = None) -> dict:
        response = client.get(urlparse(url).path)
        assert response.status_code == 200, response.text
        return response.json()

    monkeypatch.setattr("vixenbliss_creator.runtime_providers.adapters._json_post", fake_post)
    monkeypatch.setattr("vixenbliss_creator.runtime_providers.adapters._json_get", fake_get)

    from vixenbliss_creator.runtime_providers import ModalRuntimeProviderClient, RuntimeProviderSettings, ServiceRuntime

    settings = RuntimeProviderSettings(modal_endpoint_s1_image="http://testserver", provider_poll_interval_seconds=0)
    runtime_client = ModalRuntimeProviderClient(settings)

    handle = runtime_client.submit_job(ServiceRuntime.S1_IMAGE, _base_job_input())
    result = runtime_client.fetch_result(handle)

    assert result["provider"] == "modal"
    assert result["runtime_stage"] == "identity_image"
    assert result["artifacts"][0]["role"] == "base_image"
