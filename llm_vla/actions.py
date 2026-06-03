"""Action token parsing and validation."""

from __future__ import annotations


ALLOWED_TOKENS = {"left", "right", "reset"}
MOTION_TOKENS = {"left", "right"}


def parse_sequence(sequence: str) -> list[str]:
    """Parse a space-separated action sequence."""
    if not sequence or not sequence.strip():
        raise ValueError("action sequence is empty")
    if any(char.isdigit() for char in sequence):
        raise ValueError("action sequence must use names, not digits")
    if any(char in sequence for char in "[]{}(),.;:，。；："):
        raise ValueError("action sequence must not contain punctuation or JSON")
    tokens = sequence.strip().split()
    if " ".join(tokens) != sequence.strip():
        raise ValueError("action sequence must be separated by single spaces")
    return tokens


def validate_sequence(sequence: str) -> list[str]:
    """Validate that the sequence only contains allowed tokens and required resets."""
    tokens = parse_sequence(sequence)

    for token in tokens:
        if token not in ALLOWED_TOKENS:
            raise ValueError(f"unknown action token: {token}")

    if tokens[0] == "reset":
        raise ValueError("reset may not be the first action")

    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token in MOTION_TOKENS:
            next_index = index + 1
            if next_index >= len(tokens) or tokens[next_index] != "reset":
                raise ValueError(f"{token} must be followed by reset")
            index += 2
            continue
        if token == "reset":
            previous = tokens[index - 1] if index > 0 else None
            if previous not in MOTION_TOKENS:
                raise ValueError("reset must follow left or right")
        index += 1

    return tokens


def sequence_to_text(tokens: list[str]) -> str:
    """Convert validated tokens back to the canonical output text."""
    return " ".join(tokens)
