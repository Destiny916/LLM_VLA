import unittest

from llm_vla.task_plan import parse_task_plan
from llm_vla.task_validation import validate_task_plan


class TaskValidationTests(unittest.TestCase):
    def test_add_operation_requires_task_level_reset(self):
        plan = parse_task_plan(
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
                  "reset_after_task": false
                }
              ]
            }
            """
        )

        with self.assertRaises(ValueError):
            validate_task_plan(plan)

    def test_rejects_removed_circle_token_inside_subtask(self):
        plan = parse_task_plan(
            """
            {
              "visible_reasoning": "整圈动作不允许。",
              "intent": "整圈",
              "task_operations": [
                {
                  "operation": "add",
                  "task_id": "task_1",
                  "description": "整圈",
                  "subtasks": [{"description": "整圈", "action_tokens": "left_circle"}],
                  "reset_after_task": true
                }
              ]
            }
            """
        )

        with self.assertRaises(ValueError):
            validate_task_plan(plan)

    def test_rejects_lift_up_without_put_down_before_task_reset(self):
        plan = parse_task_plan(
            """
            {
              "visible_reasoning": "缺少放下动作。",
              "intent": "上举左转",
              "task_operations": [
                {
                  "operation": "add",
                  "task_id": "task_1",
                  "description": "上举左转",
                  "subtasks": [{"description": "上举左转", "action_tokens": "lift_up left_2rad"}],
                  "reset_after_task": true
                }
              ]
            }
            """
        )

        with self.assertRaises(ValueError):
            validate_task_plan(plan)

    def test_remove_modify_and_stop_must_reference_known_task(self):
        for operation_name in ("remove", "modify", "stop"):
            plan = parse_task_plan(
                f"""
                {{
                  "visible_reasoning": "引用任务。",
                  "intent": "操作任务",
                  "task_operations": [
                    {{
                      "operation": "{operation_name}",
                      "task_id": "missing_task",
                      "description": "操作任务",
                      "subtasks": [],
                      "reset_after_task": false
                    }}
                  ]
                }}
                """
            )

            with self.assertRaises(ValueError):
                validate_task_plan(plan, existing_task_ids={"task_1"})

    def test_accepts_modify_when_task_exists_and_actions_are_valid(self):
        plan = parse_task_plan(
            """
            {
              "visible_reasoning": "修改已有任务。",
              "intent": "改成右转",
              "task_operations": [
                {
                  "operation": "modify",
                  "task_id": "task_1",
                  "description": "改成右转",
                  "subtasks": [{"description": "右转", "action_tokens": "right_2rad"}],
                  "reset_after_task": true
                }
              ]
            }
            """
        )

        validated = validate_task_plan(plan, existing_task_ids={"task_1"})

        self.assertIs(validated, plan)

    def test_rejects_action_boundary_tokens_inside_subtask(self):
        plan = parse_task_plan(
            """
            {
              "visible_reasoning": "子任务不能自己复位。",
              "intent": "左转",
              "task_operations": [
                {
                  "operation": "add",
                  "task_id": "task_1",
                  "description": "左转",
                  "subtasks": [{"description": "左转", "action_tokens": "left_2rad reset"}],
                  "reset_after_task": true
                }
              ]
            }
            """
        )

        with self.assertRaises(ValueError):
            validate_task_plan(plan)


if __name__ == "__main__":
    unittest.main()
