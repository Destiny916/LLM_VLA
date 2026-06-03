import socket
import threading
import unittest

from llm_vla.client import send_sequence
from llm_vla.ipc import decode_request, encode_response


class ClientTests(unittest.TestCase):
    def test_send_sequence_encodes_request_and_decodes_response(self):
        host = "127.0.0.1"
        received = []
        ready = threading.Event()

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.bind((host, 0))
            port = probe.getsockname()[1]

        def server():
            with socket.create_server((host, port), backlog=1) as sock:
                ready.set()
                conn, _addr = sock.accept()
                with conn:
                    data = conn.recv(4096)
                    received.append(decode_request(data))
                    conn.sendall(encode_response("ok", executed=received[0]))

        thread = threading.Thread(target=server, daemon=True)
        thread.start()
        self.assertTrue(ready.wait(timeout=2.0))

        response = send_sequence(host, port, "left reset", timeout=2.0)

        thread.join(timeout=2.0)
        self.assertFalse(thread.is_alive())
        self.assertEqual(["left reset"], received)
        self.assertEqual({"status": "ok", "executed": "left reset"}, response)

    def test_send_sequence_rejects_invalid_sequence_before_network(self):
        with self.assertRaises(ValueError):
            send_sequence("127.0.0.1", 1, "left right", timeout=0.1)


if __name__ == "__main__":
    unittest.main()
