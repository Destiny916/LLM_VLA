"""OpenAI-compatible LLM planner."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Protocol

from .actions import sequence_to_text, validate_sequence
from .harness import read_core_harness
from .prompting import build_repair_prompt, build_system_prompt


class ChatClient(Protocol):
    def complete(self, messages: list[dict[str, str]]) -> str:
        """Return raw assistant content."""


def build_prompt_messages(user_request: str) -> list[dict[str, str]]:
    """Build messages from harness context and the user request."""
    harness_context = read_core_harness()
    system_content = build_system_prompt(harness_context)
    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_request},
    ]


@dataclass
class MockClient:
    output: str

    def complete(self, messages: list[dict[str, str]]) -> str:
        return self.output


@dataclass(frozen=True)
class PlanningResult:
    raw_output: str
    visible_reasoning: str
    action_tokens: str


@dataclass
class OpenAIChatClient:
    base_url: str
    api_key: str
    model: str
    timeout: float = 60.0

    def complete(self, messages: list[dict[str, str]]) -> str:
        url = self.base_url.rstrip("/") + "/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0,
        }
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=data,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                response_body = response.read().decode("utf-8")
        except urllib.error.URLError as exc:
            raise RuntimeError(f"LLM API request failed: {exc}") from exc

        parsed = json.loads(response_body)
        try:
            content = parsed["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("LLM API response did not contain choices[0].message.content") from exc
        if not isinstance(content, str):
            raise RuntimeError("LLM API response content is not a string")
        return content.strip()


@dataclass
class OpenAICompatiblePlanner:
    client: ChatClient

    @classmethod
    def from_environment(cls) -> "OpenAICompatiblePlanner":
        base_url = os.environ.get("LLM_BASE_URL")
        api_key = os.environ.get("LLM_API_KEY")
        model = os.environ.get("LLM_MODEL")
        missing = [
            name
            for name, value in (
                ("LLM_BASE_URL", base_url),
                ("LLM_API_KEY", api_key),
                ("LLM_MODEL", model),
            )
            if not value
        ]
        if missing:
            raise EnvironmentError("missing required environment variables: " + ", ".join(missing))
        return cls(OpenAIChatClient(base_url=base_url, api_key=api_key, model=model))

    def plan_details(self, user_request: str, *, repair: bool = True) -> PlanningResult:
        messages = build_prompt_messages(user_request)
        raw_output = self.client.complete(messages)
        try:
            return parse_planning_result(raw_output)
        except ValueError as exc:
            if not repair:
                raise
            repair_messages = messages + [
                {"role": "assistant", "content": raw_output},
                {"role": "user", "content": build_repair_prompt(raw_output, str(exc))},
            ]
            repaired_output = self.client.complete(repair_messages)
            return parse_planning_result(repaired_output)

    def plan(self, user_request: str) -> str:
        return self.plan_details(user_request).action_tokens


def parse_planning_result(raw_output: str) -> PlanningResult:
    """Parse and validate the structured LLM planner response."""
    try:
        parsed = json.loads(raw_output)
    except json.JSONDecodeError as exc:
        raise ValueError("LLM output must be a JSON object") from exc

    if not isinstance(parsed, dict):
        raise ValueError("LLM output must be a JSON object")
    required_keys = {"visible_reasoning", "action_tokens"}
    if set(parsed) != required_keys:
        raise ValueError("LLM output must contain only visible_reasoning and action_tokens")

    visible_reasoning = parsed["visible_reasoning"]
    action_tokens = parsed["action_tokens"]
    if not isinstance(visible_reasoning, str) or not visible_reasoning.strip():
        raise ValueError("visible_reasoning must be a non-empty string")
    if not isinstance(action_tokens, str):
        raise ValueError("action_tokens must be a string")

    tokens = validate_sequence(action_tokens)
    return PlanningResult(
        raw_output=raw_output.strip(),
        visible_reasoning=visible_reasoning.strip(),
        action_tokens=sequence_to_text(tokens),
    )
