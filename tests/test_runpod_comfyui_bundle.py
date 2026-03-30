from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "infra" / "runpod-comfyui"


def test_runpod_comfyui_bundle_contains_expected_files() -> None:
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
    assert workflow["workflow_version"] == "2026-03-30"
    assert workflow["vb_meta"]["logical_nodes"]["ip_adapter"] == "ip_adapter_apply"
    assert workflow["vb_meta"]["logical_nodes"]["face_detector"] == "face_detector"
    assert workflow["vb_meta"]["logical_nodes"]["face_detailer"] == "face_detailer"
    assert "save_base_image" in workflow
    assert "save_final_image" in workflow


def test_bundle_runtime_scripts_do_not_clone_repositories_at_startup() -> None:
    bootstrap = (BUNDLE / "scripts" / "bootstrap.sh").read_text(encoding="utf-8")
    entrypoint = (BUNDLE / "scripts" / "entrypoint.sh").read_text(encoding="utf-8")
    dockerfile = (BUNDLE / "Dockerfile").read_text(encoding="utf-8")
    handler = (BUNDLE / "handler.py").read_text(encoding="utf-8")

    assert "git clone" not in bootstrap
    assert "git clone" not in entrypoint
    assert "git clone" in dockerfile
    assert "runpod.serverless.start" in handler
    assert 'ENTRYPOINT ["/usr/bin/tini", "--", "python", "/opt/runpod-comfyui/handler.py"]' in dockerfile
