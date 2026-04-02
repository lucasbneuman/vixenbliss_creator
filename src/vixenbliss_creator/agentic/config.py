from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AgenticSettings:
    llm_serverless_base_url: str | None = None
    llm_serverless_api_key: str | None = None
    llm_serverless_model: str | None = None
    openai_api_key: str | None = None
    openai_model: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    comfyui_copilot_base_url: str | None = None
    comfyui_copilot_api_key: str | None = None
    comfyui_copilot_path: str = "/recommend"
    max_attempts: int = 2
    source_issue_id: str = "DEV-7"
    source_epic_id: str = "DEV-3"
    contract_owner: str = "Codex"

    @property
    def resolved_llm_base_url(self) -> str | None:
        return self.llm_serverless_base_url or (self.openai_base_url if self.openai_api_key else None)

    @property
    def resolved_llm_api_key(self) -> str | None:
        return self.llm_serverless_api_key or self.openai_api_key

    @property
    def resolved_llm_model(self) -> str | None:
        return self.llm_serverless_model or self.openai_model or ("gpt-4o-mini" if self.openai_api_key else None)

    @classmethod
    def from_env(cls) -> "AgenticSettings":
        max_attempts_raw = os.getenv("AGENTIC_BRAIN_MAX_ATTEMPTS", "2")
        return cls(
            llm_serverless_base_url=os.getenv("LLM_SERVERLESS_BASE_URL"),
            llm_serverless_api_key=os.getenv("LLM_SERVERLESS_API_KEY"),
            llm_serverless_model=os.getenv("LLM_SERVERLESS_MODEL"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_model=os.getenv("OPENAI_MODEL"),
            openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            comfyui_copilot_base_url=os.getenv("COMFYUI_COPILOT_BASE_URL"),
            comfyui_copilot_api_key=os.getenv("COMFYUI_COPILOT_API_KEY"),
            comfyui_copilot_path=os.getenv("COMFYUI_COPILOT_PATH", "/recommend"),
            max_attempts=int(max_attempts_raw),
            source_issue_id=os.getenv("AGENTIC_BRAIN_SOURCE_ISSUE_ID", "DEV-7"),
            source_epic_id=os.getenv("AGENTIC_BRAIN_SOURCE_EPIC_ID", "DEV-3"),
            contract_owner=os.getenv("AGENTIC_BRAIN_CONTRACT_OWNER", "Codex"),
        )
