from __future__ import annotations

import importlib.util
import sys
import types
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HANDLER_PATH = ROOT / "infra" / "runpod-visual-serverless" / "handler.py"


def load_handler_module(tmp_path: Path, monkeypatch) -> types.ModuleType:
    comfy_home = tmp_path / "comfyui"
    models_dir = comfy_home / "models"
    workflow_dir = tmp_path / "bundle" / "workflows"
    workflow_dir.mkdir(parents=True, exist_ok=True)
    (workflow_dir / "base-image-ipadapter-impact.json").write_text(
        (ROOT / "infra" / "runpod-visual-serverless" / "workflows" / "base-image-ipadapter-impact.json").read_text(
            encoding="utf-8"
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("COMFYUI_HOME", str(comfy_home))
    monkeypatch.setenv("COMFYUI_MODELS_DIR", str(models_dir))
    monkeypatch.setenv("COMFYUI_USER_DIR", str(comfy_home / "user" / "default"))
    monkeypatch.setenv("COMFYUI_INPUT_DIR", str(comfy_home / "input"))
    monkeypatch.setitem(sys.modules, "runpod", types.SimpleNamespace(serverless=types.SimpleNamespace(start=lambda *_args, **_kwargs: None)))

    module_name = f"test_runpod_visual_handler_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, HANDLER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    module.WORKFLOW_TEMPLATE = workflow_dir / "base-image-ipadapter-impact.json"
    return module


def create_required_flux_assets(module: types.ModuleType) -> None:
    for path in module._required_runtime_paths().values():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"stub")


def test_runtime_checks_detect_missing_flux_assets(tmp_path: Path, monkeypatch) -> None:
    module = load_handler_module(tmp_path, monkeypatch)

    checks = module._runtime_checks({})

    assert checks["flux_diffusion_model_present"] is False
    assert checks["flux_ae_present"] is False
    assert checks["flux_clip_l_present"] is False
    assert checks["flux_t5xxl_present"] is False
    assert checks["ip_adapter_present"] is False


def test_handler_reports_missing_flux_diffusion_model(tmp_path: Path, monkeypatch) -> None:
    module = load_handler_module(tmp_path, monkeypatch)
    monkeypatch.setattr(module, "_ensure_comfyui_running", lambda: None)

    for key, path in module._required_runtime_paths().items():
        if key == "flux_diffusion_model":
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"stub")

    payload = module.handler({"input": {"action": "generate", "mode": "base_render", "reference_face_image_url": "https://example.com/ref.png"}})

    assert payload["error_code"] == "COMFYUI_EXECUTION_FAILED"
    assert "missing flux_diffusion_model asset" in payload["error_message"]


def test_handler_reports_missing_flux_ae(tmp_path: Path, monkeypatch) -> None:
    module = load_handler_module(tmp_path, monkeypatch)
    monkeypatch.setattr(module, "_ensure_comfyui_running", lambda: None)

    for key, path in module._required_runtime_paths().items():
        if key == "flux_ae":
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"stub")

    payload = module.handler({"input": {"action": "generate", "mode": "base_render", "reference_face_image_url": "https://example.com/ref.png"}})

    assert payload["error_code"] == "COMFYUI_EXECUTION_FAILED"
    assert "missing flux_ae asset" in payload["error_message"]


def test_handler_reports_missing_encoder_asset(tmp_path: Path, monkeypatch) -> None:
    module = load_handler_module(tmp_path, monkeypatch)
    monkeypatch.setattr(module, "_ensure_comfyui_running", lambda: None)

    for key, path in module._required_runtime_paths().items():
        if key == "flux_t5xxl":
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"stub")

    payload = module.handler({"input": {"action": "generate", "mode": "base_render", "reference_face_image_url": "https://example.com/ref.png"}})

    assert payload["error_code"] == "COMFYUI_EXECUTION_FAILED"
    assert "missing flux_t5xxl asset" in payload["error_message"]


def test_handler_reports_unresolvable_reference_image(tmp_path: Path, monkeypatch) -> None:
    module = load_handler_module(tmp_path, monkeypatch)
    monkeypatch.setattr(module, "_ensure_comfyui_running", lambda: None)
    create_required_flux_assets(module)

    payload = module.handler({"input": {"action": "generate", "mode": "base_render"}})

    assert payload["error_code"] == "REFERENCE_IMAGE_NOT_FOUND"
    assert "reference_face_image_url could not be resolved" in payload["error_message"]
