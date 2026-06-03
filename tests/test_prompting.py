import unittest
from pathlib import Path

from llm_vla.prompting import build_repair_prompt, build_system_prompt


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class PromptingTests(unittest.TestCase):
    def test_system_prompt_contains_json_response_contract_and_action_rules(self):
        harness_context = "Rule 1\nOutput Contract\nFranka skill"

        prompt = build_system_prompt(harness_context)

        for text in ("left", "right", "reset"):
            self.assertIn(text, prompt)
        self.assertIn("visible_reasoning", prompt)
        self.assertIn("action_tokens", prompt)
        self.assertIn("JSON", prompt)
        self.assertIn("只包含", prompt)
        self.assertIn("简短可见决策摘要", prompt)
        self.assertIn("不是隐藏链式思考", prompt)
        self.assertIn("0 -> left reset", prompt)
        self.assertIn("1 -> right reset", prompt)
        self.assertIn(harness_context, prompt)

    def test_repair_prompt_contains_previous_output_error_and_retry_rules(self):
        prompt = build_repair_prompt(
            previous_output="left right",
            error="left must be followed by reset",
        )

        self.assertIn("left right", prompt)
        self.assertIn("left must be followed by reset", prompt)
        self.assertIn("重新输出", prompt)
        self.assertIn("visible_reasoning", prompt)
        self.assertIn("action_tokens", prompt)
        self.assertIn("left right reset", prompt)
        self.assertIn("不是隐藏链式思考", prompt)

    def test_harness_prompt_contract_exists(self):
        contract = PROJECT_ROOT / "harness" / "rules" / "llm_prompt_contract.md"

        self.assertTrue(contract.is_file())
        text = contract.read_text(encoding="utf-8")
        self.assertIn("visible_reasoning", text)
        self.assertIn("action_tokens", text)
        self.assertIn("0 -> left reset", text)
        self.assertIn("1 -> right reset", text)


if __name__ == "__main__":
    unittest.main()
