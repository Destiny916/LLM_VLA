# LLM Prompt Contract

LLM CLI must ask the model to convert natural language into a structured JSON
object for display and execution.

Preferred task-plan JSON fields:

- `visible_reasoning`: one short Chinese user-facing decision summary. It is not hidden chain-of-thought.
- `intent`: user intent summary.
- `task_operations`: structured task operations containing `operation`, `task_id`, `description`, `subtasks`, and `reset_after_task`.

Conversation context:

- CLI provides current task queue, current task ID, and robot state as conversation context.
- The model should use that context to resolve phrases such as `刚才的任务`, `当前任务`, `删除这个任务`, and `继续`.
- Reference operations `modify`, `remove`, and `stop` must use an existing `task_id` from the context or the current task ID.
- The model must not invent a reference task ID when the context does not contain one.

Legacy JSON fields are still accepted for compatibility:

- `visible_reasoning`
- `action_tokens`

Action rules:

- Allowed action tokens are `left_2rad`, `right_2rad`, `lift_up`, `put_down`, `reset`, `hold_reset`, and `stop`.
- `left_circle` and `right_circle` were removed and must not be emitted.
- `0 -> left_2rad reset`
- `1 -> right_2rad reset`
- `01 -> left_2rad right_2rad reset`
- If the user explicitly defines a temporary mapping such as `right means 0` and
  `left means 1`, that explicit user mapping has priority over the default
  binary mapping for that request only.
- Explicit mapping override changes semantic interpretation only. The executable
  output must still use allowed action tokens.
- Actions are not forced to reset after every motion.
- Each task sequence must end with `reset` or `reset hold_reset`.
- For multiple tasks, output task actions, then `reset`, then the next task actions.
- `hold_reset` is only for idle or all-tasks-complete state; it does not replace per-task `reset`.
- Only `panda_joint1` and `panda_joint2` are unlocked in the current simulation action layer.
- `panda_joint1` is the base rotation joint.
- `panda_joint2` is the vertical up/down joint above the base.
- All other Franka joints are locked by keeping IsaacLab default joint targets.
- In the default down state, `left_2rad` means `打招呼`.
- In the default down state, `right_2rad` means `握手`.
- In the lifted state, `left_2rad` means `泡咖啡`.
- In the lifted state, `right_2rad` means `做冰淇淋`.
- In the lifted state, `left_2rad right_2rad right_2rad` means `泡浓咖啡`.
- In the lifted state, `left_2rad left_2rad left_2rad` means `泡淡咖啡`.
- `lift_up` must be followed by `put_down` before `reset`.
- `put_down` requires a previous `lift_up` in the same task context.
- `hold_reset` is valid as a standalone idle command, or after `reset` as the final token.
- `stop` must be standalone.

Execution rule:

- CLI may display `visible_reasoning`.
- CLI must validate executable action tokens.
- CLI must send only validated executable action tokens to Isaac Sim.
- CLI displays task operation summary, current task queue, and robot state after applying a planner result.

Repair rule:

- If model output is invalid, the repair prompt must include the previous raw output and local validation error.
- The repair prompt must ask the model to re-output JSON with only allowed fields for the current planner path.
