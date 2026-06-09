import socket
import threading
import unittest

from llm_vla.ipc import decode_response, encode_request
from llm_vla.server import handle_request, serve_forever


class ServerTests(unittest.TestCase):
    def test_handle_request_executes_valid_sequence_and_returns_ok(self):
        executed = []

        response = handle_request(
            encode_request("left_2rad reset"),
            execute_sequence=executed.append,
        )

        self.assertEqual(["left_2rad reset"], executed)
        self.assertEqual({"status": "ok", "executed": "left_2rad reset"}, decode_response(response))

    def test_handle_request_returns_error_when_executor_fails(self):
        def fail(_sequence):
            raise RuntimeError("sim failed")

        response = handle_request(encode_request("left_2rad reset"), execute_sequence=fail)

        decoded = decode_response(response)
        self.assertEqual("error", decoded["status"])
        self.assertIn("sim failed", decoded["message"])

    def test_handle_request_rejects_invalid_request_without_executing(self):
        executed = []

        response = handle_request(
            b'{"sequence":"left_2rad right_2rad"}\n',
            execute_sequence=executed.append,
        )

        decoded = decode_response(response)
        self.assertEqual([], executed)
        self.assertEqual("error", decoded["status"])
        self.assertIn("task sequence must end with reset", decoded["message"])

    def test_serve_forever_handles_one_json_line_request(self):
        executed = []
        ready = threading.Event()
        host = "127.0.0.1"

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.bind((host, 0))
            port = probe.getsockname()[1]

        thread = threading.Thread(
            target=serve_forever,
            kwargs={
                "host": host,
                "port": port,
                "execute_sequence": executed.append,
                "ready_event": ready,
                "max_requests": 1,
            },
            daemon=True,
        )
        thread.start()
        self.assertTrue(ready.wait(timeout=2.0))

        with socket.create_connection((host, port), timeout=2.0) as client:
            client.sendall(encode_request("right_2rad reset"))
            response = client.recv(4096)

        thread.join(timeout=2.0)
        self.assertFalse(thread.is_alive())
        self.assertEqual(["right_2rad reset"], executed)
        self.assertEqual({"status": "ok", "executed": "right_2rad reset"}, decode_response(response))


if __name__ == "__main__":
    unittest.main()
