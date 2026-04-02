from __future__ import annotations

import os
from dataclasses import dataclass

from vixenbliss_creator.provider import Provider

from .models import ServiceRuntime


@dataclass(frozen=True)
class RuntimeProviderSettings:
    s1_image_provider: Provider = Provider.BEAM
    s1_lora_train_provider: Provider = Provider.MODAL
    s1_llm_provider: Provider = Provider.MODAL
    s2_image_provider: Provider = Provider.BEAM
    s2_video_provider: Provider = Provider.MODAL
    beam_api_key: str | None = None
    beam_endpoint_s1_image: str | None = None
    beam_endpoint_s1_lora_train: str | None = None
    beam_endpoint_s1_llm: str | None = None
    beam_endpoint_s2_image: str | None = None
    beam_endpoint_s2_video: str | None = None
    modal_token_id: str | None = None
    modal_token_secret: str | None = None
    modal_endpoint_s1_image: str | None = None
    modal_endpoint_s1_lora_train: str | None = None
    modal_endpoint_s1_llm: str | None = None
    modal_endpoint_s2_image: str | None = None
    modal_endpoint_s2_video: str | None = None
    provider_http_timeout_seconds: int = 30
    provider_poll_interval_seconds: int = 3
    provider_job_timeout_seconds: int = 900

    def provider_for(self, service_runtime: ServiceRuntime) -> Provider:
        mapping = {
            ServiceRuntime.S1_IMAGE: self.s1_image_provider,
            ServiceRuntime.S1_LORA_TRAIN: self.s1_lora_train_provider,
            ServiceRuntime.S1_LLM: self.s1_llm_provider,
            ServiceRuntime.S2_IMAGE: self.s2_image_provider,
            ServiceRuntime.S2_VIDEO: self.s2_video_provider,
        }
        return mapping[service_runtime]

    def endpoint_for(self, provider: Provider, service_runtime: ServiceRuntime) -> str | None:
        endpoints = {
            Provider.BEAM: {
                ServiceRuntime.S1_IMAGE: self.beam_endpoint_s1_image,
                ServiceRuntime.S1_LORA_TRAIN: self.beam_endpoint_s1_lora_train,
                ServiceRuntime.S1_LLM: self.beam_endpoint_s1_llm,
                ServiceRuntime.S2_IMAGE: self.beam_endpoint_s2_image,
                ServiceRuntime.S2_VIDEO: self.beam_endpoint_s2_video,
            },
            Provider.MODAL: {
                ServiceRuntime.S1_IMAGE: self.modal_endpoint_s1_image,
                ServiceRuntime.S1_LORA_TRAIN: self.modal_endpoint_s1_lora_train,
                ServiceRuntime.S1_LLM: self.modal_endpoint_s1_llm,
                ServiceRuntime.S2_IMAGE: self.modal_endpoint_s2_image,
                ServiceRuntime.S2_VIDEO: self.modal_endpoint_s2_video,
            },
        }
        return endpoints.get(provider, {}).get(service_runtime)

    def auth_headers_for(self, provider: Provider) -> dict[str, str]:
        if provider == Provider.BEAM and self.beam_api_key:
            return {"Authorization": f"Bearer {self.beam_api_key}"}
        if provider == Provider.MODAL and self.modal_token_id and self.modal_token_secret:
            return {
                "Modal-Key": self.modal_token_id,
                "Modal-Secret": self.modal_token_secret,
            }
        return {}

    @classmethod
    def from_env(cls) -> "RuntimeProviderSettings":
        return cls(
            s1_image_provider=Provider(os.getenv("S1_IMAGE_PROVIDER", Provider.BEAM.value)),
            s1_lora_train_provider=Provider(os.getenv("S1_LORA_TRAIN_PROVIDER", Provider.MODAL.value)),
            s1_llm_provider=Provider(os.getenv("S1_LLM_PROVIDER", Provider.MODAL.value)),
            s2_image_provider=Provider(os.getenv("S2_IMAGE_PROVIDER", Provider.BEAM.value)),
            s2_video_provider=Provider(os.getenv("S2_VIDEO_PROVIDER", Provider.MODAL.value)),
            beam_api_key=os.getenv("BEAM_API_KEY"),
            beam_endpoint_s1_image=os.getenv("BEAM_ENDPOINT_S1_IMAGE"),
            beam_endpoint_s1_lora_train=os.getenv("BEAM_ENDPOINT_S1_LORA_TRAIN"),
            beam_endpoint_s1_llm=os.getenv("BEAM_ENDPOINT_S1_LLM"),
            beam_endpoint_s2_image=os.getenv("BEAM_ENDPOINT_S2_IMAGE"),
            beam_endpoint_s2_video=os.getenv("BEAM_ENDPOINT_S2_VIDEO"),
            modal_token_id=os.getenv("MODAL_TOKEN_ID"),
            modal_token_secret=os.getenv("MODAL_TOKEN_SECRET"),
            modal_endpoint_s1_image=os.getenv("MODAL_ENDPOINT_S1_IMAGE"),
            modal_endpoint_s1_lora_train=os.getenv("MODAL_ENDPOINT_S1_LORA_TRAIN"),
            modal_endpoint_s1_llm=os.getenv("MODAL_ENDPOINT_S1_LLM"),
            modal_endpoint_s2_image=os.getenv("MODAL_ENDPOINT_S2_IMAGE"),
            modal_endpoint_s2_video=os.getenv("MODAL_ENDPOINT_S2_VIDEO"),
            provider_http_timeout_seconds=int(os.getenv("PROVIDER_HTTP_TIMEOUT_SECONDS", "30")),
            provider_poll_interval_seconds=int(os.getenv("PROVIDER_POLL_INTERVAL_SECONDS", "3")),
            provider_job_timeout_seconds=int(os.getenv("PROVIDER_JOB_TIMEOUT_SECONDS", "900")),
        )
