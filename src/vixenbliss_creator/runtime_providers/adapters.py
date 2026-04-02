from __future__ import annotations

import time
from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit

from vixenbliss_creator.runtime_http import json_get as _json_get
from vixenbliss_creator.runtime_http import json_post as _json_post
from vixenbliss_creator.provider import Provider

from .config import RuntimeProviderSettings
from .models import JobHandle, JobStatus, ServiceRuntime


@dataclass
class HTTPPollingRuntimeProviderClient:
    provider: Provider
    settings: RuntimeProviderSettings

    def submit_job(self, service_runtime: ServiceRuntime, payload: dict) -> JobHandle:
        endpoint = self._endpoint_for(service_runtime)
        response = _json_post(
            f"{endpoint}/jobs",
            {"input": payload, "service_runtime": service_runtime.value},
            timeout_seconds=self.settings.provider_http_timeout_seconds,
            headers=self.settings.auth_headers_for(self.provider),
        )
        output = response.get("output")
        if isinstance(output, dict):
            handle = self._handle_for(endpoint=endpoint, service_runtime=service_runtime, payload=response)
            handle.status = JobStatus.COMPLETED
            handle.result_url = f"{endpoint}/jobs/{handle.job_id}/result"
            return handle
        return self._handle_for(endpoint=endpoint, service_runtime=service_runtime, payload=response)

    def get_job_status(self, handle: JobHandle) -> JobHandle:
        status_url = handle.status_url or f"{self._endpoint_for(handle.service_runtime)}/jobs/{handle.job_id}"
        payload = _json_get(
            status_url,
            timeout_seconds=self.settings.provider_http_timeout_seconds,
            headers=self.settings.auth_headers_for(handle.provider),
        )
        raw_status = str(payload.get("status", JobStatus.IN_PROGRESS.value)).lower()
        status = JobStatus(raw_status)
        return handle.model_copy(
            update={
                "status": status,
                "result_url": payload.get("result_url") or handle.result_url,
                "progress_url": payload.get("progress_url") or handle.progress_url,
                "metadata_json": {**handle.metadata_json, **payload.get("metadata", {})},
            }
        )

    def fetch_result(self, handle: JobHandle) -> dict:
        if handle.status == JobStatus.COMPLETED and handle.result_url:
            return _json_get(
                handle.result_url,
                timeout_seconds=self.settings.provider_http_timeout_seconds,
                headers=self.settings.auth_headers_for(handle.provider),
            )

        deadline = time.time() + self.settings.provider_job_timeout_seconds
        current = handle
        while time.time() < deadline:
            current = self.get_job_status(current)
            if current.status == JobStatus.COMPLETED:
                result_url = current.result_url or f"{self._endpoint_for(current.service_runtime)}/jobs/{current.job_id}/result"
                return _json_get(
                    result_url,
                    timeout_seconds=self.settings.provider_http_timeout_seconds,
                    headers=self.settings.auth_headers_for(current.provider),
                )
            if current.status == JobStatus.FAILED:
                raise RuntimeError(f"{current.provider} job {current.job_id} failed")
            time.sleep(self.settings.provider_poll_interval_seconds)
        raise RuntimeError(f"{current.provider} job {current.job_id} did not complete within timeout")

    def resolve_asset_uri(self, uri: str) -> str:
        return uri

    def progress_stream_url(self, handle: JobHandle) -> str | None:
        return handle.progress_url

    def healthcheck(self, service_runtime: ServiceRuntime) -> dict:
        endpoint = self._endpoint_for(service_runtime)
        return _json_get(
            f"{endpoint}/healthcheck",
            timeout_seconds=self.settings.provider_http_timeout_seconds,
            headers=self.settings.auth_headers_for(self.provider),
        )

    def _endpoint_for(self, service_runtime: ServiceRuntime) -> str:
        endpoint = self.settings.endpoint_for(self.provider, service_runtime)
        if not endpoint:
            raise RuntimeError(f"missing {self.provider.value} endpoint for {service_runtime.value}")
        return endpoint.rstrip("/")

    def _progress_url_for(self, endpoint: str, job_id: str) -> str:
        parts = urlsplit(endpoint)
        scheme = "wss" if parts.scheme == "https" else "ws" if parts.scheme == "http" else parts.scheme
        return urlunsplit((scheme, parts.netloc, f"{parts.path.rstrip('/')}/ws/jobs/{job_id}", "", ""))

    def _handle_for(self, *, endpoint: str, service_runtime: ServiceRuntime, payload: dict) -> JobHandle:
        job_id = str(payload.get("job_id") or payload.get("id") or payload.get("request_id") or "inline-result")
        return JobHandle(
            provider=self.provider,
            service_runtime=service_runtime,
            job_id=job_id,
            submit_url=f"{endpoint}/jobs",
            status_url=payload.get("status_url") or f"{endpoint}/jobs/{job_id}",
            result_url=payload.get("result_url"),
            progress_url=payload.get("progress_url") or self._progress_url_for(endpoint, job_id),
            status=JobStatus(str(payload.get("status", JobStatus.QUEUED.value)).lower()),
            metadata_json=payload.get("metadata", {}),
        )


class BeamRuntimeProviderClient(HTTPPollingRuntimeProviderClient):
    def __init__(self, settings: RuntimeProviderSettings) -> None:
        super().__init__(provider=Provider.BEAM, settings=settings)


class ModalRuntimeProviderClient(HTTPPollingRuntimeProviderClient):
    def __init__(self, settings: RuntimeProviderSettings) -> None:
        super().__init__(provider=Provider.MODAL, settings=settings)
