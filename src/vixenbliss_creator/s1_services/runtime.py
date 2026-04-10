from __future__ import annotations

from dataclasses import dataclass, field
from inspect import signature
from typing import Callable
from uuid import uuid4

from vixenbliss_creator.runtime_providers.models import JobStatus

from .models import ProgressEvent


Processor = Callable[[dict], dict]
ProgressReporter = Callable[[str, str, float], None]


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

    def _append_event(self, record: JobRecord, *, stage: str, message: str, progress: float) -> None:
        record.progress_events.append(
            ProgressEvent(job_id=record.job_id, stage=stage, message=message, progress=progress)
        )

    def _invoke_processor(self, payload: dict, emit_progress: ProgressReporter) -> dict:
        params = signature(self.processor).parameters
        if "emit_progress" in params:
            return self.processor(payload, emit_progress=emit_progress)
        return self.processor(payload)

    def submit(self, payload: dict) -> JobRecord:
        job_id = f"job-{uuid4().hex[:12]}"
        record = JobRecord(job_id=job_id, status=JobStatus.IN_PROGRESS)
        self._append_event(record, stage="accepted", message="job accepted", progress=0.05)
        self.jobs[job_id] = record

        def emit_progress(stage: str, message: str, progress: float) -> None:
            self._append_event(record, stage=stage, message=message, progress=progress)

        try:
            self._append_event(record, stage="running", message="job running", progress=0.12)
            record.result = self._invoke_processor(payload, emit_progress)
            self._append_event(record, stage="completed", message="job completed", progress=1.0)
            record.status = JobStatus.COMPLETED
        except Exception as exc:
            record.error_message = str(exc)
            self._append_event(record, stage="failed", message=str(exc), progress=1.0)
            record.status = JobStatus.FAILED
        return record

    def status(self, job_id: str) -> JobRecord:
        return self.jobs[job_id]

    def result(self, job_id: str) -> dict:
        record = self.jobs[job_id]
        if record.result is None:
            raise RuntimeError(record.error_message or "job result is not available")
        return record.result
