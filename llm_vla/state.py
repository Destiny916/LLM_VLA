"""Robot state tracking for semantic action interpretation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from llm_vla.actions import validate_sequence


ArmLift = Literal["down", "up"]
BaseTarget = Literal["neutral", "left_2rad", "right_2rad"]
TaskStatus = Literal["idle", "running", "stopped"]


DEFAULT_ROTATION_SEMANTICS = {
    ("down", "left_2rad"): "打招呼",
    ("down", "right_2rad"): "握手",
    ("up", "left_2rad"): "泡咖啡",
    ("up", "right_2rad"): "做冰淇淋",
}
LIFTED_COMPOSITE_SEMANTICS = {
    ("left_2rad", "right_2rad", "right_2rad"): "泡浓咖啡",
    ("left_2rad", "left_2rad", "left_2rad"): "泡淡咖啡",
}
ROTATION_TOKENS = {"left_2rad", "right_2rad"}


@dataclass(frozen=True)
class RobotState:
    """Persistent high-level state for the simplified two-joint robot."""

    arm_lift: ArmLift = "down"
    base_target: BaseTarget = "neutral"
    task_status: TaskStatus = "idle"
    last_semantic: str | None = None
    semantic_history: tuple[str, ...] = ()


def apply_sequence(sequence: str, initial_state: RobotState | None = None) -> RobotState:
    """Validate and apply an executable action-token sequence."""
    tokens = validate_sequence(sequence)
    initial = initial_state or RobotState()
    arm_lift: ArmLift = initial.arm_lift
    base_target: BaseTarget = initial.base_target
    task_status: TaskStatus = initial.task_status
    semantic_history = list(initial.semantic_history)
    lifted_rotations: list[str] = []

    def flush_lifted_rotations() -> None:
        if not lifted_rotations:
            return
        semantic_history.append(_lifted_rotation_sequence_semantic(lifted_rotations))
        lifted_rotations.clear()

    for token in tokens:
        if token == "lift_up":
            flush_lifted_rotations()
            arm_lift = "up"
            task_status = "running"
            semantic_history.append("上举")
        elif token in ROTATION_TOKENS:
            task_status = "running"
            base_target = token  # type: ignore[assignment]
            if arm_lift == "up":
                lifted_rotations.append(token)
            else:
                flush_lifted_rotations()
                semantic_history.append(_rotation_semantic(arm_lift, token))
        elif token == "put_down":
            flush_lifted_rotations()
            arm_lift = "down"
            task_status = "running"
            semantic_history.append("放下")
        elif token == "reset":
            flush_lifted_rotations()
            arm_lift = "down"
            base_target = "neutral"
            task_status = "idle"
            semantic_history.append("任务复位")
        elif token == "hold_reset":
            flush_lifted_rotations()
            arm_lift = "down"
            base_target = "neutral"
            task_status = "idle"
            semantic_history.append("保持复位")
        elif token == "stop":
            flush_lifted_rotations()
            arm_lift = "down"
            base_target = "neutral"
            task_status = "stopped"
            semantic_history.append("停止任务")
        else:
            raise ValueError(f"unknown action token: {token}")

    return RobotState(
        arm_lift=arm_lift,
        base_target=base_target,
        task_status=task_status,
        last_semantic=semantic_history[-1] if semantic_history else initial.last_semantic,
        semantic_history=tuple(semantic_history),
    )


def apply_token(state: RobotState, token: str) -> RobotState:
    """Apply one already-known action token to the high-level robot state."""
    if token == "lift_up":
        return _with_semantic(state, "上举", arm_lift="up", task_status="running")
    if token == "put_down":
        return _with_semantic(state, "放下", arm_lift="down", task_status="running")
    if token == "left_2rad":
        return _with_semantic(
            state,
            _rotation_semantic(state.arm_lift, token),
            base_target="left_2rad",
            task_status="running",
        )
    if token == "right_2rad":
        return _with_semantic(
            state,
            _rotation_semantic(state.arm_lift, token),
            base_target="right_2rad",
            task_status="running",
        )
    if token == "reset":
        return _with_semantic(state, "任务复位", arm_lift="down", base_target="neutral", task_status="idle")
    if token == "hold_reset":
        return _with_semantic(state, "保持复位", arm_lift="down", base_target="neutral", task_status="idle")
    if token == "stop":
        return _with_semantic(state, "停止任务", arm_lift="down", base_target="neutral", task_status="stopped")
    raise ValueError(f"unknown action token: {token}")


def describe_sequence(sequence: str, initial_state: RobotState | None = None) -> list[str]:
    """Return the semantic labels produced by a validated sequence."""
    state = apply_sequence(sequence, initial_state=initial_state)
    return list(state.semantic_history)


def _rotation_semantic(arm_lift: ArmLift, token: str) -> str:
    try:
        return DEFAULT_ROTATION_SEMANTICS[(arm_lift, token)]
    except KeyError as exc:
        raise ValueError(f"unsupported rotation semantic for {arm_lift} {token}") from exc


def _lifted_rotation_sequence_semantic(tokens: list[str]) -> str:
    key = tuple(tokens)
    if key in LIFTED_COMPOSITE_SEMANTICS:
        return LIFTED_COMPOSITE_SEMANTICS[key]
    if len(tokens) == 1:
        return _rotation_semantic("up", tokens[0])
    return "、".join(_rotation_semantic("up", token) for token in tokens)


def _with_semantic(
    state: RobotState,
    semantic: str,
    *,
    arm_lift: ArmLift | None = None,
    base_target: BaseTarget | None = None,
    task_status: TaskStatus | None = None,
) -> RobotState:
    return RobotState(
        arm_lift=arm_lift or state.arm_lift,
        base_target=base_target or state.base_target,
        task_status=task_status or state.task_status,
        last_semantic=semantic,
        semantic_history=state.semantic_history + (semantic,),
    )
