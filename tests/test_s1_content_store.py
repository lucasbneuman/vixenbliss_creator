from __future__ import annotations

from typing import Any
from uuid import uuid4

from vixenbliss_creator.contracts.content import Content
from vixenbliss_creator.s1_control import DirectusContentStore


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
        return list(self.store.get(collection, []))


def build_content(identity_id: str = "identity-123") -> Content:
    return Content.model_validate(
        {
            "id": str(uuid4()),
            "identity_id": identity_id,
            "content_mode": "image",
            "generation_status": "generated",
            "qa_status": "not_reviewed",
            "job_id": "job-123",
            "primary_artifact_id": "artifact-123",
            "related_artifact_ids": ["artifact-123"],
            "base_model_id": "flux-schnell-v1",
            "model_version_used": "2026-04-08",
            "provider": "modal",
            "workflow_id": "content-image-flux-lora",
            "prompt": "editorial portrait with dramatic lighting",
            "negative_prompt": "bad anatomy, low quality",
            "seed": 99,
            "metadata_json": {"artifact_role": "generated_image"},
        }
    )


def test_content_store_roundtrips_content() -> None:
    store = DirectusContentStore(client=FakeControlPlane())
    content = build_content()

    store.upsert_content(content)
    restored = store.get_content(content.id)

    assert restored is not None
    assert restored.id == content.id
    assert restored.workflow_id == "content-image-flux-lora"
    assert restored.related_artifact_ids == ["artifact-123"]


def test_content_store_updates_existing_row_in_place() -> None:
    fake = FakeControlPlane()
    store = DirectusContentStore(client=fake)
    content = build_content()

    store.upsert_content(content)
    updated = content.model_copy(update={"qa_status": "approved", "metadata_json": {"reviewed_by": "qa"}})
    store.upsert_content(updated)

    assert len(fake.store["content_catalog"]) == 1
    assert fake.store["content_catalog"][0]["qa_status"] == "approved"
    assert fake.store["content_catalog"][0]["metadata_json"]["reviewed_by"] == "qa"


def test_content_store_lists_by_identity() -> None:
    store = DirectusContentStore(client=FakeControlPlane())
    first = build_content(identity_id="identity-a")
    second = build_content(identity_id="identity-b")

    store.upsert_content(first)
    store.upsert_content(second)

    contents = store.list_contents(identity_id="identity-a")

    assert [item.identity_id for item in contents] == ["identity-a"]


def test_content_store_roundtrips_video_request_fields() -> None:
    store = DirectusContentStore(client=FakeControlPlane())
    content = Content.model_validate(
        {
            "id": str(uuid4()),
            "identity_id": "identity-video-123",
            "content_mode": "video",
            "video_generation_mode": "image_to_video",
            "generation_status": "pending",
            "qa_status": "not_reviewed",
            "base_model_id": "future-video-placeholder-v1",
            "model_version_used": "future-video-placeholder-v1",
            "provider": "modal",
            "workflow_id": "video-image-to-video-prep",
            "prompt": "fashion clip with subtle camera drift",
            "negative_prompt": "low quality, temporal drift",
            "source_artifact_id": "artifact-source-123",
            "metadata_json": {"video_backend_hint": "wan2.2"},
        }
    )

    store.upsert_content(content)
    restored = store.get_content(content.id)

    assert restored is not None
    assert restored.video_generation_mode == "image_to_video"
    assert restored.source_artifact_id == "artifact-source-123"
