import unittest

from llm_vla.sim_actions import ACTION_STEPS, FRANKA_JOINT_NAME, RESET_STEPS, joint_targets_for_sequence


class SimActionTests(unittest.TestCase):
    def test_joint_targets_map_left_reset_right_reset(self):
        targets = joint_targets_for_sequence("left reset right reset")

        self.assertEqual(FRANKA_JOINT_NAME, "panda_joint1")
        self.assertEqual(
            [
                ("left", -2.0, ACTION_STEPS),
                ("reset", 0.0, RESET_STEPS),
                ("right", 2.0, ACTION_STEPS),
                ("reset", 0.0, RESET_STEPS),
            ],
            targets,
        )

    def test_custom_reset_steps_are_used_only_for_reset_tokens(self):
        targets = joint_targets_for_sequence("left reset", action_steps=10, reset_steps=25)

        self.assertEqual([("left", -2.0, 10), ("reset", 0.0, 25)], targets)

    def test_joint_targets_reject_invalid_sequence(self):
        with self.assertRaises(ValueError):
            joint_targets_for_sequence("left right")


if __name__ == "__main__":
    unittest.main()
