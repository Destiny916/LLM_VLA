import os
import unittest

from llm_vla.planner import MockClient, OpenAIChatClient, OpenAICompatiblePlanner, build_prompt_messages


class RecordingClient:
    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.calls = []

    def complete(self, messages):
        self.calls.append(messages)
        if not self.outputs:
            raise AssertionError("no mock output left")
        return self.outputs.pop(0)


class PlannerTests(unittest.TestCase):
    def test_mock_planner_returns_valid_action_names_for_binary_task(self):
        planner = OpenAICompatiblePlanner(
            client=MockClient(
                '{"visible_reasoning":"用户要求表示 01，任务结束后复位。","action_tokens":"left_2rad right_2rad reset"}'
            )
        )

        self.assertEqual("left_2rad right_2rad reset", planner.plan("输出 01 的动作"))

    def test_plan_details_exposes_raw_output_reasoning_and_tokens(self):
        raw_output = '{"visible_reasoning":"用户要求右转 2rad 后复位。","action_tokens":"right_2rad reset"}'
        planner = OpenAICompatiblePlanner(client=MockClient(raw_output))

        result = planner.plan_details("右转一次")

        self.assertEqual(raw_output, result.raw_output)
        self.assertEqual("用户要求右转 2rad 后复位。", result.visible_reasoning)
        self.assertEqual("right_2rad reset", result.action_tokens)

    def test_mock_planner_rejects_invalid_model_output(self):
        planner = OpenAICompatiblePlanner(
            client=MockClient('{"visible_reasoning":"错误地输出数字。","action_tokens":"0 1"}')
        )

        with self.assertRaises(ValueError):
            planner.plan("输出 01 的动作")

    def test_planner_repairs_once_after_invalid_output(self):
        client = RecordingClient(
            [
                '{"visible_reasoning":"缺少任务级复位。","action_tokens":"left_2rad right_2rad"}',
                '{"visible_reasoning":"已修正为任务结束后复位。","action_tokens":"left_2rad right_2rad reset"}',
            ]
        )
        planner = OpenAICompatiblePlanner(client=client)

        result = planner.plan_details("先左转再右转")

        self.assertEqual("left_2rad right_2rad reset", result.action_tokens)
        self.assertEqual(2, len(client.calls))
        repair_prompt = client.calls[1][-1]["content"]
        self.assertIn("left_2rad right_2rad", repair_prompt)
        self.assertIn("left_2rad", repair_prompt)
        self.assertIn("reset", repair_prompt)
        self.assertIn("重新输出", repair_prompt)

    def test_planner_rejects_lift_up_without_put_down(self):
        planner = OpenAICompatiblePlanner(
            client=MockClient('{"visible_reasoning":"缺少放下动作。","action_tokens":"lift_up left_2rad reset"}')
        )

        with self.assertRaises(ValueError):
            planner.plan("上举后左转")

    def test_planner_rejects_removed_circle_action(self):
        planner = OpenAICompatiblePlanner(
            client=MockClient('{"visible_reasoning":"整圈动作已删除。","action_tokens":"left_circle reset"}')
        )

        with self.assertRaises(ValueError):
            planner.plan("左转一圈")

    def test_planner_rejects_non_json_model_output(self):
        planner = OpenAICompatiblePlanner(client=MockClient("left_2rad reset"))

        with self.assertRaises(ValueError):
            planner.plan_details("左转")

    def test_prompt_reads_harness_context(self):
        messages = build_prompt_messages("输出 01 的动作")
        system_content = messages[0]["content"]

        self.assertIn("left_2rad", system_content)
        self.assertIn("right_2rad", system_content)
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

    def test_environment_client_uses_configured_deepseek_endpoint_and_model(self):
        old_values = {key: os.environ.get(key) for key in ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL")}
        os.environ["LLM_BASE_URL"] = "https://api.deepseek.com"
        os.environ["LLM_API_KEY"] = "test-key"
        os.environ["LLM_MODEL"] = "deepseek-v4-pro"
        try:
            planner = OpenAICompatiblePlanner.from_environment()
        finally:
            for key, value in old_values.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

        self.assertIsInstance(planner.client, OpenAIChatClient)
        self.assertEqual("https://api.deepseek.com", planner.client.base_url)
        self.assertEqual("deepseek-v4-pro", planner.client.model)


if __name__ == "__main__":
    unittest.main()
