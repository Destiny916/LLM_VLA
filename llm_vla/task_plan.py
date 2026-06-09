"""Structured task-plan parsing and expansion."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any


SUPPORTED_OPERATIONS = {"add", "stop", "remove", "modify", "continue"}
ACTION_OPERATIONS = {"add", "modify", "continue"}


@dataclass(frozen=True)
class Subtask:
    """One natural-language subtask and its executable action tokens."""

    description: str
    action_tokens: str


@dataclass(frozen=True)
class TaskOperation:
    """A task queue operation produced by the LLM."""

    operation: str
    task_id: str
    description: str
    subtasks: tuple[Subtask, ...]
    reset_after_task: bool = True


@dataclass(frozen=True)
class TaskPlan:
    """Top-level structured output for task queue editing."""

    visible_reasoning: str
    intent: str
    task_operations: tuple[TaskOperation, ...]


def parse_task_plan(raw_output: str) -> TaskPlan:
    """Parse LLM task-plan JSON into typed data."""
    try:
        payload = json.loads(raw_output)
    except json.JSONDecodeError as exc:
        raise ValueError(f"task plan output must be valid JSON: {exc}") from exc

    if not isinstance(payload, dict):
        raise ValueError("task plan output must be a JSON object")

    visible_reasoning = _required_string(payload, "visible_reasoning")
    intent = _required_string(payload, "intent")
    raw_operations = payload.get("task_operations")
    if not isinstance(raw_operations, list) or not raw_operations:
        raise ValueError("task_operations must be a non-empty list")

    operations = tuple(_parse_operation(item) for item in raw_operations)
    return TaskPlan(visible_reasoning=visible_reasoning, intent=intent, task_operations=operations)


def expand_task_operation(operation: TaskOperation) -> str:
    """Expand one action-producing operation into executable action tokens."""
    if operation.operation == "stop":
        return "stop"
    if operation.operation not in ACTION_OPERATIONS:
        return ""

    tokens: list[str] = []
    for subtask in operation.subtasks:
        tokens.extend(subtask.action_tokens.split())
    if operation.reset_after_task:
        tokens.append("reset")
    return " ".join(tokens)


def expand_task_plan(
    plan: TaskPlan,
    *,
    existing_task_ids: set[str] | frozenset[str] | None = None,
    current_task_id: str | None = None,
) -> str:
    """Validate and expand a task plan into the sequence sent to Isaac Sim."""
    from llm_vla.task_validation import validate_task_plan

    validate_task_plan(plan, existing_task_ids=existing_task_ids, current_task_id=current_task_id)

    sequences: list[str] = []
    for operation in plan.task_operations:
        expanded = expand_task_operation(operation)
        if expanded == "stop":
            return "stop"
        if expanded:
            sequences.append(expanded)

    if not sequences:
        return "hold_reset"
    return " ".join(sequences + ["hold_reset"])


def _parse_operation(item: Any) -> TaskOperation:
    if not isinstance(item, dict):
        raise ValueError("each task operation must be a JSON object")

    operation = _required_string(item, "operation")
    if operation not in SUPPORTED_OPERATIONS:
        raise ValueError(f"unsupported task operation: {operation}")

    task_id = _required_string(item, "task_id")
    description = _required_string(item, "description")
    subtasks = _parse_subtasks(item.get("subtasks", []))
    reset_after_task = item.get("reset_after_task", True)
    if not isinstance(reset_after_task, bool):
        raise ValueError("reset_after_task must be a boolean")

    return TaskOperation(
        operation=operation,
        task_id=task_id,
        description=description,
        subtasks=subtasks,
        reset_after_task=reset_after_task,
    )


def _parse_subtasks(raw_subtasks: Any) -> tuple[Subtask, ...]:
    if not isinstance(raw_subtasks, list):
        raise ValueError("subtasks must be a list")

    subtasks: list[Subtask] = []
    for item in raw_subtasks:
        if not isinstance(item, dict):
            raise ValueError("each subtask must be a JSON object")
        subtasks.append(
            Subtask(
                description=_required_string(item, "description"),
                action_tokens=_required_string(item, "action_tokens"),
            )
        )
    return tuple(subtasks)


def _required_string(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value.strip()
