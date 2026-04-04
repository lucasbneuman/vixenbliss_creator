from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib import request

import pytest

from vixenbliss_creator.s1_control import DirectusControlPlaneClient, DirectusSchemaManager, S1ControlSettings


class FakeSchemaManager(DirectusSchemaManager):
    def __init__(self) -> None:
        super().__init__(S1ControlSettings(directus_base_url="https://directus.example.com", directus_token="secret"))
        self.collections: dict[str, dict[str, Any]] = {}

    def _list_collections(self) -> list[dict[str, Any]]:
        return [{"collection": name} for name in self.collections]

    def _list_fields(self, collection: str) -> list[dict[str, Any]]:
        fields = self.collections.get(collection, {}).get("fields", set())
        return [{"field": name} for name in fields]

    def _create_collection(self, collection: str, meta: dict[str, Any]) -> None:
        self.collections[collection] = {"meta": meta, "fields": set()}

    def _create_field(self, collection: str, field_name: str, field_type: str) -> None:
        self.collections.setdefault(collection, {"meta": {}, "fields": set()})
        self.collections[collection]["fields"].add(field_name)


def test_settings_require_directus_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DIRECTUS_BASE_URL", raising=False)
    monkeypatch.delenv("DIRECTUS_API_TOKEN", raising=False)

    with pytest.raises(ValueError, match="DIRECTUS_BASE_URL"):
        S1ControlSettings.from_env()


def test_settings_read_directus_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DIRECTUS_BASE_URL", "https://directus.example.com/")
    monkeypatch.setenv("DIRECTUS_API_TOKEN", "secret")
    monkeypatch.setenv("DIRECTUS_TIMEOUT_SECONDS", "45")

    settings = S1ControlSettings.from_env()

    assert settings.directus_base_url == "https://directus.example.com"
    assert settings.directus_token == "secret"
    assert settings.directus_timeout_seconds == 45


def test_schema_manager_creates_expected_s1_collections() -> None:
    manager = FakeSchemaManager()

    created = manager.ensure_schema()

    assert "s1_identities" in created
    assert "s1_prompt_requests" in created
    assert "s1_generation_runs" in created
    assert "s1_artifacts" in created
    assert "s1_model_assets" in created
    assert "s1_events" in created
    assert "display_name" in manager.collections["s1_identities"]["fields"]
    assert "metadata_json" in manager.collections["s1_artifacts"]["fields"]
    assert "identity_schema_version" in manager.collections["s1_identities"]["fields"]
    assert "alias" in manager.collections["s1_identities"]["fields"]
    assert "technical_sheet_json" in manager.collections["s1_identities"]["fields"]
    assert "base_model_id" in manager.collections["s1_identities"]["fields"]
    assert "created_at" in manager.collections["s1_identities"]["fields"]
    assert "latest_seed_bundle_json" in manager.collections["s1_identities"]["fields"]
    assert "latest_base_image_file_id" in manager.collections["s1_identities"]["fields"]
    assert "latest_dataset_manifest_json" in manager.collections["s1_identities"]["fields"]
    assert "latest_dataset_package_file_id" in manager.collections["s1_identities"]["fields"]


def test_directus_client_can_upload_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    uploaded: dict[str, Any] = {}
    file_path = tmp_path / "dataset-manifest.json"
    file_path.write_text('{"ok":true}', encoding="utf-8")

    class FakeResponse:
        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps({"data": {"id": "file-123", "storage": "directus", "filename_download": "dataset-manifest.json"}}).encode(
                "utf-8"
            )

    def fake_urlopen(req: request.Request, timeout: int):
        uploaded["url"] = req.full_url
        uploaded["content_type"] = req.headers["Content-type"]
        uploaded["body"] = req.data
        return FakeResponse()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    client = DirectusControlPlaneClient(
        S1ControlSettings(directus_base_url="https://directus.example.com", directus_token="secret")
    )

    payload = client.upload_file(file_path, content_type="application/json", title="dataset manifest")

    assert uploaded["url"] == "https://directus.example.com/files"
    assert "multipart/form-data" in uploaded["content_type"]
    assert b'name="storage"' in uploaded["body"]
    assert b'name="file"; filename="dataset-manifest.json"' in uploaded["body"]
    assert payload["id"] == "file-123"
    assert payload["asset_url"] == "https://directus.example.com/assets/file-123"
