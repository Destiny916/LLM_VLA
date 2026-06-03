import os
import unittest

from llm_vla.planner import MockClient, OpenAICompatiblePlanner, build_prompt_messages


class PlannerTests(unittest.TestCase):
    def test_mock_planner_returns_valid_action_names_for_binary_task(self):
        planner = OpenAICompatiblePlanner(client=MockClient("left reset right reset"))

        self.assertEqual("left reset right reset", planner.plan("输出 01 的动作"))

    def test_mock_planner_rejects_invalid_model_output(self):
        planner = OpenAICompatiblePlanner(client=MockClient("0 1"))

        with self.assertRaises(ValueError):
            planner.plan("输出 01 的动作")

    def test_prompt_reads_harness_context(self):
        messages = build_prompt_messages("输出 01 的动作")
        system_content = messages[0]["content"]

        self.assertIn("left", system_content)
        self.assertIn("right", system_content)
        self.assertIn("reset", system_content)
        self.assertIn("Rule 1", system_content)
        self.assertEqual("输出 01 的动作", messages[1]["content"])

    def test_environment_client_requires_api_configuration(self):
        old_values = {key: os.environ.get(key) for key in ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL")}
        for key in old_values:
            os.environ.pop(key, None)
        try:
            with self.assertRaises(EnvironmentError):
                OpenAICompatiblePlanner.from_environment()
        finally:
            for key, value in old_values.items():
                if value is not None:
                    os.environ[key] = value


if __name__ == "__main__":
    unittest.main()
