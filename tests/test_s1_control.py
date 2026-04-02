from __future__ import annotations

from typing import Any

import pytest

from vixenbliss_creator.s1_control import DirectusSchemaManager, S1ControlSettings


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
