from __future__ import annotations

from typing import Protocol

from .models import JobHandle, ServiceRuntime


class RuntimeProviderClient(Protocol):
    def submit_job(self, service_runtime: ServiceRuntime, payload: dict) -> JobHandle:
        ...

    def get_job_status(self, handle: JobHandle) -> JobHandle:
        ...

    def fetch_result(self, handle: JobHandle) -> dict:
        ...

    def progress_stream_url(self, handle: JobHandle) -> str | None:
        ...

    def resolve_asset_uri(self, uri: str) -> str:
        ...

    def healthcheck(self, service_runtime: ServiceRuntime) -> dict:
        ...
