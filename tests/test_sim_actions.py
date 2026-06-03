import unittest

from llm_vla.sim_actions import ACTION_STEPS, FRANKA_JOINT_NAME, joint_targets_for_sequence


class SimActionTests(unittest.TestCase):
    def test_joint_targets_map_left_reset_right_reset(self):
        targets = joint_targets_for_sequence("left reset right reset")

        self.assertEqual(FRANKA_JOINT_NAME, "panda_joint1")
        self.assertEqual(
            [
                ("left", -1.57079632679, ACTION_STEPS),
                ("reset", 0.0, ACTION_STEPS),
                ("right", 1.57079632679, ACTION_STEPS),
                ("reset", 0.0, ACTION_STEPS),
            ],
            targets,
        )

    def test_joint_targets_reject_invalid_sequence(self):
        with self.assertRaises(ValueError):
            joint_targets_for_sequence("left right")


if __name__ == "__main__":
    unittest.main()
