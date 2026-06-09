"""Franka action-token to joint-target mapping."""

from __future__ import annotations

from dataclasses import dataclass

from .actions import validate_sequence


FRANKA_JOINT_NAME = "panda_joint1"
VERTICAL_JOINT_NAME = "panda_joint2"
CONTROLLED_JOINT_NAMES = {FRANKA_JOINT_NAME, VERTICAL_JOINT_NAME}
ACTION_STEPS = 30
RESET_STEPS = 60

RESET_JOINT_TARGETS = {
    "panda_joint1": 0.0,
    "panda_joint2": 0.0,
}
LIFT_UP_JOINT_TARGETS = {
    "panda_joint2": -0.8,
}
PUT_DOWN_JOINT_TARGETS = {
    "panda_joint2": 0.0,
}
ACTION_TARGETS = {
    "left_2rad": {FRANKA_JOINT_NAME: -2.0},
    "right_2rad": {FRANKA_JOINT_NAME: 2.0},
    "lift_up": LIFT_UP_JOINT_TARGETS,
    "put_down": PUT_DOWN_JOINT_TARGETS,
    "reset": RESET_JOINT_TARGETS,
    "hold_reset": RESET_JOINT_TARGETS,
    "stop": {},
}


@dataclass(frozen=True)
class JointTargetStep:
    token: str
    joint_targets: dict[str, float]
    step_count: int


def joint_targets_for_sequence(
    sequence: str,
    action_steps: int = ACTION_STEPS,
    reset_steps: int = RESET_STEPS,
) -> list[JointTargetStep]:
    """Return joint target entries for a valid action sequence."""
    tokens = validate_sequence(sequence)
    targets: list[JointTargetStep] = []
    for token in tokens:
        step_count = reset_steps if token in {"reset", "hold_reset"} else action_steps
        targets.append(JointTargetStep(token, dict(ACTION_TARGETS[token]), step_count))
    return targets
