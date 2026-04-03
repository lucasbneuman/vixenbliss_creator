from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


_ENV_PLACEHOLDERS = {"CHANGEME", "YOUR_VALUE_HERE", "TODO", "TBD"}


def _normalize_env_value(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().strip("\"'")
    if not normalized or normalized.upper() in _ENV_PLACEHOLDERS:
        return None
    return normalized


def _read_repo_dotenv() -> dict[str, str]:
    dotenv_path = Path(__file__).resolve().parents[3] / ".env"
    if not dotenv_path.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        normalized = _normalize_env_value(value)
        if normalized is not None:
            values[key.strip()] = normalized
    return values


@dataclass(frozen=True)
class AgenticSettings:
    s1_llm_provider: str = "modal"
    s1_llm_runtime_base_url: str | None = None
    s1_llm_runtime_api_key: str | None = None
    s1_llm_runtime_model: str | None = None
    s1_llm_runtime_timeout_seconds: int = 30
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
        if self.llm_serverless_base_url:
            return self.llm_serverless_base_url
        if self.s1_llm_runtime_base_url:
            return self.s1_llm_runtime_base_url.rstrip("/") + "/v1"
        return self.openai_base_url if self.openai_api_key else None

    @property
    def resolved_llm_api_key(self) -> str | None:
        return self.llm_serverless_api_key or self.s1_llm_runtime_api_key or self.openai_api_key

    @property
    def resolved_llm_model(self) -> str | None:
        return (
            self.llm_serverless_model
            or self.s1_llm_runtime_model
            or self.openai_model
            or ("gpt-4o-mini" if self.openai_api_key else None)
        )

    @classmethod
    def from_env(cls) -> "AgenticSettings":
        dotenv_values = _read_repo_dotenv()

        def _env(name: str, default: str | None = None) -> str | None:
            return _normalize_env_value(os.getenv(name)) or dotenv_values.get(name, _normalize_env_value(default))

        max_attempts_raw = os.getenv("AGENTIC_BRAIN_MAX_ATTEMPTS", "2")
        return cls(
            llm_serverless_base_url=_env("LLM_SERVERLESS_BASE_URL"),
            llm_serverless_api_key=_env("LLM_SERVERLESS_API_KEY"),
            llm_serverless_model=_env("LLM_SERVERLESS_MODEL"),
            s1_llm_provider=_env("S1_LLM_PROVIDER", "modal") or "modal",
            s1_llm_runtime_base_url=_env("S1_LLM_RUNTIME_BASE_URL"),
            s1_llm_runtime_api_key=_env("S1_LLM_RUNTIME_API_KEY"),
            s1_llm_runtime_model=_env("S1_LLM_RUNTIME_MODEL"),
            s1_llm_runtime_timeout_seconds=int(_env("S1_LLM_RUNTIME_TIMEOUT_SECONDS", "30") or "30"),
            openai_api_key=_env("OPENAI_API_KEY") or _env("OPEN_AI_TOKEN"),
            openai_model=_env("OPENAI_MODEL"),
            openai_base_url=_env("OPENAI_BASE_URL", "https://api.openai.com/v1") or "https://api.openai.com/v1",
            comfyui_copilot_base_url=_env("COMFYUI_COPILOT_BASE_URL"),
            comfyui_copilot_api_key=_env("COMFYUI_COPILOT_API_KEY"),
            comfyui_copilot_path=_env("COMFYUI_COPILOT_PATH", "/recommend") or "/recommend",
            max_attempts=int(max_attempts_raw),
            source_issue_id=_env("AGENTIC_BRAIN_SOURCE_ISSUE_ID", "DEV-7") or "DEV-7",
            source_epic_id=_env("AGENTIC_BRAIN_SOURCE_EPIC_ID", "DEV-3") or "DEV-3",
            contract_owner=_env("AGENTIC_BRAIN_CONTRACT_OWNER", "Codex") or "Codex",
        )
