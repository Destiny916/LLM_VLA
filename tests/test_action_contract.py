import unittest

from llm_vla.actions import ALLOWED_TOKENS, parse_sequence, validate_sequence


class ActionContractTests(unittest.TestCase):
    def test_valid_sequence_uses_v2_names_and_task_level_reset(self):
        sequence = "lift_up left_2rad put_down right_2rad reset hold_reset"

        tokens = parse_sequence(sequence)

        self.assertEqual(["lift_up", "left_2rad", "put_down", "right_2rad", "reset", "hold_reset"], tokens)
        self.assertEqual(tokens, validate_sequence(sequence))

    def test_allowed_tokens_are_v2_contract(self):
        self.assertEqual(
            {
                "left_2rad",
                "right_2rad",
                "lift_up",
                "put_down",
                "reset",
                "hold_reset",
                "stop",
            },
            ALLOWED_TOKENS,
        )

    def test_rejects_sequence_without_task_level_reset(self):
        with self.assertRaises(ValueError):
            validate_sequence("left_2rad right_2rad")

    def test_rejects_lift_up_without_put_down_before_reset(self):
        with self.assertRaises(ValueError):
            validate_sequence("lift_up left_2rad reset")

    def test_rejects_put_down_without_lift_up(self):
        with self.assertRaises(ValueError):
            validate_sequence("put_down left_2rad reset")

    def test_rejects_unknown_token(self):
        with self.assertRaises(ValueError):
            validate_sequence("left_2rad jump reset")

    def test_rejects_legacy_tokens(self):
        with self.assertRaises(ValueError):
            validate_sequence("left reset")

    def test_rejects_removed_circle_tokens(self):
        with self.assertRaises(ValueError):
            validate_sequence("left_circle reset")
        with self.assertRaises(ValueError):
            validate_sequence("right_circle reset")

    def test_rejects_numeric_output(self):
        with self.assertRaises(ValueError):
            validate_sequence("0 1")

    def test_stop_and_hold_reset_are_valid_standalone_control_sequences(self):
        self.assertEqual(["stop"], validate_sequence("stop"))
        self.assertEqual(["hold_reset"], validate_sequence("hold_reset"))


if __name__ == "__main__":
    unittest.main()
