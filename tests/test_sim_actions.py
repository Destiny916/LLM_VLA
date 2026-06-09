import unittest

from llm_vla.sim_actions import (
    ACTION_STEPS,
    CONTROLLED_JOINT_NAMES,
    FRANKA_JOINT_NAME,
    RESET_JOINT_TARGETS,
    RESET_STEPS,
    joint_targets_for_sequence,
)


class SimActionTests(unittest.TestCase):
    def test_joint_targets_map_2rad_actions_and_task_reset(self):
        targets = joint_targets_for_sequence("left_2rad right_2rad reset")

        self.assertEqual(FRANKA_JOINT_NAME, "panda_joint1")
        self.assertEqual({"panda_joint1", "panda_joint2"}, CONTROLLED_JOINT_NAMES)
        self.assertEqual(
            [
                ("left_2rad", {"panda_joint1": -2.0}, ACTION_STEPS),
                ("right_2rad", {"panda_joint1": 2.0}, ACTION_STEPS),
                ("reset", RESET_JOINT_TARGETS, RESET_STEPS),
            ],
            [(step.token, step.joint_targets, step.step_count) for step in targets],
        )

    def test_removed_circle_actions_are_rejected(self):
        with self.assertRaises(ValueError):
            joint_targets_for_sequence("left_circle reset")
        with self.assertRaises(ValueError):
            joint_targets_for_sequence("right_circle reset")

    def test_lift_up_and_put_down_only_use_vertical_joint(self):
        targets = joint_targets_for_sequence("lift_up put_down reset")

        lift = targets[0]
        put_down = targets[1]
        self.assertEqual("lift_up", lift.token)
        self.assertEqual({"panda_joint2"}, set(lift.joint_targets))
        self.assertEqual("put_down", put_down.token)
        self.assertEqual({"panda_joint2"}, set(put_down.joint_targets))
        self.assertEqual(0.0, put_down.joint_targets["panda_joint2"])

    def test_all_actions_only_target_unlocked_two_joints(self):
        targets = joint_targets_for_sequence("lift_up left_2rad put_down right_2rad reset hold_reset")

        for target_step in targets:
            self.assertLessEqual(set(target_step.joint_targets), CONTROLLED_JOINT_NAMES)

    def test_joint_targets_reject_invalid_sequence(self):
        with self.assertRaises(ValueError):
            joint_targets_for_sequence("left_2rad right_2rad")


if __name__ == "__main__":
    unittest.main()
