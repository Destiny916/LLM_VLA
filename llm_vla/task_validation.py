"""Validation rules for structured LLM task plans."""

from __future__ import annotations

from llm_vla.actions import ALLOWED_TOKENS, parse_sequence, validate_sequence
from llm_vla.task_plan import ACTION_OPERATIONS, TaskOperation, TaskPlan


REFERENCE_OPERATIONS = {"remove", "modify", "stop"}
BOUNDARY_TOKENS = {"reset", "hold_reset", "stop"}


def validate_task_plan(
    plan: TaskPlan,
    *,
    existing_task_ids: set[str] | frozenset[str] | None = None,
    current_task_id: str | None = None,
) -> TaskPlan:
    """Validate task-plan semantics before expansion or execution."""
    known_task_ids = set(existing_task_ids or set())
    if current_task_id:
        known_task_ids.add(current_task_id)

    for operation in plan.task_operations:
        _validate_task_reference(operation, known_task_ids)
        if operation.operation in ACTION_OPERATIONS:
            _validate_action_operation(operation)
        elif operation.subtasks:
            raise ValueError(f"{operation.operation} operation must not include subtasks")

    return plan


def _validate_task_reference(operation: TaskOperation, known_task_ids: set[str]) -> None:
    if not operation.task_id:
        raise ValueError("task operation must include task_id")

    if operation.operation in REFERENCE_OPERATIONS and operation.task_id not in known_task_ids:
        raise ValueError(f"{operation.operation} references unknown task_id: {operation.task_id}")


def _validate_action_operation(operation: TaskOperation) -> None:
    if not operation.reset_after_task:
        raise ValueError(f"{operation.operation} operation must reset after task")
    if not operation.subtasks:
        raise ValueError(f"{operation.operation} operation must include at least one subtask")

    task_tokens: list[str] = []
    for subtask in operation.subtasks:
        tokens = parse_sequence(subtask.action_tokens)
        for token in tokens:
            if token not in ALLOWED_TOKENS:
                raise ValueError(f"unknown action token: {token}")
            if token in BOUNDARY_TOKENS:
                raise ValueError("subtask action_tokens must not include reset, hold_reset, or stop")
        task_tokens.extend(tokens)

    validate_sequence(" ".join(task_tokens + ["reset"]))
