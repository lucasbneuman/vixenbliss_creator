from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from fastapi.testclient import TestClient

from .bootstrap import bootstrap_directus_schema
from .config import S1ControlSettings
from .directus import DirectusControlPlaneClient
from .support import load_local_env, tiny_png_bytes


REPO_ROOT = Path(__file__).resolve().parents[3]
RUNTIME_PATH = REPO_ROOT / "infra" / "s1-image" / "runtime" / "app.py"


def _load_runtime_module() -> object:
    spec = importlib.util.spec_from_file_location("vixenbliss_s1_image_live_smoke_runtime", RUNTIME_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["vixenbliss_s1_image_live_smoke_runtime"] = module
    spec.loader.exec_module(module)
    return module


def _create_required_assets(module: object) -> None:
    for path in module._required_runtime_paths().values():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"stub")


def _job_input(identity_id: str) -> dict[str, object]:
    return {
        "action": "generate",
        "mode": "base_render",
        "workflow_id": "base-image-ipadapter-impact",
        "workflow_version": "2026-04-03",
        "base_model_id": "flux-schnell-v1",
        "runtime_stage": "identity_image",
        "prompt": "editorial portrait of a synthetic premium performer",
        "negative_prompt": "low quality, anatomy drift, extra limbs, text, watermark",
        "seed": 42,
        "width": 1024,
        "height": 1024,
        "reference_face_image_url": "https://example.com/reference.png",
        "ip_adapter": {"enabled": True, "model_name": "plus_face", "weight": 0.9},
        "face_detailer": {"enabled": True, "confidence_threshold": 0.8, "inpaint_strength": 0.35},
        "metadata": {"identity_id": identity_id, "character_id": identity_id, "autopromote": False, "samples_target": 8},
    }


def run_live_smoke() -> dict[str, object]:
    load_local_env()
    created_collections = bootstrap_directus_schema()
    settings = S1ControlSettings.from_env()
    client = DirectusControlPlaneClient(settings)
    identity_id = str(uuid4())

    with TemporaryDirectory(prefix="vb-s1-directus-smoke-") as temp_dir:
        temp_root = Path(temp_dir)
        comfy_home = temp_root / "comfyui"
        output_dir = comfy_home / "output" / "vb"
        output_dir.mkdir(parents=True, exist_ok=True)

        os.environ["COMFYUI_HOME"] = str(comfy_home)
        os.environ["COMFYUI_CUSTOM_NODES_DIR"] = str(comfy_home / "custom_nodes")
        os.environ["COMFYUI_MODELS_DIR"] = str(comfy_home / "models")
        os.environ["COMFYUI_USER_DIR"] = str(comfy_home / "user" / "default")
        os.environ["COMFYUI_INPUT_DIR"] = str(comfy_home / "input")
        os.environ["MODEL_CACHE_ROOT"] = str(temp_root / "model-cache")
        os.environ["SERVICE_ARTIFACT_ROOT"] = str(temp_root / "artifacts")
        os.environ["COMFYUI_WORKFLOW_IDENTITY_ID"] = "base-image-ipadapter-impact"
        os.environ["COMFYUI_WORKFLOW_IDENTITY_VERSION"] = "2026-03-31"

        module = _load_runtime_module()
        module._ensure_comfyui_running = lambda **_kwargs: None
        module._download_remote_file = lambda *_args, **_kwargs: "reference.png"
        module._submit_prompt = lambda *_args, **_kwargs: "prompt-live-smoke"
        module._poll_history = lambda _prompt_id: {
            "outputs": {
                "save_base_image": {
                    "images": [{"filename": "base.png", "subfolder": "vb", "type": "output"}],
                },
                "face_detector": {"metrics": {"bbox_confidence": 0.93}},
            }
        }
        _create_required_assets(module)
        (output_dir / "base.png").write_bytes(tiny_png_bytes())
        api_client = TestClient(module.app)

        response = api_client.post("/jobs", json={"input": _job_input(identity_id)})
        response.raise_for_status()
        payload = response.json()["output"]
        run_id = str(payload["metadata"]["directus_run_id"])

        run = client.read_item("s1_generation_runs", run_id)
        artifacts = client.list_items("s1_artifacts", params={"filter[run_id][_eq]": run_id})
        events = client.list_items("s1_events", params={"filter[run_id][_eq]": run_id})
        identities = client.list_items("s1_identities", params={"filter[avatar_id][_eq]": identity_id, "limit": "1"})
        identity = identities[0] if identities else None

        return {
            "created_collections": created_collections,
            "identity_id": identity_id,
            "run_id": run_id,
            "job_id": response.json()["job_id"],
            "dataset_storage_mode": payload["metadata"].get("dataset_storage_mode"),
            "persisted_artifacts": payload["metadata"].get("persisted_artifacts", []),
            "run": {
                "id": str(run["id"]),
                "status": run.get("status"),
                "provider": run.get("provider"),
            },
            "artifacts": [
                {
                    "id": str(item["id"]),
                    "role": item.get("role"),
                    "file": item.get("file"),
                    "uri": item.get("uri"),
                    "metadata_json": item.get("metadata_json"),
                }
                for item in artifacts
            ],
            "events": [
                {
                    "id": str(item["id"]),
                    "event_type": item.get("event_type"),
                    "message": item.get("message"),
                    "payload_json": item.get("payload_json"),
                }
                for item in events
            ],
            "identity_snapshot": {
                "id": str(identity["id"]) if identity else None,
                "avatar_id": identity.get("avatar_id") if identity else None,
                "last_run_id": identity.get("last_run_id") if identity else None,
                "latest_base_image_file_id": identity.get("latest_base_image_file_id") if identity else None,
                "latest_dataset_manifest_json": identity.get("latest_dataset_manifest_json") if identity else None,
                "latest_dataset_package_uri": identity.get("latest_dataset_package_uri") if identity else None,
                "latest_dataset_manifest_file_id": identity.get("latest_dataset_manifest_file_id") if identity else None,
                "latest_dataset_package_file_id": identity.get("latest_dataset_package_file_id") if identity else None,
            },
        }


if __name__ == "__main__":
    result = run_live_smoke()
    print(json.dumps(result, indent=2))
