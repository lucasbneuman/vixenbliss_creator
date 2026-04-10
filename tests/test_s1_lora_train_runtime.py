from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from uuid import uuid4

import pytest


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PATH = ROOT / "infra" / "s1-lora-train" / "runtime" / "app.py"


def _load_runtime_module(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> object:
    monkeypatch.setenv("SERVICE_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    spec = importlib.util.spec_from_file_location("test_s1_lora_train_runtime_module", RUNTIME_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["test_s1_lora_train_runtime_module"] = module
    spec.loader.exec_module(module)
    return module


def test_lora_runtime_blocks_training_when_identity_is_not_ready(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_runtime_module(tmp_path, monkeypatch)
    identity_id = str(uuid4())
    module._directus_client = type(
        "FakeClient",
        (),
        {
            "list_items": lambda self, collection, params=None: [
                {"avatar_id": identity_id, "dataset_status": "rejected", "pipeline_state": "base_images_registered"}
            ],
            "read_item": lambda self, collection, item_id: None,
        },
    )()

    with pytest.raises(ValueError, match="dataset_status=ready"):
        module._processor(
            {
                "identity_id": identity_id,
                "dataset_package_path": f"artifacts/{identity_id}/dataset.zip",
                "base_model_id": "flux-schnell-v1",
            }
        )


def test_lora_runtime_allows_training_when_identity_is_ready(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_runtime_module(tmp_path, monkeypatch)
    identity_id = str(uuid4())
    module._directus_client = type(
        "FakeClient",
        (),
        {
            "list_items": lambda self, collection, params=None: [
                {"avatar_id": identity_id, "dataset_status": "ready", "pipeline_state": "dataset_ready"}
            ],
            "read_item": lambda self, collection, item_id: None,
        },
    )()

    result = module._processor(
        {
            "identity_id": identity_id,
            "dataset_package_path": f"artifacts/{identity_id}/dataset.zip",
            "base_model_id": "flux-schnell-v1",
        }
    )

    assert result["training_manifest"]["identity_id"] == identity_id
