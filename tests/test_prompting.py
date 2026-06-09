import unittest
from pathlib import Path

from llm_vla.prompting import build_repair_prompt, build_system_prompt


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class PromptingTests(unittest.TestCase):
    def test_system_prompt_contains_json_response_contract_and_action_rules(self):
        harness_context = "Rule 1\nOutput Contract\nFranka skill"

        prompt = build_system_prompt(harness_context)

        for text in ("left_2rad", "right_2rad", "reset", "lift_up", "put_down"):
            self.assertIn(text, prompt)
        self.assertNotIn("left_circle：", prompt)
        self.assertNotIn("right_circle：", prompt)
        self.assertIn("left_circle 和 right_circle 已删除", prompt)
        self.assertIn("visible_reasoning", prompt)
        self.assertIn("action_tokens", prompt)
        self.assertIn("JSON", prompt)
        self.assertIn("只包含两个字段", prompt)
        self.assertIn("简短中文可见决策摘要", prompt)
        self.assertIn("不是隐藏链式思考", prompt)
        self.assertIn("0 -> left_2rad reset", prompt)
        self.assertIn("1 -> right_2rad reset", prompt)
        self.assertIn("panda_joint1", prompt)
        self.assertIn("panda_joint2", prompt)
        self.assertIn("其它 Franka 关节必须锁定", prompt)
        self.assertIn("动作之间不再强制 reset", prompt)
        self.assertIn(harness_context, prompt)

    def test_repair_prompt_contains_previous_output_error_and_retry_rules(self):
        prompt = build_repair_prompt(
            previous_output="lift_up left_2rad reset",
            error="lift_up must be followed by put_down before reset",
        )

        self.assertIn("lift_up left_2rad reset", prompt)
        self.assertIn("lift_up must be followed by put_down before reset", prompt)
        self.assertIn("重新输出", prompt)
        self.assertIn("visible_reasoning", prompt)
        self.assertIn("action_tokens", prompt)
        self.assertIn("left_2rad right_2rad", prompt)
        self.assertIn("当前只允许控制 panda_joint1 和 panda_joint2", prompt)
        self.assertIn("left_circle 和 right_circle 已删除", prompt)
        self.assertIn("lift_up 后必须在 reset 前 put_down", prompt)
        self.assertIn("不是隐藏链式思考", prompt)

    def test_harness_prompt_contract_exists(self):
        contract = PROJECT_ROOT / "harness" / "rules" / "llm_prompt_contract.md"

        self.assertTrue(contract.is_file())
        text = contract.read_text(encoding="utf-8")
        self.assertIn("visible_reasoning", text)
        self.assertIn("action_tokens", text)
        self.assertIn("0 -> left_2rad reset", text)
        self.assertIn("1 -> right_2rad reset", text)
        self.assertIn("panda_joint1", text)
        self.assertIn("panda_joint2", text)


if __name__ == "__main__":
    unittest.main()
