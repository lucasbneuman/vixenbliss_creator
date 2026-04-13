-- DEV-14 / T2.2
-- Relational persistence for Content without replacing the Directus control plane.
-- content_mode is the canonical replacement for the media_modality wording in the ticket.

CREATE TABLE IF NOT EXISTS contents (
    content_id text PRIMARY KEY,
    identity_id text NOT NULL,
    content_mode text NOT NULL,
    video_generation_mode text NULL,
    generation_status text NOT NULL,
    qa_status text NOT NULL,
    job_id text NULL,
    primary_artifact_id text NULL,
    related_artifact_ids jsonb NOT NULL DEFAULT '[]'::jsonb,
    base_model_id text NULL,
    model_version_used text NULL,
    provider text NULL,
    workflow_id text NULL,
    prompt text NULL,
    negative_prompt text NULL,
    seed bigint NULL,
    source_content_id text NULL,
    source_artifact_id text NULL,
    duration_seconds double precision NULL,
    frame_count integer NULL,
    frame_rate double precision NULL,
    metadata_json jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL,
    CONSTRAINT ck_contents_content_mode CHECK (content_mode IN ('image', 'video')),
    CONSTRAINT ck_contents_video_generation_mode CHECK (
        video_generation_mode IS NULL OR video_generation_mode IN ('text_to_video', 'image_to_video')
    ),
    CONSTRAINT ck_contents_generation_status CHECK (
        generation_status IN ('pending', 'generated', 'failed', 'archived')
    ),
    CONSTRAINT ck_contents_qa_status CHECK (
        qa_status IN ('not_reviewed', 'approved', 'rejected')
    ),
    CONSTRAINT ck_contents_temporal_order CHECK (created_at <= updated_at),
    CONSTRAINT ck_contents_video_source_consistency CHECK (
        content_mode <> 'video'
        OR video_generation_mode <> 'image_to_video'
        OR source_content_id IS NOT NULL
        OR source_artifact_id IS NOT NULL
    )
);

CREATE INDEX IF NOT EXISTS ix_contents_identity_id
    ON contents (identity_id);

CREATE INDEX IF NOT EXISTS ix_contents_content_mode
    ON contents (content_mode);

CREATE INDEX IF NOT EXISTS ix_contents_generation_status
    ON contents (generation_status);

CREATE INDEX IF NOT EXISTS ix_contents_qa_status
    ON contents (qa_status);

CREATE INDEX IF NOT EXISTS ix_contents_created_at
    ON contents (created_at DESC);

CREATE INDEX IF NOT EXISTS ix_contents_identity_created_at
    ON contents (identity_id, created_at DESC);
