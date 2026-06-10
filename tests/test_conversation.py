import unittest

from llm_vla.conversation import ConversationMemory
from llm_vla.planner import PlanningResult


def planning_result(raw_output: str) -> PlanningResult:
    return PlanningResult(raw_output=raw_output, visible_reasoning="摘要", action_tokens="")


class ConversationMemoryTests(unittest.TestCase):
    def test_add_task_records_queue_and_returns_executable_sequence(self):
        memory = ConversationMemory()
        result = planning_result(
            """
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
        )

        update = memory.apply_planning_result(result)

        self.assertEqual("left_2rad reset hold_reset", update.action_tokens)
        self.assertEqual({"task_1"}, memory.existing_task_ids)
        self.assertEqual("task_1", memory.current_task_id)
        self.assertIn("task_1: 左转打招呼", update.queue_summary)
        self.assertIn("arm_lift=down", update.state_summary)
        self.assertIn("保持复位", update.state_summary)

    def test_modify_existing_task_replaces_queue_record_and_executes_modified_task(self):
        memory = ConversationMemory()
        memory.apply_planning_result(
            planning_result(
                """
                {
                  "visible_reasoning": "添加任务。",
                  "intent": "左转",
                  "task_operations": [
                    {
                      "operation": "add",
                      "task_id": "task_1",
                      "description": "左转",
                      "subtasks": [{"description": "左转", "action_tokens": "left_2rad"}],
                      "reset_after_task": true
                    }
                  ]
                }
                """
            )
        )

        update = memory.apply_planning_result(
            planning_result(
                """
                {
                  "visible_reasoning": "修改任务。",
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
            )
        )

        self.assertEqual("right_2rad reset hold_reset", update.action_tokens)
        self.assertIn("task_1: 右转握手", memory.queue_summary())
        self.assertNotIn("左转", memory.queue_summary())

    def test_remove_existing_task_deletes_queue_record_and_holds_reset(self):
        memory = ConversationMemory()
        memory.apply_planning_result(
            planning_result(
                """
                {
                  "visible_reasoning": "添加任务。",
                  "intent": "左转",
                  "task_operations": [
                    {
                      "operation": "add",
                      "task_id": "task_1",
                      "description": "左转",
                      "subtasks": [{"description": "左转", "action_tokens": "left_2rad"}],
                      "reset_after_task": true
                    }
                  ]
                }
                """
            )
        )

        update = memory.apply_planning_result(
            planning_result(
                """
                {
                  "visible_reasoning": "删除任务。",
                  "intent": "删除",
                  "task_operations": [
                    {
                      "operation": "remove",
                      "task_id": "task_1",
                      "description": "删除左转任务",
                      "subtasks": [],
                      "reset_after_task": false
                    }
                  ]
                }
                """
            )
        )

        self.assertEqual("hold_reset", update.action_tokens)
        self.assertEqual(set(), memory.existing_task_ids)
        self.assertIn("任务队列为空", update.queue_summary)

    def test_stop_clears_current_task_and_returns_stop(self):
        memory = ConversationMemory()
        memory.apply_planning_result(
            planning_result(
                """
                {
                  "visible_reasoning": "添加任务。",
                  "intent": "左转",
                  "task_operations": [
                    {
                      "operation": "add",
                      "task_id": "task_1",
                      "description": "左转",
                      "subtasks": [{"description": "左转", "action_tokens": "left_2rad"}],
                      "reset_after_task": true
                    }
                  ]
                }
                """
            )
        )

        update = memory.apply_planning_result(
            planning_result(
                """
                {
                  "visible_reasoning": "停止任务。",
                  "intent": "停止",
                  "task_operations": [
                    {
                      "operation": "stop",
                      "task_id": "task_1",
                      "description": "停止当前任务",
                      "subtasks": [],
                      "reset_after_task": false
                    }
                  ]
                }
                """
            )
        )

        self.assertEqual("stop", update.action_tokens)
        self.assertIsNone(memory.current_task_id)
        self.assertIn("task_status=stopped", update.state_summary)

    def test_prompt_context_describes_queue_and_robot_state(self):
        memory = ConversationMemory()
        memory.apply_planning_result(
            planning_result(
                """
                {
                  "visible_reasoning": "添加任务。",
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
            )
        )

        context = memory.prompt_context()

        self.assertIn("当前任务队列", context)
        self.assertIn("task_1", context)
        self.assertIn("当前任务", context)
        self.assertIn("机械臂状态", context)


if __name__ == "__main__":
    unittest.main()
