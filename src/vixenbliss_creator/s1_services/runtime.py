from __future__ import annotations

from dataclasses import dataclass, field
from inspect import signature
from threading import Event, Lock, Thread
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
    done_event: Event = field(default_factory=Event, repr=False)

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
    _lock: Lock = field(default_factory=Lock)

    def _append_event(self, record: JobRecord, *, stage: str, message: str, progress: float) -> None:
        with self._lock:
            record.progress_events.append(
                ProgressEvent(job_id=record.job_id, stage=stage, message=message, progress=progress)
            )

    def _invoke_processor(self, payload: dict, emit_progress: ProgressReporter) -> dict:
        params = signature(self.processor).parameters
        if "emit_progress" in params:
            return self.processor(payload, emit_progress=emit_progress)
        return self.processor(payload)

    @staticmethod
    def _is_error_result(result: dict | None) -> bool:
        if not isinstance(result, dict):
            return False
        return bool(result.get("error_code") or result.get("error_message"))

    def _run_job(self, record: JobRecord, payload: dict) -> None:
        def emit_progress(stage: str, message: str, progress: float) -> None:
            self._append_event(record, stage=stage, message=message, progress=progress)

        try:
            self._append_event(record, stage="running", message="job running", progress=0.12)
            result = self._invoke_processor(payload, emit_progress)
            with self._lock:
                record.result = result
                if self._is_error_result(result):
                    record.error_message = str(result.get("error_message") or result.get("error_code") or "job failed")
                    record.status = JobStatus.FAILED
                else:
                    record.status = JobStatus.COMPLETED

            if self._is_error_result(result):
                self._append_event(record, stage="failed", message=record.error_message or "job failed", progress=1.0)
            else:
                self._append_event(record, stage="completed", message="job completed", progress=1.0)
        except Exception as exc:
            with self._lock:
                record.error_message = str(exc)
                record.status = JobStatus.FAILED
            self._append_event(record, stage="failed", message=str(exc), progress=1.0)
        finally:
            record.done_event.set()

    def submit(self, payload: dict) -> JobRecord:
        job_id = f"job-{uuid4().hex[:12]}"
        record = JobRecord(job_id=job_id, status=JobStatus.IN_PROGRESS)
        self._append_event(record, stage="accepted", message="job accepted", progress=0.05)
        with self._lock:
            self.jobs[job_id] = record
        Thread(target=self._run_job, args=(record, payload), daemon=True).start()
        record.done_event.wait(timeout=0.05)
        return record

    def status(self, job_id: str) -> JobRecord:
        with self._lock:
            return self.jobs[job_id]

    def result(self, job_id: str) -> dict:
        with self._lock:
            record = self.jobs[job_id]
            result = record.result
            error_message = record.error_message
        if result is None:
            raise RuntimeError(error_message or "job result is not available")
        return result
