"""Franka action-token to joint-target mapping."""

from __future__ import annotations

from .actions import validate_sequence


FRANKA_JOINT_NAME = "panda_joint1"
ACTION_STEPS = 30
ACTION_TARGETS = {
    "left": -1.57079632679,
    "right": 1.57079632679,
    "reset": 0.0,
}


def joint_targets_for_sequence(sequence: str, action_steps: int = ACTION_STEPS) -> list[tuple[str, float, int]]:
    """Return `(token, joint_target_rad, step_count)` entries for a valid action sequence."""
    tokens = validate_sequence(sequence)
    return [(token, ACTION_TARGETS[token], action_steps) for token in tokens]
