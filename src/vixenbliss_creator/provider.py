from __future__ import annotations

from enum import Enum


class Provider(str, Enum):
    ROUTED = "routed"
    COMFYUI = "comfyui"
    COMFYUI_HTTP = "comfyui_http"
    MODAL = "modal"
    BEAM = "beam"
    RUNPOD = "runpod"
