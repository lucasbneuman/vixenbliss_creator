from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "infra" / "runpod-visual-serverless"

def test_runpod_visual_serverless_bundle_contains_expected_files() -> None:
    expected = [
        BUNDLE / "Dockerfile",
        BUNDLE / ".env.example",
        BUNDLE / "handler.py",
        BUNDLE / "README.md",
        BUNDLE / "requirements.txt",
        BUNDLE / "config" / "node-map.example.json",
        BUNDLE / "workflows" / "base-image-ipadapter-impact.json",
        BUNDLE / "scripts" / "bootstrap.sh",
        BUNDLE / "scripts" / "download_models.sh",
        BUNDLE / "scripts" / "entrypoint.sh",
        BUNDLE / "scripts" / "healthcheck.sh",
    ]

    for path in expected:
        assert path.exists(), f"missing deployable artifact: {path}"


def test_node_map_declares_expected_logical_nodes() -> None:
    payload = json.loads((BUNDLE / "config" / "node-map.example.json").read_text(encoding="utf-8"))

    assert payload["workflow_id"] == "base-image-ipadapter-impact"
    assert set(payload["logical_nodes"]) == {"ip_adapter", "face_detector", "face_detailer"}


def test_workflow_json_exposes_expected_node_ids() -> None:
    workflow = json.loads((BUNDLE / "workflows" / "base-image-ipadapter-impact.json").read_text(encoding="utf-8"))

    assert workflow["workflow_id"] == "base-image-ipadapter-impact"
    assert workflow["workflow_version"] == "2026-03-31"
    assert workflow["vb_meta"]["model_family"] == "flux"
    assert workflow["vb_meta"]["logical_nodes"]["ip_adapter"] == "ip_adapter_apply"
    assert workflow["vb_meta"]["logical_nodes"]["face_detector"] == "face_detector"
    assert workflow["vb_meta"]["logical_nodes"]["face_detailer"] == "face_detailer"
    assert "save_base_image" in workflow
    assert "save_final_image" in workflow


def test_bundle_env_example_uses_explicit_flux_assets() -> None:
    env_example = (BUNDLE / ".env.example").read_text(encoding="utf-8")

    assert "COMFYUI_FLUX_DIFFUSION_MODEL_NAME=flux1-schnell.safetensors" in env_example
    assert "COMFYUI_FLUX_AE_NAME=ae.safetensors" in env_example
    assert "COMFYUI_FLUX_CLIP_L_NAME=clip_l.safetensors" in env_example
    assert "COMFYUI_FLUX_T5XXL_NAME=t5xxl_fp8_e4m3fn.safetensors" in env_example
    assert "FLUX_DIFFUSION_MODEL_URL=CHANGEME" in env_example
    assert "FLUX_AE_URL=CHANGEME" in env_example
    assert "FLUX_CLIP_L_URL=CHANGEME" in env_example
    assert "FLUX_T5XXL_URL=CHANGEME" in env_example
    assert "IPADAPTER_FLUX_URL=CHANGEME" in env_example


def test_bundle_runtime_scripts_do_not_clone_repositories_at_startup() -> None:
    bootstrap = (BUNDLE / "scripts" / "bootstrap.sh").read_text(encoding="utf-8")
    entrypoint = (BUNDLE / "scripts" / "entrypoint.sh").read_text(encoding="utf-8")
    dockerfile = (BUNDLE / "Dockerfile").read_text(encoding="utf-8")
    handler = (BUNDLE / "handler.py").read_text(encoding="utf-8")

    assert "git clone" not in bootstrap
    assert "git clone" not in entrypoint
    assert "git clone" in dockerfile
    assert "ComfyUI-IPAdapter-Flux" in dockerfile
    assert "runpod.serverless.start" in handler
    assert 'ENTRYPOINT ["/usr/bin/tini", "--", "python", "/opt/runpod-visual-serverless/handler.py"]' in dockerfile
