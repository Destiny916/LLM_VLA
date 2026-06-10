"""Conversation memory and task queue editing for the interactive CLI."""

from __future__ import annotations

import json
from dataclasses import dataclass

from .actions import validate_sequence
from .planner import PlanningResult
from .state import RobotState, apply_sequence
from .task_plan import ACTION_OPERATIONS, TaskOperation, expand_task_operation, parse_task_plan
from .task_validation import validate_task_plan


@dataclass(frozen=True)
class QueuedTask:
    """One remembered task in the CLI task queue."""

    task_id: str
    description: str
    action_tokens: str


@dataclass(frozen=True)
class ConversationUpdate:
    """Result of applying one planner response to the conversation memory."""

    action_tokens: str
    queue_summary: str
    state_summary: str
    operations_summary: str


class ConversationMemory:
    """Track task queue, current task, and high-level robot state across CLI turns."""

    def __init__(self) -> None:
        self._tasks: dict[str, QueuedTask] = {}
        self._task_order: list[str] = []
        self.current_task_id: str | None = None
        self.robot_state = RobotState()
        self._legacy_task_index = 0

    @property
    def existing_task_ids(self) -> set[str]:
        return set(self._task_order)

    def apply_planning_result(self, result: PlanningResult) -> ConversationUpdate:
        """Apply a validated planner result and return the sequence to execute."""
        if _looks_like_task_plan(result.raw_output):
            action_tokens, operations_summary = self._apply_task_plan_result(result.raw_output)
        else:
            action_tokens = result.action_tokens
            operations_summary = self._apply_legacy_action_result(result)

        self.robot_state = apply_sequence(action_tokens, initial_state=self.robot_state)
        return ConversationUpdate(
            action_tokens=action_tokens,
            queue_summary=self.queue_summary(),
            state_summary=self.state_summary(),
            operations_summary=operations_summary,
        )

    def prompt_context(self) -> str:
        """Return compact context for the next LLM request."""
        return "\n".join(
            (
                "当前任务队列:",
                self.queue_summary(),
                f"当前任务: {self.current_task_id or '无'}",
                "机械臂状态:",
                self.state_summary(),
            )
        )

    def queue_summary(self) -> str:
        if not self._task_order:
            return "任务队列为空"
        return "\n".join(
            f"- {task_id}: {self._tasks[task_id].description} | actions={self._tasks[task_id].action_tokens}"
            for task_id in self._task_order
        )

    def state_summary(self) -> str:
        state = self.robot_state
        last_semantic = state.last_semantic or "无"
        return (
            f"arm_lift={state.arm_lift}, base_target={state.base_target}, "
            f"task_status={state.task_status}, last_semantic={last_semantic}"
        )

    def _apply_task_plan_result(self, raw_output: str) -> tuple[str, str]:
        plan = parse_task_plan(raw_output)
        validate_task_plan(
            plan,
            existing_task_ids=self.existing_task_ids,
            current_task_id=self.current_task_id,
        )

        sequences: list[str] = []
        summaries: list[str] = []
        for operation in plan.task_operations:
            if operation.operation == "stop":
                self.current_task_id = None
                summaries.append(f"stop {operation.task_id}")
                return "stop", "；".join(summaries)
            if operation.operation == "remove":
                self._remove_task(operation.task_id)
                summaries.append(f"remove {operation.task_id}")
                continue
            if operation.operation in ACTION_OPERATIONS:
                task_sequence = expand_task_operation(operation)
                self._upsert_task(operation, task_sequence)
                sequences.append(task_sequence)
                summaries.append(f"{operation.operation} {operation.task_id}")

        if not sequences:
            return "hold_reset", "；".join(summaries) if summaries else "hold_reset"
        return " ".join(sequences + ["hold_reset"]), "；".join(summaries)

    def _apply_legacy_action_result(self, result: PlanningResult) -> str:
        tokens = validate_sequence(result.action_tokens)
        self._legacy_task_index += 1
        task_id = f"legacy_{self._legacy_task_index}"
        task = QueuedTask(task_id=task_id, description=result.visible_reasoning, action_tokens=" ".join(tokens))
        self._tasks[task_id] = task
        self._task_order.append(task_id)
        self.current_task_id = task_id
        return f"add {task_id}"

    def _upsert_task(self, operation: TaskOperation, action_tokens: str) -> None:
        task = QueuedTask(
            task_id=operation.task_id,
            description=operation.description,
            action_tokens=action_tokens,
        )
        if operation.task_id not in self._tasks:
            self._task_order.append(operation.task_id)
        self._tasks[operation.task_id] = task
        self.current_task_id = operation.task_id

    def _remove_task(self, task_id: str) -> None:
        self._tasks.pop(task_id, None)
        self._task_order = [existing_id for existing_id in self._task_order if existing_id != task_id]
        if self.current_task_id == task_id:
            self.current_task_id = self._task_order[-1] if self._task_order else None


def _looks_like_task_plan(raw_output: str) -> bool:
    try:
        payload = json.loads(raw_output)
    except json.JSONDecodeError:
        return False
    return isinstance(payload, dict) and "task_operations" in payload
