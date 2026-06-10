"""OpenAI-compatible LLM planner."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .actions import sequence_to_text, validate_sequence
from .harness import HARNESS_DIR, read_core_harness
from .prompting import build_repair_prompt, build_system_prompt
from .rag import load_rag_documents, retrieve_context
from .task_plan import expand_task_plan, parse_task_plan


class ChatClient(Protocol):
    def complete(self, messages: list[dict[str, str]]) -> str:
        """Return raw assistant content."""


def build_prompt_messages(user_request: str, *, conversation_context: str | None = None) -> list[dict[str, str]]:
    """Build messages from harness context and the user request."""
    harness_context = read_core_harness()
    rag_context = build_rag_context(user_request)
    if rag_context:
        harness_context = harness_context + "\n\n## RAG 检索上下文\n" + rag_context
    system_content = build_system_prompt(harness_context)
    user_content = user_request
    if conversation_context:
        user_content = (
            "## 当前会话上下文\n"
            f"{conversation_context}\n\n"
            "## 用户新输入\n"
            f"{user_request}"
        )
    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]


def build_rag_context(user_request: str, *, top_k: int = 5) -> str:
    """Retrieve task-relevant harness RAG context for the prompt."""
    rag_root = Path(HARNESS_DIR) / "rag"
    if not rag_root.is_dir():
        return ""
    hits = retrieve_context(user_request, load_rag_documents(rag_root), top_k=top_k)
    if not hits:
        return ""
    lines: list[str] = []
    for hit in hits:
        lines.append(f"- {hit.path} / {hit.title}: {hit.snippet}")
    return "\n".join(lines)


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
    intent: str | None = None


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

    def plan_details(
        self,
        user_request: str,
        *,
        repair: bool = True,
        existing_task_ids: set[str] | frozenset[str] | None = None,
        current_task_id: str | None = None,
        conversation_context: str | None = None,
    ) -> PlanningResult:
        messages = build_prompt_messages(user_request, conversation_context=conversation_context)
        raw_output = self.client.complete(messages)
        try:
            return parse_planning_result(
                raw_output,
                existing_task_ids=existing_task_ids,
                current_task_id=current_task_id,
            )
        except ValueError as exc:
            if not repair:
                raise
            repair_messages = messages + [
                {"role": "assistant", "content": raw_output},
                {"role": "user", "content": build_repair_prompt(raw_output, str(exc))},
            ]
            repaired_output = self.client.complete(repair_messages)
            return parse_planning_result(
                repaired_output,
                existing_task_ids=existing_task_ids,
                current_task_id=current_task_id,
            )

    def plan(self, user_request: str) -> str:
        return self.plan_details(user_request).action_tokens


def parse_planning_result(
    raw_output: str,
    *,
    existing_task_ids: set[str] | frozenset[str] | None = None,
    current_task_id: str | None = None,
) -> PlanningResult:
    """Parse and validate the structured LLM planner response."""
    try:
        parsed = json.loads(raw_output)
    except json.JSONDecodeError as exc:
        raise ValueError("LLM output must be a JSON object") from exc

    if not isinstance(parsed, dict):
        raise ValueError("LLM output must be a JSON object")
    legacy_keys = {"visible_reasoning", "action_tokens"}
    task_plan_keys = {"visible_reasoning", "intent", "task_operations"}
    if set(parsed) == task_plan_keys:
        task_plan = parse_task_plan(raw_output)
        action_tokens = expand_task_plan(
            task_plan,
            existing_task_ids=existing_task_ids,
            current_task_id=current_task_id,
        )
        tokens = validate_sequence(action_tokens)
        return PlanningResult(
            raw_output=raw_output.strip(),
            visible_reasoning=task_plan.visible_reasoning,
            action_tokens=sequence_to_text(tokens),
            intent=task_plan.intent,
        )

    if set(parsed) != legacy_keys:
        raise ValueError("LLM output must contain task-plan fields or legacy visible_reasoning/action_tokens fields")

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
