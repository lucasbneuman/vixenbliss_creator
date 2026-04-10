from __future__ import annotations

import sqlite3
from pathlib import Path


MIGRATION_PATH = Path(__file__).resolve().parents[1] / "migrations" / "001_initial_relational_persistence.sql"
SMOKE_TEST_PATH = Path(__file__).resolve().parents[1] / "migrations" / "smoke" / "001_relational_persistence_smoke.sql"


def test_migration_sql_declares_expected_tables_and_indexes() -> None:
    sql = MIGRATION_PATH.read_text(encoding="utf-8")

    assert "CREATE TABLE IF NOT EXISTS contents" in sql
    assert "content_id text PRIMARY KEY" in sql
    assert "identity_id text NOT NULL" in sql
    assert "content_mode text NOT NULL" in sql
    assert "video_generation_mode text NULL" in sql
    assert "generation_status text NOT NULL" in sql
    assert "qa_status text NOT NULL" in sql
    assert "job_id text NULL" in sql
    assert "primary_artifact_id text NULL" in sql
    assert "related_artifact_ids jsonb NOT NULL" in sql
    assert "metadata_json jsonb NOT NULL" in sql
    assert "CREATE INDEX IF NOT EXISTS ix_contents_identity_id" in sql
    assert "CREATE INDEX IF NOT EXISTS ix_contents_content_mode" in sql
    assert "CREATE INDEX IF NOT EXISTS ix_contents_generation_status" in sql
    assert "CREATE INDEX IF NOT EXISTS ix_contents_qa_status" in sql
    assert "CREATE INDEX IF NOT EXISTS ix_contents_created_at" in sql
    assert "CREATE INDEX IF NOT EXISTS ix_contents_identity_created_at" in sql


def test_migration_sql_uses_jsonb_and_temporal_checks() -> None:
    sql = MIGRATION_PATH.read_text(encoding="utf-8")

    assert "related_artifact_ids jsonb NOT NULL DEFAULT '[]'::jsonb" in sql
    assert "metadata_json jsonb NOT NULL DEFAULT '{}'::jsonb" in sql
    assert "CONSTRAINT ck_contents_temporal_order CHECK (created_at <= updated_at)" in sql
    assert "video_generation_mode" in sql
    assert "source_content_id" in sql
    assert "source_artifact_id" in sql


def test_smoke_sql_covers_insert_query_and_failure_scenarios() -> None:
    smoke_sql = SMOKE_TEST_PATH.read_text(encoding="utf-8")
    connection = sqlite3.connect(":memory:")
    connection.executescript(smoke_sql)

    stored = connection.execute(
        """
        SELECT
            content_id,
            identity_id,
            content_mode,
            generation_status,
            qa_status,
            job_id,
            primary_artifact_id,
            base_model_id,
            model_version_used
        FROM contents
        WHERE content_id = ?
        """,
        ("content-smoke-001",),
    ).fetchone()

    assert stored == (
        "content-smoke-001",
        "identity-smoke-001",
        "image",
        "generated",
        "not_reviewed",
        "job-smoke-001",
        "artifact-smoke-001",
        "flux-schnell-v1",
        "2026-04-08",
    )

    by_identity = connection.execute(
        "SELECT content_id FROM contents WHERE identity_id = ? ORDER BY created_at DESC",
        ("identity-smoke-001",),
    ).fetchall()
    assert by_identity == [("content-smoke-001",)]

    indexes = {row[1] for row in connection.execute("PRAGMA index_list('contents')").fetchall()}
    assert "ix_contents_identity_id" in indexes
    assert "ix_contents_content_mode" in indexes
    assert "ix_contents_generation_status" in indexes
    assert "ix_contents_qa_status" in indexes
    assert "ix_contents_created_at" in indexes
    assert "ix_contents_identity_created_at" in indexes

    try:
        connection.execute(
            """
            INSERT INTO contents (
                content_id,
                identity_id,
                content_mode,
                video_generation_mode,
                generation_status,
                qa_status,
                created_at,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "content-invalid-video",
                "identity-smoke-001",
                "video",
                "image_to_video",
                "pending",
                "not_reviewed",
                "2026-04-10T00:00:00Z",
                "2026-04-10T00:00:00Z",
            ),
        )
    except sqlite3.IntegrityError:
        failed_as_expected = True
    else:
        failed_as_expected = False

    assert failed_as_expected is True
    connection.close()
