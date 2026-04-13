-- SQLite smoke script for DEV-14 / T2.2.
-- It proves the operational shape of contents insertion and query without requiring Postgres.

CREATE TABLE contents (
    content_id TEXT PRIMARY KEY,
    identity_id TEXT NOT NULL,
    content_mode TEXT NOT NULL,
    video_generation_mode TEXT NULL,
    generation_status TEXT NOT NULL,
    qa_status TEXT NOT NULL,
    job_id TEXT NULL,
    primary_artifact_id TEXT NULL,
    related_artifact_ids TEXT NOT NULL DEFAULT '[]',
    base_model_id TEXT NULL,
    model_version_used TEXT NULL,
    provider TEXT NULL,
    workflow_id TEXT NULL,
    prompt TEXT NULL,
    negative_prompt TEXT NULL,
    seed INTEGER NULL,
    source_content_id TEXT NULL,
    source_artifact_id TEXT NULL,
    duration_seconds REAL NULL,
    frame_count INTEGER NULL,
    frame_rate REAL NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CHECK (content_mode IN ('image', 'video')),
    CHECK (video_generation_mode IS NULL OR video_generation_mode IN ('text_to_video', 'image_to_video')),
    CHECK (generation_status IN ('pending', 'generated', 'failed', 'archived')),
    CHECK (qa_status IN ('not_reviewed', 'approved', 'rejected')),
    CHECK (created_at <= updated_at),
    CHECK (
        content_mode <> 'video'
        OR video_generation_mode <> 'image_to_video'
        OR source_content_id IS NOT NULL
        OR source_artifact_id IS NOT NULL
    )
);

CREATE INDEX ix_contents_identity_id ON contents (identity_id);
CREATE INDEX ix_contents_content_mode ON contents (content_mode);
CREATE INDEX ix_contents_generation_status ON contents (generation_status);
CREATE INDEX ix_contents_qa_status ON contents (qa_status);
CREATE INDEX ix_contents_created_at ON contents (created_at DESC);
CREATE INDEX ix_contents_identity_created_at ON contents (identity_id, created_at DESC);

INSERT INTO contents (
    content_id,
    identity_id,
    content_mode,
    generation_status,
    qa_status,
    job_id,
    primary_artifact_id,
    related_artifact_ids,
    base_model_id,
    model_version_used,
    provider,
    workflow_id,
    prompt,
    negative_prompt,
    seed,
    metadata_json,
    created_at,
    updated_at
) VALUES (
    'content-smoke-001',
    'identity-smoke-001',
    'image',
    'generated',
    'not_reviewed',
    'job-smoke-001',
    'artifact-smoke-001',
    '["artifact-smoke-001","artifact-smoke-aux"]',
    'flux-schnell-v1',
    '2026-04-08',
    'modal',
    'content-image-flux-lora',
    'editorial portrait with stable identity',
    'low quality, watermark',
    20260410,
    '{"artifact_role":"generated_image","traceability":"smoke"}',
    '2026-04-10T00:00:00Z',
    '2026-04-10T00:00:00Z'
);
