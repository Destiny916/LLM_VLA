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

## Current Action Contract

- Valid planner output tokens: `left_2rad`, `right_2rad`, `lift_up`, `put_down`, `reset`, `hold_reset`, `stop`.
- Removed tokens: `left_circle`, `right_circle`.
- Final executable output must use action names, not `0` or `1`.
- Default binary mapping: `0 -> left_2rad reset`, `1 -> right_2rad reset`, `01 -> left_2rad right_2rad reset`.
- User-explicit temporary mapping overrides the default binary mapping for that request only.
- Mapping override affects semantic interpretation only; execution still uses validated action tokens.
- Actions are not forced to reset after every motion.
- Each task sequence must end with `reset` or `reset hold_reset`.
- `lift_up` must be followed by `put_down` before `reset`.
- `put_down` requires a previous `lift_up`; it changes the arm from lifted to down but is not the same as `reset`.
- `stop` must be standalone.
- `hold_reset` is valid as a standalone idle command, or after `reset` as the final token.

## Franka Targets

- `left_2rad`: `panda_joint1 = -2.0`.
- `right_2rad`: `panda_joint1 = +2.0`.
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

## Extension Status

- P8 status: extension spec and Chinese PROJECT_PLAN define RAG-backed task planning, task-level reset, idle hold, and conversational task editing.
- P9-task1 status: `harness/rag` knowledge files were created for action catalog, examples, task rules, state rules, safety rules, conversation memory, and two-joint policy.
- P9 status: `llm_vla.rag` implements standard-library Markdown RAG loading and keyword retrieval over `harness/rag`.
- P10 status: action contract v2 implemented for local validation, prompt contract, harness skill, and Franka joint target mapping.
- P10 correction: reset no longer forces all Franka joints to zero; only `panda_joint1` and `panda_joint2` are controlled to avoid strange reset poses.
- P11 status: `llm_vla.task_plan` and `llm_vla.task_validation` implement structured task-plan parsing, validation, and expansion.
- Next step: task 5 should introduce the robot state model.
