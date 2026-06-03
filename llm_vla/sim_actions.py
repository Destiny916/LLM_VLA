"""Franka action-token to joint-target mapping."""

from __future__ import annotations

from .actions import validate_sequence


FRANKA_JOINT_NAME = "panda_joint1"
ACTION_STEPS = 30
RESET_STEPS = 60
ACTION_TARGETS = {
    "left": -2.0,
    "right": 2.0,
    "reset": 0.0,
}


def joint_targets_for_sequence(
    sequence: str,
    action_steps: int = ACTION_STEPS,
    reset_steps: int = RESET_STEPS,
) -> list[tuple[str, float, int]]:
    """Return `(token, joint_target_rad, step_count)` entries for a valid action sequence."""
    tokens = validate_sequence(sequence)
    return [
        (token, ACTION_TARGETS[token], reset_steps if token == "reset" else action_steps)
        for token in tokens
    ]
