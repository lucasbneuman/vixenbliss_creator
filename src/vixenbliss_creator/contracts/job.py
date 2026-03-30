from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import Field, model_validator

from .common import ContractBaseModel, JsonObject, is_utc_datetime, utc_now


class JobSchemaVersion(str, Enum):
    V1 = "1.0.0"


class JobType(str, Enum):
    CREATE_IDENTITY = "create_identity"
    GENERATE_BASE_IMAGES = "generate_base_images"
    BUILD_DATASET = "build_dataset"
    VALIDATE_DATASET = "validate_dataset"
    TRAIN_LORA = "train_lora"
    GENERATE_CONTENT = "generate_content"
    PREPARE_VIDEO = "prepare_video"
    QA_REVIEW = "qa_review"


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"


ALLOWED_JOB_TRANSITIONS: dict[JobStatus, set[JobStatus]] = {
    JobStatus.PENDING: {JobStatus.RUNNING, JobStatus.CANCELLED},
    JobStatus.RUNNING: {JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.CANCELLED, JobStatus.TIMED_OUT},
    JobStatus.SUCCEEDED: set(),
    JobStatus.FAILED: set(),
    JobStatus.CANCELLED: set(),
    JobStatus.TIMED_OUT: set(),
}


def is_valid_job_transition(source: JobStatus, target: JobStatus) -> bool:
    return target in ALLOWED_JOB_TRANSITIONS[source]


class Job(ContractBaseModel):
    schema_version: JobSchemaVersion = JobSchemaVersion.V1
    id: UUID
    identity_id: UUID
    job_type: JobType
    status: JobStatus = JobStatus.PENDING
    timeout_seconds: int = Field(gt=0, le=86400)
    attempt_count: int = Field(default=0, ge=0, le=20)
    payload_json: JsonObject = Field(default_factory=dict)
    metadata_json: JsonObject = Field(default_factory=dict)
    error_message: str | None = Field(default=None, min_length=8, max_length=500)
    queued_at: datetime = Field(default_factory=utc_now)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def validate_consistency(self) -> "Job":
        timestamps = {
            "queued_at": self.queued_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        for field_name, value in timestamps.items():
            if not is_utc_datetime(value):
                raise ValueError(f"{field_name} must be a UTC datetime")
        for field_name, value in {"started_at": self.started_at, "finished_at": self.finished_at}.items():
            if value is not None and not is_utc_datetime(value):
                raise ValueError(f"{field_name} must be a UTC datetime")
        if self.created_at > self.updated_at:
            raise ValueError("created_at cannot be later than updated_at")
        if self.queued_at < self.created_at:
            raise ValueError("queued_at cannot be earlier than created_at")
        if self.started_at is not None and self.started_at < self.queued_at:
            raise ValueError("started_at cannot be earlier than queued_at")
        if self.finished_at is not None and self.started_at is None:
            raise ValueError("finished_at requires started_at")
        if self.finished_at is not None and self.started_at is not None and self.finished_at < self.started_at:
            raise ValueError("finished_at cannot be earlier than started_at")
        if self.status == JobStatus.PENDING and self.started_at is not None:
            raise ValueError("pending jobs cannot define started_at")
        if self.status == JobStatus.RUNNING and self.started_at is None:
            raise ValueError("running jobs require started_at")
        if self.status in {JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.CANCELLED, JobStatus.TIMED_OUT}:
            if self.started_at is None or self.finished_at is None:
                raise ValueError("terminal jobs require started_at and finished_at")
        if self.status in {JobStatus.FAILED, JobStatus.TIMED_OUT} and self.error_message is None:
            raise ValueError("failed and timed_out jobs require error_message")
        if self.status in {JobStatus.PENDING, JobStatus.RUNNING, JobStatus.SUCCEEDED, JobStatus.CANCELLED} and self.error_message is not None:
            raise ValueError("error_message is only allowed for failed and timed_out jobs")
        return self
