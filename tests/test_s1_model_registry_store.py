from __future__ import annotations

from typing import Any

from vixenbliss_creator.s1_control import DirectusModelRegistryStore, default_model_catalog


class FakeControlPlane:
    def __init__(self) -> None:
        self.store: dict[str, list[dict[str, Any]]] = {}

    def create_item(self, collection: str, payload: dict[str, Any]) -> dict[str, Any]:
        item = dict(payload)
        self.store.setdefault(collection, []).append(item)
        return item

    def update_item(self, collection: str, item_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        for item in self.store.get(collection, []):
            if str(item["id"]) == str(item_id):
                item.update(payload)
                return item
        raise KeyError(item_id)

    def read_item(self, collection: str, item_id: str) -> dict[str, Any]:
        for item in self.store.get(collection, []):
            if str(item["id"]) == str(item_id):
                return item
        raise KeyError(item_id)

    def list_items(self, collection: str, *, params: dict[str, str] | None = None) -> list[dict[str, Any]]:
        return list(self.store.get(collection, []))


def test_model_registry_store_seeds_default_catalog() -> None:
    store = DirectusModelRegistryStore(client=FakeControlPlane())

    seeded = store.seed_default_catalog()

    assert len(seeded) == 2
    assert {model.model_role for model in seeded} == {"base_model", "video_placeholder"}
    assert store.find_active_base_model("flux-schnell-v1") is not None


def test_default_catalog_declares_compatibilities_and_version_policy() -> None:
    catalog = default_model_catalog()
    base_model = next(model for model in catalog if model.model_role == "base_model")
    video_placeholder = next(model for model in catalog if model.model_role == "video_placeholder")

    assert base_model.metadata_json["adapters_supported"] == ["lora", "ip_adapter", "controlnet"]
    assert base_model.metadata_json["pipelines_supported"] == ["s1_image", "s2_image"]
    assert video_placeholder.metadata_json["video_support"] == "planned"
    assert "version_policy" in base_model.metadata_json
