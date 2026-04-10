from __future__ import annotations

import argparse
import json
from typing import Any

from .bootstrap import bootstrap_directus_schema
from .config import S1ControlSettings
from .directus import DirectusControlPlaneClient
from .support import load_local_env


S1_COLLECTIONS = (
    "s1_events",
    "s1_model_registry",
    "s1_model_assets",
    "s1_artifacts",
    "s1_generation_runs",
    "s1_prompt_requests",
    "s1_identities",
)


def _list_all(client: DirectusControlPlaneClient, collection: str) -> list[dict[str, Any]]:
    page_size = 200
    offset = 0
    rows: list[dict[str, Any]] = []
    while True:
        batch = client.list_items(
            collection,
            params={"limit": str(page_size), "offset": str(offset)},
        )
        if not batch:
            break
        rows.extend(batch)
        if len(batch) < page_size:
            break
        offset += page_size
    return rows


def run_cleanup() -> dict[str, Any]:
    load_local_env()
    bootstrap_directus_schema()
    client = DirectusControlPlaneClient(S1ControlSettings.from_env())

    artifacts = _list_all(client, "s1_artifacts")
    identities = _list_all(client, "s1_identities")

    file_ids: set[str] = set()
    for artifact in artifacts:
        file_id = artifact.get("file")
        if file_id:
            file_ids.add(str(file_id))
    for identity in identities:
        for field_name in (
            "reference_face_image_id",
            "latest_base_image_file_id",
            "latest_dataset_manifest_file_id",
            "latest_dataset_package_file_id",
        ):
            file_id = identity.get(field_name)
            if file_id:
                file_ids.add(str(file_id))

    deleted_rows: dict[str, int] = {}
    for collection in S1_COLLECTIONS:
        rows = _list_all(client, collection)
        deleted_rows[collection] = len(rows)
        for row in rows:
            client.delete_item(collection, str(row["id"]))

    deleted_files = 0
    for file_id in sorted(file_ids):
        try:
            client.delete_file(file_id)
            deleted_files += 1
        except Exception:
            continue

    return {
        "deleted_rows": deleted_rows,
        "deleted_files": deleted_files,
        "tracked_file_ids": sorted(file_ids),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Delete S1 test data from Directus collections and files.")
    parser.parse_args()
    result = run_cleanup()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
