# LLM Prompt Contract

LLM CLI must ask the model to convert natural language into a structured JSON
object for display and execution.

Required JSON fields:

- `visible_reasoning`: one short Chinese user-facing decision summary. It is not hidden chain-of-thought.
- `action_tokens`: the only executable token sequence while the CLI still uses the legacy string path.

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
- Only `panda_joint1` and `panda_joint2` are unlocked in the current simulation action layer.
- `panda_joint1` is the base rotation joint.
- `panda_joint2` is the vertical up/down joint above the base.
- All other Franka joints are locked by keeping IsaacLab default joint targets.
- `lift_up` must be followed by `put_down` before `reset`.
- `put_down` requires a previous `lift_up` in the same task context.
- `hold_reset` is valid as a standalone idle command, or after `reset` as the final token.
- `stop` must be standalone.

Execution rule:

- CLI may display `visible_reasoning`.
- CLI must validate executable action tokens.
- CLI must send only validated executable action tokens to Isaac Sim.

Repair rule:

- If model output is invalid, the repair prompt must include the previous raw output and local validation error.
- The repair prompt must ask the model to re-output JSON with only allowed fields for the current planner path.
