import unittest

from llm_vla.state import RobotState, apply_sequence, apply_token, describe_sequence


class RobotStateTests(unittest.TestCase):
    def test_default_state_is_idle_down_and_neutral(self):
        state = RobotState()

        self.assertEqual("down", state.arm_lift)
        self.assertEqual("neutral", state.base_target)
        self.assertEqual("idle", state.task_status)
        self.assertEqual((), state.semantic_history)

    def test_default_left_and_right_have_task_semantics(self):
        left_state = apply_sequence("left_2rad reset")
        right_state = apply_sequence("right_2rad reset")

        self.assertEqual(("打招呼", "任务复位"), left_state.semantic_history)
        self.assertEqual(("握手", "任务复位"), right_state.semantic_history)
        self.assertEqual("neutral", left_state.base_target)
        self.assertEqual("down", right_state.arm_lift)

    def test_lifted_left_and_right_have_different_task_semantics(self):
        coffee_state = apply_sequence("lift_up left_2rad put_down reset")
        ice_cream_state = apply_sequence("lift_up right_2rad put_down reset")

        self.assertEqual(("上举", "泡咖啡", "放下", "任务复位"), coffee_state.semantic_history)
        self.assertEqual(("上举", "做冰淇淋", "放下", "任务复位"), ice_cream_state.semantic_history)

    def test_apply_token_tracks_running_and_idle_status(self):
        state = RobotState()

        state = apply_token(state, "lift_up")
        self.assertEqual("up", state.arm_lift)
        self.assertEqual("running", state.task_status)

        state = apply_token(state, "right_2rad")
        self.assertEqual("right_2rad", state.base_target)
        self.assertEqual("做冰淇淋", state.last_semantic)

        state = apply_token(state, "put_down")
        self.assertEqual("down", state.arm_lift)

        state = apply_token(state, "reset")
        self.assertEqual("neutral", state.base_target)
        self.assertEqual("idle", state.task_status)

    def test_hold_reset_keeps_idle_reset_state(self):
        state = apply_sequence("left_2rad reset hold_reset")

        self.assertEqual("down", state.arm_lift)
        self.assertEqual("neutral", state.base_target)
        self.assertEqual("idle", state.task_status)
        self.assertEqual(("打招呼", "任务复位", "保持复位"), state.semantic_history)

    def test_stop_marks_state_stopped_and_reset(self):
        state = apply_sequence("stop")

        self.assertEqual("down", state.arm_lift)
        self.assertEqual("neutral", state.base_target)
        self.assertEqual("stopped", state.task_status)
        self.assertEqual(("停止任务",), state.semantic_history)

    def test_describe_sequence_returns_semantic_history(self):
        semantics = describe_sequence("lift_up right_2rad put_down reset hold_reset")

        self.assertEqual(["上举", "做冰淇淋", "放下", "任务复位", "保持复位"], semantics)

    def test_composite_lifted_rotation_sequences_have_coffee_strength_semantics(self):
        strong_state = apply_sequence("lift_up left_2rad right_2rad right_2rad put_down reset")
        light_state = apply_sequence("lift_up left_2rad left_2rad left_2rad put_down reset")

        self.assertEqual(("上举", "泡浓咖啡", "放下", "任务复位"), strong_state.semantic_history)
        self.assertEqual(("上举", "泡淡咖啡", "放下", "任务复位"), light_state.semantic_history)

    def test_invalid_sequence_is_rejected_before_state_update(self):
        with self.assertRaises(ValueError):
            apply_sequence("lift_up left_2rad reset")


if __name__ == "__main__":
    unittest.main()
