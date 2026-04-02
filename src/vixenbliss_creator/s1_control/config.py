from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class S1ControlSettings:
    directus_base_url: str
    directus_token: str
    directus_timeout_seconds: int = 30
    directus_webhook_secret: str | None = None
    directus_assets_storage: str = "directus"
    s1_control_bind_host: str = "127.0.0.1"
    s1_control_port: int = 8091
    s1_control_public_base_url: str | None = None

    @classmethod
    def from_env(cls) -> "S1ControlSettings":
        directus_base_url = os.getenv("DIRECTUS_BASE_URL")
        directus_token = os.getenv("DIRECTUS_API_TOKEN")
        if not directus_base_url:
            raise ValueError("DIRECTUS_BASE_URL is required for S1 control plane")
        if not directus_token:
            raise ValueError("DIRECTUS_API_TOKEN is required for S1 control plane")
        return cls(
            directus_base_url=directus_base_url.rstrip("/"),
            directus_token=directus_token,
            directus_timeout_seconds=int(os.getenv("DIRECTUS_TIMEOUT_SECONDS", "30")),
            directus_webhook_secret=os.getenv("DIRECTUS_WEBHOOK_SECRET"),
            directus_assets_storage=os.getenv("DIRECTUS_ASSETS_STORAGE", "directus"),
            s1_control_bind_host=os.getenv("S1_CONTROL_BIND_HOST", "127.0.0.1"),
            s1_control_port=int(os.getenv("S1_CONTROL_PORT", "8091")),
            s1_control_public_base_url=os.getenv("S1_CONTROL_PUBLIC_BASE_URL"),
        )
