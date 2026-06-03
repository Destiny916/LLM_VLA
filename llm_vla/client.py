"""Client helpers for sending validated action sequences to the sim server."""

from __future__ import annotations

import socket
from typing import Any

from .ipc import decode_response, encode_request


def send_sequence(host: str, port: int, sequence: str, *, timeout: float = 10.0) -> dict[str, Any]:
    """Send one validated action sequence to the persistent simulation server."""
    request = encode_request(sequence)
    with socket.create_connection((host, port), timeout=timeout) as conn:
        conn.sendall(request)
        response = _recv_json_line(conn)
    return decode_response(response)


def _recv_json_line(conn: socket.socket, *, chunk_size: int = 4096) -> bytes:
    chunks: list[bytes] = []
    while True:
        chunk = conn.recv(chunk_size)
        if not chunk:
            break
        chunks.append(chunk)
        if b"\n" in chunk:
            break
    return b"".join(chunks)
