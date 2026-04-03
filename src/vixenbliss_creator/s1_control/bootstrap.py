from __future__ import annotations

from .config import S1ControlSettings
from .directus import DirectusSchemaManager
from .support import load_local_env


def bootstrap_directus_schema() -> list[str]:
    load_local_env()
    settings = S1ControlSettings.from_env()
    manager = DirectusSchemaManager(settings)
    return manager.ensure_schema()


if __name__ == "__main__":
    created = bootstrap_directus_schema()
    if created:
        print("created_collections=" + ",".join(created))
    else:
        print("created_collections=")
