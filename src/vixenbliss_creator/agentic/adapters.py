from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Callable
from urllib import error, parse, request

from .config import AgenticSettings
from .models import CopilotRecommendation, CritiqueIssue, ExpansionResult


def _json_post(url: str, payload: dict, headers: dict[str, str]) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(url=url, data=body, headers=headers, method="POST")
    try:
        with request.urlopen(req, timeout=30) as response:
            raw = response.read().decode("utf-8")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP error calling {url}: {exc.code} {detail}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Network error calling {url}: {exc.reason}") from exc
    return json.loads(raw)


@dataclass
class OpenAICompatibleLLMClient:
    settings: AgenticSettings

    def generate_expansion(
        self,
        idea: str,
        critique_history: list[CritiqueIssue],
        attempt_count: int,
    ) -> ExpansionResult:
        if not self.settings.llm_serverless_base_url:
            raise RuntimeError("LLM_SERVERLESS_BASE_URL is required for the real LLM adapter")
        if not self.settings.llm_serverless_model:
            raise RuntimeError("LLM_SERVERLESS_MODEL is required for the real LLM adapter")

        critique_lines = [f"{issue.code}: {issue.message}" for issue in critique_history] or ["none"]
        instructions = (
            "Return only valid JSON for ExpansionResult. "
            "The technical_sheet_payload must satisfy the TechnicalSheet contract exactly."
        )
        payload = {
            "model": self.settings.llm_serverless_model,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": instructions},
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "idea": idea,
                            "attempt_count": attempt_count,
                            "critique_history": critique_lines,
                        }
                    ),
                },
            ],
        }
        headers = {"Content-Type": "application/json"}
        if self.settings.llm_serverless_api_key:
            headers["Authorization"] = f"Bearer {self.settings.llm_serverless_api_key}"
        url = self.settings.llm_serverless_base_url.rstrip("/") + "/chat/completions"
        response_payload = _json_post(url, payload, headers)
        content = response_payload["choices"][0]["message"]["content"]
        return ExpansionResult.model_validate_json(content)


@dataclass
class ComfyUICopilotHTTPClient:
    settings: AgenticSettings

    def recommend_workflow(self, expansion: ExpansionResult) -> CopilotRecommendation:
        if not self.settings.comfyui_copilot_base_url:
            raise RuntimeError("COMFYUI_COPILOT_BASE_URL is required for the real Copilot adapter")

        headers = {"Content-Type": "application/json"}
        if self.settings.comfyui_copilot_api_key:
            headers["Authorization"] = f"Bearer {self.settings.comfyui_copilot_api_key}"
        url = parse.urljoin(
            self.settings.comfyui_copilot_base_url.rstrip("/") + "/",
            self.settings.comfyui_copilot_path.lstrip("/"),
        )
        response_payload = _json_post(
            url,
            {
                "expansion_summary": expansion.expansion_summary,
                "prompt_blueprint": expansion.prompt_blueprint,
                "technical_sheet_payload": expansion.technical_sheet_payload.model_dump(mode="json"),
            },
            headers,
        )
        return CopilotRecommendation.model_validate(response_payload)


@dataclass
class FakeLLMClient:
    sequence: list[ExpansionResult] = field(default_factory=list)
    factory: Callable[[str, list[CritiqueIssue], int], ExpansionResult | dict] | None = None
    _calls: int = field(default=0, init=False, repr=False)

    def generate_expansion(
        self,
        idea: str,
        critique_history: list[CritiqueIssue],
        attempt_count: int,
    ) -> ExpansionResult:
        if self.factory is not None:
            payload = self.factory(idea, critique_history, attempt_count)
            return ExpansionResult.model_validate(payload)
        if self._calls >= len(self.sequence):
            raise RuntimeError("FakeLLMClient sequence exhausted")
        item = self.sequence[self._calls]
        self._calls += 1
        return item


@dataclass
class FakeCopilotClient:
    sequence: list[CopilotRecommendation] = field(default_factory=list)
    factory: Callable[[ExpansionResult], CopilotRecommendation | dict] | None = None
    _calls: int = field(default=0, init=False, repr=False)

    def recommend_workflow(self, expansion: ExpansionResult) -> CopilotRecommendation:
        if self.factory is not None:
            payload = self.factory(expansion)
            return CopilotRecommendation.model_validate(payload)
        if self._calls >= len(self.sequence):
            raise RuntimeError("FakeCopilotClient sequence exhausted")
        item = self.sequence[self._calls]
        self._calls += 1
        return item
