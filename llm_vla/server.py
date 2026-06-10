"""Persistent JSON-line TCP server helpers for simulation execution."""

from __future__ import annotations

import socket
import threading
from collections.abc import Callable

from .ipc import decode_request, encode_response


ExecuteSequence = Callable[[str], None]
IdleFunc = Callable[[], None]


def handle_request(data: bytes, execute_sequence: ExecuteSequence) -> bytes:
    """Decode, execute, and encode a response for one IPC request."""
    try:
        sequence = decode_request(data)
        execute_sequence(sequence)
    except Exception as exc:
        return encode_response("error", message=str(exc))
    return encode_response("ok", executed=sequence)


def serve_forever(
    host: str,
    port: int,
    execute_sequence: ExecuteSequence,
    *,
    ready_event: threading.Event | None = None,
    max_requests: int | None = None,
    backlog: int = 1,
    idle_func: IdleFunc | None = None,
    poll_interval: float = 0.05,
    stop_event: threading.Event | None = None,
) -> None:
    """Serve JSON-line requests and optionally run an idle hook between requests."""
    handled = 0
    with socket.create_server((host, port), backlog=backlog) as server:
        if idle_func is not None or stop_event is not None:
            server.settimeout(poll_interval)
        if ready_event is not None:
            ready_event.set()
        while max_requests is None or handled < max_requests:
            if stop_event is not None and stop_event.is_set():
                break
            try:
                conn, _addr = server.accept()
            except TimeoutError:
                if idle_func is not None:
                    idle_func()
                continue
            with conn:
                data = _recv_json_line(conn)
                conn.sendall(handle_request(data, execute_sequence))
            handled += 1


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
