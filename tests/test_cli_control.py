import io
import unittest

from llm_vla.cli_control import run_cli
from llm_vla.planner import PlanningResult


class FakePlanner:
    def __init__(self, results=None):
        self.requests = []
        self.calls = []
        self.results = list(results or [])

    def plan_details(self, request, **kwargs):
        self.requests.append(request)
        self.calls.append((request, kwargs))
        if self.results:
            return self.results.pop(0)
        raw_output = '{"visible_reasoning":"用户要求左转 2rad。","action_tokens":"left_2rad reset"}'
        return PlanningResult(raw_output=raw_output, visible_reasoning="用户要求左转 2rad。", action_tokens="left_2rad reset")


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

    def test_run_cli_passes_conversation_context_and_prints_queue_state(self):
        add_output = """
        {
          "visible_reasoning": "添加左转任务。",
          "intent": "左转",
          "task_operations": [
            {
              "operation": "add",
              "task_id": "task_1",
              "description": "左转打招呼",
              "subtasks": [{"description": "左转", "action_tokens": "left_2rad"}],
              "reset_after_task": true
            }
          ]
        }
        """
        modify_output = """
        {
          "visible_reasoning": "修改为右转任务。",
          "intent": "改为右转",
          "task_operations": [
            {
              "operation": "modify",
              "task_id": "task_1",
              "description": "右转握手",
              "subtasks": [{"description": "右转", "action_tokens": "right_2rad"}],
              "reset_after_task": true
            }
          ]
        }
        """
        planner = FakePlanner(
            [
                PlanningResult(add_output.strip(), "添加左转任务。", "left_2rad reset hold_reset", intent="左转"),
                PlanningResult(modify_output.strip(), "修改为右转任务。", "right_2rad reset hold_reset", intent="改为右转"),
            ]
        )
        sent = []
        output = io.StringIO()
        inputs = iter(["左转打招呼", "把刚才的任务改成右转握手", "quit"])

        run_cli(
            planner=planner,
            send_sequence_func=lambda host, port, sequence: sent.append((host, port, sequence))
            or {"status": "ok", "executed": sequence},
            input_func=lambda prompt: next(inputs),
            output_func=lambda text: print(text, file=output),
            host="127.0.0.1",
            port=8765,
        )

        self.assertEqual(
            [
                ("127.0.0.1", 8765, "left_2rad reset hold_reset"),
                ("127.0.0.1", 8765, "right_2rad reset hold_reset"),
            ],
            sent,
        )
        second_call_kwargs = planner.calls[1][1]
        self.assertEqual({"task_1"}, second_call_kwargs["existing_task_ids"])
        self.assertEqual("task_1", second_call_kwargs["current_task_id"])
        self.assertIn("task_1: 左转打招呼", second_call_kwargs["conversation_context"])
        text = output.getvalue()
        self.assertIn("当前任务队列:", text)
        self.assertIn("task_1: 右转握手", text)
        self.assertIn("机械臂状态:", text)


if __name__ == "__main__":
    unittest.main()
