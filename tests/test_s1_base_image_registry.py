from __future__ import annotations

from pathlib import Path
from typing import Any

from vixenbliss_creator.s1_control import S1BaseImageRegistry
from vixenbliss_creator.s1_control.support import tiny_png_bytes


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


def test_registry_registers_multiple_base_images_and_marks_primary(tmp_path: Path) -> None:
    fake = FakeControlPlane()
    fake.create_item("s1_identities", {"avatar_id": "42", "pipeline_state": "base_images_generated"})
    first = tmp_path / "base-1.png"
    second = tmp_path / "base-2.png"
    first.write_bytes(tiny_png_bytes())
    second.write_bytes(tiny_png_bytes())
    artifact_rows = [
        fake.create_item(
            "s1_artifacts",
            {
                "identity_id": "42",
                "run_id": "run-1",
                "role": "base_image",
                "file": "file-1",
                "uri": "https://directus.example.com/assets/file-1",
                "content_type": "image/png",
                "version": "2026-04-02",
                "metadata_json": {},
            },
        ),
        fake.create_item(
            "s1_artifacts",
            {
                "identity_id": "42",
                "run_id": "run-1",
                "role": "base_image",
                "file": "file-2",
                "uri": "https://directus.example.com/assets/file-2",
                "content_type": "image/png",
                "version": "2026-04-02",
                "metadata_json": {},
            },
        ),
    ]
    uploaded_artifacts = [
        {
            "artifact_type": "base_image",
            "storage_path": str(first),
            "content_type": "image/png",
            "directus_file_id": "file-1",
            "directus_asset_url": "https://directus.example.com/assets/file-1",
            "metadata_json": {"size_bytes": first.stat().st_size, "checksum_sha256": "a" * 64},
        },
        {
            "artifact_type": "base_image",
            "storage_path": str(second),
            "content_type": "image/png",
            "directus_file_id": "file-2",
            "directus_asset_url": "https://directus.example.com/assets/file-2",
            "metadata_json": {"size_bytes": second.stat().st_size, "checksum_sha256": "b" * 64},
        },
    ]

    result = S1BaseImageRegistry(client=fake).register(
        identity_id="42",
        run_id="run-1",
        source_job_id="job-123",
        result_payload={
            "workflow_id": "base-image-ipadapter-impact",
            "workflow_version": "2026-04-02",
            "base_model_id": "flux-schnell-v1",
        },
        runtime_metadata={
            "prompt": "portrait",
            "seed_bundle": {"portrait_seed": 11},
            "workflow_id": "base-image-ipadapter-impact",
            "workflow_version": "2026-04-02",
            "base_model_id": "flux-schnell-v1",
        },
        uploaded_artifacts=uploaded_artifacts,
        artifact_rows=artifact_rows,
    )

    assert result is not None
    assert len(result.registered_rows) == 2
    assert result.primary_row["file"] == "file-1"
    identity = fake.store["s1_identities"][0]
    assert identity["pipeline_state"] == "base_images_registered"
    assert identity["base_image_urls"] == [
        "https://directus.example.com/assets/file-1",
        "https://directus.example.com/assets/file-2",
    ]
    assert identity["reference_face_image_url"] == "https://directus.example.com/assets/file-1"
    assert identity["reference_face_image_id"] == "file-1"
    assert fake.store["s1_artifacts"][0]["metadata_json"]["source_job_id"] == "job-123"
    assert fake.store["s1_artifacts"][0]["metadata_json"]["is_primary_reference"] is True
    assert fake.store["s1_artifacts"][1]["metadata_json"]["is_primary_reference"] is False
    assert any(event["event_type"] == "base_images_registered" for event in fake.store["s1_events"])


def test_registry_fails_fast_when_checksum_is_missing_and_source_is_unrecoverable() -> None:
    fake = FakeControlPlane()
    fake.create_item("s1_identities", {"avatar_id": "42", "pipeline_state": "base_images_generated"})
    artifact_row = fake.create_item(
        "s1_artifacts",
        {
            "identity_id": "42",
            "run_id": "run-1",
            "role": "base_image",
            "file": "file-1",
            "uri": "https://directus.example.com/assets/file-1",
            "content_type": "image/png",
            "version": "2026-04-02",
            "metadata_json": {},
        },
    )

    result = S1BaseImageRegistry(client=fake).register(
        identity_id="42",
        run_id="run-1",
        source_job_id="job-123",
        result_payload={"workflow_id": "base-image-ipadapter-impact", "workflow_version": "2026-04-02"},
        runtime_metadata={"prompt": "portrait"},
        uploaded_artifacts=[
            {
                "artifact_type": "base_image",
                "storage_path": "missing-file.png",
                "content_type": "image/png",
                "directus_file_id": "file-1",
                "directus_asset_url": "https://directus.example.com/assets/file-1",
                "metadata_json": {},
            }
        ],
        artifact_rows=[artifact_row],
    )

    assert result is None
    assert fake.store["s1_identities"][0]["pipeline_state"] == "base_images_generated"
    assert any(event["event_type"] == "base_images_registration_failed" for event in fake.store["s1_events"])
