# Project Memory

- Project name: `LLM_VLA`.
- Goal: LLM CLI natural-language control for Isaac Sim Franka arm simulation.
- API style: OpenAI-compatible chat completions.
- Environment variables: `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`.
- Default API endpoint: `https://api.deepseek.com`.
- Default API model: `deepseek-v4-pro`.
- Never write API keys into files or commits.
- Simulation asset: IsaacLab built-in `FRANKA_PANDA_CFG`.
- Commit branch: `codex`.
- Do not commit automatically. Ask the user before every commit.

## Current Architecture

- CLI calls a real LLM API and displays API raw output, visible reasoning summary, API token result, local validation result, and simulation response.
- Visible reasoning summary is user-facing explanation only; it is not hidden chain-of-thought and must not be used as the execution source.
- Execution source is always validated action tokens or validated expanded task-plan action tokens.
- JSON-line IPC sends validated action sequences from CLI to the persistent Isaac Sim server.
- Persistent Isaac Sim server executes Franka sequences without restarting the scene.
- Persistent Isaac Sim server keeps stepping during idle time and holds the simplified arm at reset when there is no command or after all tasks are complete.
- CLI keeps conversation memory with the current task queue, current task ID, and high-level robot state.
- Each CLI turn passes `existing_task_ids`, `current_task_id`, and `conversation_context` into the planner.
- CLI displays task operation summary, current task queue, robot state, validation result, and simulation response.

## Current Action Contract

- Valid planner output tokens: `left_2rad`, `right_2rad`, `lift_up`, `put_down`, `reset`, `hold_reset`, `stop`.
- Removed tokens: `left_circle`, `right_circle`.
- Final executable output must use action names, not `0` or `1`.
- Default binary mapping: `0 -> left_2rad reset`, `1 -> right_2rad reset`, `01 -> left_2rad right_2rad reset`.
- User-explicit temporary mapping overrides the default binary mapping for that request only.
- Mapping override affects semantic interpretation only; execution still uses validated action tokens.
- Actions are not forced to reset after every motion.
- Each task sequence must end with `reset` or `reset hold_reset`.
- Multiple tasks must execute with a reset boundary between tasks: task actions, then `reset`, then the next task actions.
- `lift_up` must be followed by `put_down` before `reset`.
- `put_down` requires a previous `lift_up`; it changes the arm from lifted to down but is not the same as `reset`.
- `stop` must be standalone.
- `hold_reset` is valid as a standalone idle command, or after `reset` as the final token.

## Franka Targets

- `left_2rad`: `panda_joint1 = -2.0`.
- `right_2rad`: `panda_joint1 = +2.0`.
- Default down-state semantic: `left_2rad` means `打招呼`.
- Default down-state semantic: `right_2rad` means `握手`.
- Lifted-state semantic: `left_2rad` means `泡咖啡`.
- Lifted-state semantic: `right_2rad` means `做冰淇淋`.
- Lifted composite semantic: `left_2rad right_2rad right_2rad` means `泡浓咖啡`.
- Lifted composite semantic: `left_2rad left_2rad left_2rad` means `泡淡咖啡`.
- Current simplified arm control unlocks only `panda_joint1` and `panda_joint2`.
- All other Franka joints keep IsaacLab default joint targets and must not be directly targeted by action tokens.
- `lift_up`: vertical lifted pose using `panda_joint2` only.
- `put_down`: `panda_joint2` returns to down pose but task context is preserved.
- `reset` and `hold_reset`: `panda_joint1 = 0.0` and `panda_joint2 = 0.0`; locked joints keep default targets.
- Reset duration: default reset token execution is 60 simulation steps; default motion token execution is 30 simulation steps.

## Task Plan Contract

- `TaskPlan` contains `visible_reasoning`, `intent`, and `task_operations`.
- `TaskOperation` supports `add`, `stop`, `remove`, `modify`, and `continue`.
- `TaskOperation` includes `reset_after_task` to make the task-level reset boundary explicit.
- Action-producing operations use subtasks with executable `action_tokens`.
- Subtasks must not include `reset`, `hold_reset`, or `stop`; task-plan expansion appends task boundaries.
- `add`, `modify`, and `continue` must reset after task.
- `remove`, `modify`, and `stop` must reference an existing task or the current task.
- Expanding all action tasks appends `hold_reset` at the end.
- Idle hold is a service-layer behavior after the task queue is empty; it does not replace the required per-task `reset` boundary.
- Task-plan JSON is the preferred planner output path; legacy `visible_reasoning` and `action_tokens` JSON is retained for compatibility.
- `ConversationMemory` applies task-plan operations across turns.
- `add` appends or records a task and executes it.
- `modify` replaces an existing task and executes the modified task.
- `remove` deletes an existing task and sends `hold_reset` when there is no executable action.
- `continue` is treated as an action-producing task operation with task-level reset.
- `stop` sends standalone `stop` and clears the current task.

## Robot State Contract

- `RobotState` records `arm_lift`, `base_target`, `task_status`, `last_semantic`, and `semantic_history`.
- `arm_lift` is `down` or `up`.
- `base_target` is `neutral`, `left_2rad`, or `right_2rad`.
- `task_status` is `idle`, `running`, or `stopped`.
- `semantic_history` records the user-level meanings produced by a sequence.
- `reset` returns `arm_lift = down`, `base_target = neutral`, and `task_status = idle`.
- `hold_reset` keeps the reset idle state.
- `stop` returns to reset pose and marks `task_status = stopped`.

## Extension Status

- P8 status: extension spec and Chinese PROJECT_PLAN define RAG-backed task planning, task-level reset, idle hold, and conversational task editing.
- P9-task1 status: `harness/rag` knowledge files were created for action catalog, examples, task rules, state rules, safety rules, conversation memory, and two-joint policy.
- P9 status: `llm_vla.rag` implements standard-library Markdown RAG loading and keyword retrieval over `harness/rag`.
- P10 status: action contract v2 implemented for local validation, prompt contract, harness skill, and Franka joint target mapping.
- P10 correction: reset no longer forces all Franka joints to zero; only `panda_joint1` and `panda_joint2` are controlled to avoid strange reset poses.
- P11 status: `llm_vla.task_plan` and `llm_vla.task_validation` implement structured task-plan parsing, validation, and expansion.
- P12 status: `llm_vla.state` implements robot state tracking and semantic interpretation for greeting, handshake, coffee, and ice cream actions.
- P13 status: planner prompt injects RAG context and parser accepts task-plan JSON before expanding it to executable action tokens.
- P14 status: Isaac Sim server idle hold is implemented; the server polls for CLI requests, advances reset-hold steps when idle, and returns to idle hold after executing a sequence.
- P15 status: CLI conversation memory and task queue editing are implemented through `llm_vla.conversation`.
- Next step: task 9 should run two-window integration verification.
