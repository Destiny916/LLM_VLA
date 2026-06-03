import unittest

from llm_vla.actions import parse_sequence, validate_sequence


class ActionContractTests(unittest.TestCase):
    def test_valid_sequence_uses_names_and_reset_after_each_motion(self):
        tokens = parse_sequence("left reset right reset")

        self.assertEqual(["left", "reset", "right", "reset"], tokens)
        self.assertEqual(["left", "reset", "right", "reset"], validate_sequence("left reset right reset"))

    def test_rejects_missing_reset_after_motion(self):
        with self.assertRaises(ValueError):
            validate_sequence("left right")

    def test_rejects_unknown_token(self):
        with self.assertRaises(ValueError):
            validate_sequence("left reset jump reset")

    def test_rejects_numeric_output(self):
        with self.assertRaises(ValueError):
            validate_sequence("0 1")


if __name__ == "__main__":
    unittest.main()
