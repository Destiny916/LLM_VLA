"""Action token parsing and validation."""

from __future__ import annotations


ALLOWED_TOKENS = {
    "left_2rad",
    "right_2rad",
    "lift_up",
    "put_down",
    "reset",
    "hold_reset",
    "stop",
}
TASK_END_TOKENS = {"reset", "hold_reset"}
PUNCTUATION = set("[]{}(),.;:，。；：")


def parse_sequence(sequence: str) -> list[str]:
    """Parse a space-separated action sequence."""
    if not sequence or not sequence.strip():
        raise ValueError("action sequence is empty")
    if any(char in PUNCTUATION for char in sequence):
        raise ValueError("action sequence must not contain punctuation or JSON")
    tokens = sequence.strip().split()
    if " ".join(tokens) != sequence.strip():
        raise ValueError("action sequence must be separated by single spaces")
    if any(token.isdigit() for token in tokens):
        raise ValueError("action sequence must use names, not digits")
    return tokens


def validate_sequence(sequence: str) -> list[str]:
    """Validate that the sequence only contains v2 tokens and a task-level reset."""
    tokens = parse_sequence(sequence)

    for token in tokens:
        if token not in ALLOWED_TOKENS:
            raise ValueError(f"unknown action token: {token}")

    if tokens == ["stop"] or tokens == ["hold_reset"]:
        return tokens

    if "stop" in tokens:
        raise ValueError("stop must be used as a standalone sequence")

    if "hold_reset" in tokens:
        if tokens[-1] != "hold_reset":
            raise ValueError("hold_reset may only appear at the end of a sequence")
        if tokens.count("hold_reset") > 1:
            raise ValueError("hold_reset may appear at most once")
        if len(tokens) < 2 or tokens[-2] != "reset":
            raise ValueError("hold_reset must follow reset after task actions")

    if tokens[-1] not in TASK_END_TOKENS:
        raise ValueError("task sequence must end with reset or hold_reset")

    _validate_lift_state(tokens)

    return tokens


def sequence_to_text(tokens: list[str]) -> str:
    """Convert validated tokens back to the canonical output text."""
    return " ".join(tokens)


def _validate_lift_state(tokens: list[str]) -> None:
    arm_lifted = False
    for token in tokens:
        if token == "lift_up":
            if arm_lifted:
                raise ValueError("lift_up cannot be repeated before put_down")
            arm_lifted = True
        elif token == "put_down":
            if not arm_lifted:
                raise ValueError("put_down requires a previous lift_up")
            arm_lifted = False
        elif token == "reset":
            if arm_lifted:
                raise ValueError("lift_up must be followed by put_down before reset")

    if arm_lifted:
        raise ValueError("lift_up must be followed by put_down")
