from __future__ import annotations

from vixenbliss_creator.s1_control.bootstrap import bootstrap_directus_schema


def test_bootstrap_uses_schema_manager(monkeypatch) -> None:
    created_collections: list[str] = []

    class FakeManager:
        def __init__(self, settings) -> None:
            self.settings = settings

        def ensure_schema(self) -> list[str]:
            created_collections.extend(["s1_identities", "s1_generation_runs"])
            return ["s1_identities", "s1_generation_runs"]

    class FakeSettings:
        @classmethod
        def from_env(cls):
            return object()

    monkeypatch.setattr("vixenbliss_creator.s1_control.bootstrap.S1ControlSettings", FakeSettings)
    monkeypatch.setattr("vixenbliss_creator.s1_control.bootstrap.DirectusSchemaManager", FakeManager)

    created = bootstrap_directus_schema()

    assert created == ["s1_identities", "s1_generation_runs"]
    assert created_collections == ["s1_identities", "s1_generation_runs"]


def test_directus_schema_declares_content_catalog() -> None:
    from vixenbliss_creator.s1_control import S1_DIRECTUS_SCHEMA

    assert "content_catalog" in S1_DIRECTUS_SCHEMA
    fields = {field["field"] for field in S1_DIRECTUS_SCHEMA["content_catalog"]["fields"]}
    assert {"content_id", "content_mode", "generation_status", "qa_status", "workflow_id"} <= fields
