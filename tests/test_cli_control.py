import io
import unittest

from llm_vla.cli_control import run_cli
from llm_vla.planner import PlanningResult


class FakePlanner:
    def __init__(self):
        self.requests = []

    def plan_details(self, request):
        self.requests.append(request)
        return PlanningResult(
            raw_output='{"visible_reasoning":"用户要求左转 2rad。","action_tokens":"left_2rad reset"}',
            visible_reasoning="用户要求左转 2rad。",
            action_tokens="left_2rad reset",
        )


class CliControlTests(unittest.TestCase):
    def test_run_cli_plans_sends_sequence_and_prints_details(self):
        planner = FakePlanner()
        sent = []
        output = io.StringIO()
        inputs = iter(["左转一次", "quit"])

        exit_code = run_cli(
            planner=planner,
            send_sequence_func=lambda host, port, sequence: sent.append((host, port, sequence))
            or {"status": "ok", "executed": sequence},
            input_func=lambda prompt: next(inputs),
            output_func=lambda text: print(text, file=output),
            host="127.0.0.1",
            port=8765,
        )

        self.assertEqual(0, exit_code)
        self.assertEqual(["左转一次"], planner.requests)
        self.assertEqual([("127.0.0.1", 8765, "left_2rad reset")], sent)
        text = output.getvalue()
        self.assertIn("用户输入: 左转一次", text)
        self.assertIn('API 原始输出: {"visible_reasoning":"用户要求左转 2rad。","action_tokens":"left_2rad reset"}', text)
        self.assertIn("思考摘要: 用户要求左转 2rad。", text)
        self.assertIn("API token: left_2rad reset", text)
        self.assertIn("本地校验: ok", text)
        self.assertIn("仿真结果: ok", text)
        self.assertIn("退出 CLI", text)

    def test_run_cli_prints_simulation_error(self):
        planner = FakePlanner()
        output = io.StringIO()
        inputs = iter(["左转一次", "exit"])

        run_cli(
            planner=planner,
            send_sequence_func=lambda _host, _port, _sequence: {"status": "error", "message": "sim failed"},
            input_func=lambda prompt: next(inputs),
            output_func=lambda text: print(text, file=output),
            host="127.0.0.1",
            port=8765,
        )

        text = output.getvalue()
        self.assertIn("仿真结果: error", text)
        self.assertIn("sim failed", text)


if __name__ == "__main__":
    unittest.main()
