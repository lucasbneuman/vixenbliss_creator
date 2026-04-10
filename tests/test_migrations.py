from __future__ import annotations

from pathlib import Path


def test_sql_migration_artifacts_exist() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    migration = repo_root / "migrations" / "001_initial_relational_persistence.sql"
    smoke = repo_root / "migrations" / "smoke" / "001_relational_persistence_smoke.sql"

    assert migration.exists()
    assert smoke.exists()
