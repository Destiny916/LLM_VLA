import unittest

from llm_vla.task_plan import expand_task_operation, expand_task_plan, parse_task_plan


class TaskPlanTests(unittest.TestCase):
    def test_parse_task_plan_json_with_add_operation(self):
        raw_output = """
        {
          "visible_reasoning": "用户要求上举后左转，再放下。",
          "intent": "添加一个上举状态下的左转任务",
          "task_operations": [
            {
              "operation": "add",
              "task_id": "task_1",
              "description": "上举后左转",
              "subtasks": [
                {
                  "description": "上举并左转",
                  "action_tokens": "lift_up left_2rad"
                },
                {
                  "description": "放下机械臂",
                  "action_tokens": "put_down"
                }
              ],
              "reset_after_task": true
            }
          ]
        }
        """

        plan = parse_task_plan(raw_output)

        self.assertEqual("用户要求上举后左转，再放下。", plan.visible_reasoning)
        self.assertEqual("添加一个上举状态下的左转任务", plan.intent)
        self.assertEqual(1, len(plan.task_operations))
        operation = plan.task_operations[0]
        self.assertEqual("add", operation.operation)
        self.assertEqual("task_1", operation.task_id)
        self.assertEqual("lift_up left_2rad", operation.subtasks[0].action_tokens)

    def test_expand_add_operation_appends_task_reset(self):
        plan = parse_task_plan(
            """
            {
              "visible_reasoning": "添加任务。",
              "intent": "上举后左转并放下",
              "task_operations": [
                {
                  "operation": "add",
                  "task_id": "task_1",
                  "description": "上举后左转",
                  "subtasks": [
                    {"description": "上举左转", "action_tokens": "lift_up left_2rad"},
                    {"description": "放下", "action_tokens": "put_down"}
                  ],
                  "reset_after_task": true
                }
              ]
            }
            """
        )

        sequence = expand_task_operation(plan.task_operations[0])

        self.assertEqual("lift_up left_2rad put_down reset", sequence)

    def test_expand_task_plan_enters_hold_reset_after_all_tasks(self):
        plan = parse_task_plan(
            """
            {
              "visible_reasoning": "添加两个任务。",
              "intent": "先左转再右转",
              "task_operations": [
                {
                  "operation": "add",
                  "task_id": "task_1",
                  "description": "左转",
                  "subtasks": [{"description": "左转", "action_tokens": "left_2rad"}],
                  "reset_after_task": true
                },
                {
                  "operation": "add",
                  "task_id": "task_2",
                  "description": "右转",
                  "subtasks": [{"description": "右转", "action_tokens": "right_2rad"}],
                  "reset_after_task": true
                }
              ]
            }
            """
        )

        sequence = expand_task_plan(plan)

        self.assertEqual("left_2rad reset right_2rad reset hold_reset", sequence)

    def test_stop_plan_expands_to_standalone_stop(self):
        plan = parse_task_plan(
            """
            {
              "visible_reasoning": "停止当前任务。",
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

        self.assertEqual("stop", expand_task_plan(plan, existing_task_ids={"task_1"}))


if __name__ == "__main__":
    unittest.main()
