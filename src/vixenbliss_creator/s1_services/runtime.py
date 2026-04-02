from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable
from uuid import uuid4

from vixenbliss_creator.runtime_providers.models import JobStatus

from .models import ProgressEvent


Processor = Callable[[dict], dict]


@dataclass
class JobRecord:
    job_id: str
    status: JobStatus
    result: dict | None = None
    error_message: str | None = None
    progress_events: list[ProgressEvent] = field(default_factory=list)

    def status_payload(self, *, progress_url: str | None = None, result_url: str | None = None) -> dict:
        metadata = {
            "progress_events": [event.model_dump(mode="json") for event in self.progress_events],
        }
        if self.error_message:
            metadata["error_message"] = self.error_message
        return {
            "job_id": self.job_id,
            "status": self.status.value,
            "result_url": result_url,
            "progress_url": progress_url,
            "metadata": metadata,
        }


@dataclass
class InMemoryServiceRuntime:
    processor: Processor
    jobs: dict[str, JobRecord] = field(default_factory=dict)

    def submit(self, payload: dict) -> JobRecord:
        job_id = f"job-{uuid4().hex[:12]}"
        record = JobRecord(job_id=job_id, status=JobStatus.IN_PROGRESS)
        record.progress_events.append(ProgressEvent(job_id=job_id, stage="accepted", message="job accepted", progress=0.05))
        self.jobs[job_id] = record
        try:
            record.progress_events.append(ProgressEvent(job_id=job_id, stage="running", message="job running", progress=0.45))
            record.result = self.processor(payload)
            record.progress_events.append(ProgressEvent(job_id=job_id, stage="completed", message="job completed", progress=1.0))
            record.status = JobStatus.COMPLETED
        except Exception as exc:
            record.error_message = str(exc)
            record.progress_events.append(ProgressEvent(job_id=job_id, stage="failed", message=str(exc), progress=1.0))
            record.status = JobStatus.FAILED
        return record

    def status(self, job_id: str) -> JobRecord:
        return self.jobs[job_id]

    def result(self, job_id: str) -> dict:
        record = self.jobs[job_id]
        if record.result is None:
            raise RuntimeError(record.error_message or "job result is not available")
        return record.result
