from __future__ import annotations

from enum import Enum

from pydantic import Field

from vixenbliss_creator.contracts.common import ContractBaseModel, JsonObject
from vixenbliss_creator.provider import Provider


class ServiceRuntime(str, Enum):
    S1_IMAGE = "s1_image"
    S1_LORA_TRAIN = "s1_lora_train"
    S1_LLM = "s1_llm"
    S2_IMAGE = "s2_image"
    S2_VIDEO = "s2_video"


class JobStatus(str, Enum):
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class JobHandle(ContractBaseModel):
    provider: Provider
    service_runtime: ServiceRuntime
    job_id: str = Field(min_length=1, max_length=120)
    submit_url: str | None = Field(default=None, min_length=3, max_length=500)
    status_url: str | None = Field(default=None, min_length=3, max_length=500)
    result_url: str | None = Field(default=None, min_length=3, max_length=500)
    status: JobStatus = JobStatus.QUEUED
    metadata_json: JsonObject = Field(default_factory=dict)
