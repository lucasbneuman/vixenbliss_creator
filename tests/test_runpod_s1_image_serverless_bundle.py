from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "infra" / "runpod-s1-image-serverless"


def test_runpod_s1_image_serverless_bundle_contains_expected_files() -> None:
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


def test_s1_bundle_env_example_uses_identity_endpoint_and_plus_face_alias() -> None:
    env_example = (BUNDLE / ".env.example").read_text(encoding="utf-8")

    assert "RUNPOD_ENDPOINT_IMAGE_IDENTITY=CHANGEME" in env_example
    assert "RUNPOD_ENDPOINT_IMAGE_CONTENT" not in env_example
    assert "RUNPOD_ENDPOINT_LORA_TRAIN" not in env_example
    assert "RUNPOD_ENDPOINT_VIDEO_GEN" not in env_example
    assert "COMFYUI_WORKFLOW_IDENTITY_ID=base-image-ipadapter-impact" in env_example
    assert "COMFYUI_IP_ADAPTER_MODEL=plus_face" in env_example
    assert "RUNPOD_MODELS_ROOT=/runpod-volume/models" in env_example
    assert "RUNPOD_FLUX_DIFFUSION_MODEL_PATH=/runpod-volume/models/diffusion_models/flux1-schnell.safetensors" in env_example


def test_s1_bundle_runtime_scripts_point_to_s1_paths() -> None:
    bootstrap = (BUNDLE / "scripts" / "bootstrap.sh").read_text(encoding="utf-8")
    entrypoint = (BUNDLE / "scripts" / "entrypoint.sh").read_text(encoding="utf-8")
    dockerfile = (BUNDLE / "Dockerfile").read_text(encoding="utf-8")

    assert "/opt/runpod-s1-image-serverless" in bootstrap
    assert "/opt/runpod-s1-image-serverless" in entrypoint
    assert "/opt/runpod-s1-image-serverless" in dockerfile
    assert 'ENTRYPOINT ["/usr/bin/tini", "--", "python", "/opt/runpod-s1-image-serverless/handler.py"]' in dockerfile
    assert "vixenbliss-runpod-s1-image-serverless" in (
        ROOT / ".github" / "workflows" / "runpod-s1-image-serverless-image.yml"
    ).read_text(encoding="utf-8")


def test_s1_bundle_dockerfile_pins_production_runtime_versions() -> None:
    dockerfile = (BUNDLE / "Dockerfile").read_text(encoding="utf-8")

    assert "FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04" in dockerfile
    assert "ARG COMFYUI_REF=ebf6b52e322664af91fcdc8b8848d31d5fb98f66" in dockerfile
    assert "ARG COMFYUI_IPADAPTER_REF=eef22b6875ddaf10f13657248b8123d6bdec2014" in dockerfile
    assert "ARG COMFYUI_IMPACT_REF=6a517ebe06fea2b74fc41b3bd089c0d7173eeced" in dockerfile
    assert "ARG TORCH_VERSION=2.6.0" in dockerfile
    assert "ARG TORCH_INDEX_URL=https://download.pytorch.org/whl/cu124" in dockerfile
    assert "COMFYUI_REF=master" not in dockerfile


def test_s1_bundle_download_script_prefers_runpod_network_volume() -> None:
    script = (BUNDLE / "scripts" / "download_models.sh").read_text(encoding="utf-8")

    assert 'RUNPOD_MODELS_ROOT="${RUNPOD_MODELS_ROOT:-${RUNPOD_VOLUME_PATH}/models}"' in script
    assert "link_or_copy_from_volume" in script
    assert "RUNPOD_FLUX_DIFFUSION_MODEL_PATH" in script


def test_s1_bundle_workflow_keeps_dev8_nodes() -> None:
    workflow = json.loads((BUNDLE / "workflows" / "base-image-ipadapter-impact.json").read_text(encoding="utf-8"))

    assert workflow["workflow_id"] == "base-image-ipadapter-impact"
    assert workflow["vb_meta"]["logical_nodes"]["ip_adapter"] == "ip_adapter_apply"
    assert workflow["vb_meta"]["logical_nodes"]["face_detector"] == "face_detector"
    assert workflow["vb_meta"]["logical_nodes"]["face_detailer"] == "face_detailer"
