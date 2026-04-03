from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "infra" / "s1-image"
RUNTIME = BUNDLE / "runtime"


def test_s1_image_bundle_contains_expected_runtime_files() -> None:
    expected = [
        BUNDLE / "README.md",
        RUNTIME / "Dockerfile",
        RUNTIME / "app.py",
        RUNTIME / "requirements.txt",
        RUNTIME / "config" / "node-map.example.json",
        RUNTIME / "workflows" / "base-image-ipadapter-impact.json",
        RUNTIME / "scripts" / "bootstrap.sh",
        RUNTIME / "scripts" / "download_models.sh",
        RUNTIME / "scripts" / "entrypoint.sh",
        RUNTIME / "scripts" / "healthcheck.sh",
        BUNDLE / "providers" / "modal" / "app.py",
    ]

    for path in expected:
        assert path.exists(), f"missing deployable artifact: {path}"


def test_s1_image_bundle_workflow_keeps_dev8_nodes() -> None:
    workflow = json.loads((RUNTIME / "workflows" / "base-image-ipadapter-impact.json").read_text(encoding="utf-8"))

    assert workflow["workflow_id"] == "base-image-ipadapter-impact"
    assert workflow["vb_meta"]["logical_nodes"]["ip_adapter"] == "ip_adapter_apply"
    assert workflow["vb_meta"]["logical_nodes"]["face_detector"] == "face_detector"
    assert workflow["vb_meta"]["logical_nodes"]["face_detailer"] == "face_detailer"


def test_s1_image_bundle_download_script_prefers_neutral_model_cache() -> None:
    script = (RUNTIME / "scripts" / "download_models.sh").read_text(encoding="utf-8")

    assert 'MODEL_CACHE_ROOT="${MODEL_CACHE_ROOT:-${RUNPOD_MODELS_ROOT:-${RUNPOD_VOLUME_PATH:-/cache/models}}}"' in script
    assert "link_or_copy_from_cache" in script
    assert 'COMFYUI_IP_ADAPTER_ASSET_NAME="$(resolve_ip_adapter_asset_name "${COMFYUI_IP_ADAPTER_MODEL}")"' in script
    assert "MODEL_CACHE_IPADAPTER_FLUX_PATH" in script


def test_s1_image_modal_wrapper_uses_volume_backed_cache() -> None:
    modal_app = (BUNDLE / "providers" / "modal" / "app.py").read_text(encoding="utf-8")

    assert 'modal.Volume.from_name("vixenbliss-s1-image-model-cache", create_if_missing=True)' in modal_app
    assert 'modal.Image.from_dockerfile(' in modal_app
    assert '"MODEL_CACHE_ROOT": "/cache/models"' in modal_app
    assert 'volumes={"/cache/models": model_cache_volume}' in modal_app
    assert "def run_s1_image_job(payload: dict) -> dict:" in modal_app
    assert "@modal.asgi_app()" not in modal_app
