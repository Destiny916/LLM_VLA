# LLM Prompt Contract

LLM CLI must ask the model to convert natural language into a structured JSON
object for display and execution.

Required JSON fields:

- `visible_reasoning`: one short Chinese user-facing decision summary. It is not hidden chain-of-thought.
- `action_tokens`: the only executable token sequence.

Action rules:

- Allowed action tokens are `left`, `right`, and `reset`.
- `0 -> left reset`
- `1 -> right reset`
- `01 -> left reset right reset`
- If the user explicitly defines a temporary mapping such as `right means 0` and
  `left means 1`, that explicit user mapping has priority over the default
  binary mapping for that request only.
- Explicit mapping override changes semantic interpretation only. The executable
  output must still use `left`, `right`, and `reset` action tokens.
- Every `left` or `right` must be followed immediately by `reset`.
- `reset` may not be the first action.

Execution rule:

- CLI may display `visible_reasoning`.
- CLI must validate `action_tokens`.
- CLI must send only validated `action_tokens` to Isaac Sim.

Repair rule:

- If model output is invalid, the repair prompt must include the previous raw output and local validation error.
- The repair prompt must ask the model to re-output JSON with only `visible_reasoning` and `action_tokens`.
