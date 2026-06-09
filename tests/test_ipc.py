import unittest

from llm_vla.ipc import decode_request, decode_response, encode_request, encode_response


class IpcTests(unittest.TestCase):
    def test_encode_decode_request_uses_utf8_json_line_and_validates_sequence(self):
        data = encode_request("left_2rad right_2rad reset")

        self.assertIsInstance(data, bytes)
        self.assertTrue(data.endswith(b"\n"))
        self.assertEqual("left_2rad right_2rad reset", decode_request(data))

    def test_encode_request_rejects_invalid_sequence(self):
        with self.assertRaises(ValueError):
            encode_request("left_2rad right_2rad")

    def test_decode_request_rejects_missing_or_invalid_sequence(self):
        with self.assertRaises(ValueError):
            decode_request(b'{"sequence":"0 1"}\n')

        with self.assertRaises(ValueError):
            decode_request(b'{"command":"left_2rad reset"}\n')

    def test_encode_decode_success_response(self):
        data = encode_response("ok", executed="left_2rad reset")

        self.assertTrue(data.endswith(b"\n"))
        decoded = decode_response(data)
        self.assertEqual({"status": "ok", "executed": "left_2rad reset"}, decoded)

    def test_encode_decode_error_response(self):
        data = encode_response("error", message="task sequence must end with reset or hold_reset")

        decoded = decode_response(data)
        self.assertEqual("error", decoded["status"])
        self.assertEqual("task sequence must end with reset or hold_reset", decoded["message"])

    def test_response_status_must_be_ok_or_error(self):
        with self.assertRaises(ValueError):
            encode_response("done")

        with self.assertRaises(ValueError):
            decode_response(b'{"status":"done"}\n')


if __name__ == "__main__":
    unittest.main()
