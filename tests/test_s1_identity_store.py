from __future__ import annotations

from typing import Any

from vixenbliss_creator.agentic.runner import run_agentic_brain
from vixenbliss_creator.s1_control import DirectusIdentityStore, build_identity_from_graph_state


class FakeControlPlane:
    def __init__(self) -> None:
        self.store: dict[str, list[dict[str, Any]]] = {}
        self.sequence = 1

    def create_item(self, collection: str, payload: dict[str, Any]) -> dict[str, Any]:
        item = {"id": self.sequence, **payload}
        self.sequence += 1
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
        items = list(self.store.get(collection, []))
        if not params:
            return items
        avatar_eq = params.get("filter[avatar_id][_eq]")
        if avatar_eq is not None:
            items = [item for item in items if str(item.get("avatar_id")) == str(avatar_eq)]
        limit = params.get("limit")
        if limit is not None:
            items = items[: int(limit)]
        return items


def test_identity_store_persists_and_reads_identity_created_payload() -> None:
    state = run_agentic_brain("Creá un avatar nuevo para lifestyle premium")
    identity = build_identity_from_graph_state(state)
    store = DirectusIdentityStore(client=FakeControlPlane())

    store.upsert_identity(identity, created_by="codex", source_prompt_request_id="101")
    restored = store.get_identity(identity.id)

    assert restored is not None
    assert restored.id == identity.id
    assert restored.pipeline_state == "identity_created"
    assert restored.base_model_id == "flux-schnell-v1"
    assert restored.technical_sheet_json.identity_metadata.avatar_id == str(identity.id)
    row = store.client.store["s1_identities"][0]
    assert row["display_name"] == "Velvet Ember"
    assert row["category"] == "lifestyle_premium"
    assert row["style"] == "premium"
    assert row["created_by"] == "codex"
    assert row["source_prompt_request_id"] == "101"


def test_identity_store_updates_existing_row_in_place() -> None:
    state = run_agentic_brain("Creá un avatar nuevo para lifestyle premium")
    identity = build_identity_from_graph_state(state)
    fake = FakeControlPlane()
    store = DirectusIdentityStore(client=fake)

    store.upsert_identity(identity, created_by="codex")
    updated_identity = build_identity_from_graph_state(
        state,
        identity_id=identity.id,
        base_model_id="flux-schnell-v1",
        reference_face_image_url="https://example.com/reference.png",
    )
    store.upsert_identity(updated_identity, created_by="codex")

    assert len(fake.store["s1_identities"]) == 1
    row = fake.store["s1_identities"][0]
    assert row["reference_face_image_url"] == "https://example.com/reference.png"
    assert row["latest_base_model_id"] == "flux-schnell-v1"


def test_identity_store_returns_none_for_unknown_identity() -> None:
    store = DirectusIdentityStore(client=FakeControlPlane())

    assert store.get_identity("missing-identity") is None
