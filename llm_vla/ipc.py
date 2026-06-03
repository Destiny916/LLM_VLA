"""JSON-line IPC helpers for LLM CLI and Isaac Sim server."""

from __future__ import annotations

import json
from typing import Any

from .actions import sequence_to_text, validate_sequence


VALID_RESPONSE_STATUSES = {"ok", "error"}


def encode_request(sequence: str) -> bytes:
    """Encode a validated action sequence request as UTF-8 JSON line."""
    tokens = validate_sequence(sequence)
    return _encode_json_line({"sequence": sequence_to_text(tokens)})


def decode_request(data: bytes) -> str:
    """Decode a UTF-8 JSON-line request and return the validated sequence."""
    payload = _decode_json_line(data)
    sequence = payload.get("sequence")
    if not isinstance(sequence, str):
        raise ValueError("request must contain string field: sequence")
    tokens = validate_sequence(sequence)
    return sequence_to_text(tokens)


def encode_response(status: str, **fields: Any) -> bytes:
    """Encode an IPC response as UTF-8 JSON line."""
    if status not in VALID_RESPONSE_STATUSES:
        raise ValueError("response status must be ok or error")
    payload = {"status": status, **fields}
    return _encode_json_line(payload)


def decode_response(data: bytes) -> dict[str, Any]:
    """Decode and validate an IPC response."""
    payload = _decode_json_line(data)
    status = payload.get("status")
    if status not in VALID_RESPONSE_STATUSES:
        raise ValueError("response status must be ok or error")
    return payload


def _encode_json_line(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def _decode_json_line(data: bytes) -> dict[str, Any]:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("IPC data must be UTF-8") from exc
    if not text.endswith("\n"):
        raise ValueError("IPC message must end with newline")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError("IPC message must be JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("IPC message must be a JSON object")
    return payload
