from __future__ import annotations

import os
from dataclasses import dataclass

from .models import Provider


@dataclass(frozen=True)
class VisualPipelineSettings:
    visual_execution_provider: Provider = Provider.COMFYUI
    comfyui_base_url: str | None = None
    comfyui_workflow_image_id: str | None = None
    comfyui_workflow_image_version: str = "v1"
    comfyui_ip_adapter_model: str = "plus_face"
    comfyui_ip_adapter_node_id: str | None = None
    comfyui_face_detector_node_id: str | None = None
    comfyui_face_detailer_node_id: str | None = None
    comfyui_face_confidence_threshold: float = 0.8
    comfyui_resume_cache_mode: str = "checkpoint"
    comfyui_http_timeout_seconds: int = 30
    runpod_api_key: str | None = None
    runpod_endpoint_image_gen: str | None = None
    runpod_poll_interval_seconds: int = 3
    runpod_job_timeout_seconds: int = 600
    runpod_use_runsync: bool = False

    @classmethod
    def from_env(cls) -> "VisualPipelineSettings":
        return cls(
            visual_execution_provider=Provider(os.getenv("VISUAL_EXECUTION_PROVIDER", Provider.COMFYUI.value)),
            comfyui_base_url=os.getenv("COMFYUI_BASE_URL"),
            comfyui_workflow_image_id=os.getenv("COMFYUI_WORKFLOW_IMAGE_ID"),
            comfyui_workflow_image_version=os.getenv("COMFYUI_WORKFLOW_IMAGE_VERSION", "v1"),
            comfyui_ip_adapter_model=os.getenv("COMFYUI_IP_ADAPTER_MODEL", "plus_face"),
            comfyui_ip_adapter_node_id=os.getenv("COMFYUI_IP_ADAPTER_NODE_ID"),
            comfyui_face_detector_node_id=os.getenv("COMFYUI_FACE_DETECTOR_NODE_ID"),
            comfyui_face_detailer_node_id=os.getenv("COMFYUI_FACE_DETAILER_NODE_ID"),
            comfyui_face_confidence_threshold=float(os.getenv("COMFYUI_FACE_CONFIDENCE_THRESHOLD", "0.8")),
            comfyui_resume_cache_mode=os.getenv("COMFYUI_RESUME_CACHE_MODE", "checkpoint"),
            comfyui_http_timeout_seconds=int(os.getenv("COMFYUI_HTTP_TIMEOUT_SECONDS", "30")),
            runpod_api_key=os.getenv("RUNPOD_API_KEY"),
            runpod_endpoint_image_gen=os.getenv("RUNPOD_ENDPOINT_IMAGE_GEN"),
            runpod_poll_interval_seconds=int(os.getenv("RUNPOD_POLL_INTERVAL_SECONDS", "3")),
            runpod_job_timeout_seconds=int(os.getenv("RUNPOD_JOB_TIMEOUT_SECONDS", "600")),
            runpod_use_runsync=os.getenv("RUNPOD_USE_RUNSYNC", "false").lower() in {"1", "true", "yes", "on"},
        )
