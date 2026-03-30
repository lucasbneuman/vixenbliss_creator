from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class VisualPipelineSettings:
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

    @classmethod
    def from_env(cls) -> "VisualPipelineSettings":
        return cls(
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
        )
