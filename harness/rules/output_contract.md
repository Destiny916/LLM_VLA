# Output Contract

The execution output sent to Isaac Sim must be a space-separated sequence of action names.

For the future LLM CLI, the API may return a structured JSON object with:

- `visible_reasoning`: a short user-facing decision summary, not hidden chain-of-thought.
- `action_tokens`: the only field used for execution.

Only `action_tokens` may be passed to `validate_sequence()` and then to Isaac Sim.

Allowed tokens:

- `left`
- `right`
- `reset`

Rules:

- `left` means Franka `panda_joint1 = -2.0 rad`.
- `right` means Franka `panda_joint1 = +2.0 rad`.
- `reset` means Franka `panda_joint1 = 0.0 rad`.
- Default motion actions run for 30 simulation steps.
- Default `reset` actions run for 60 simulation steps.
- Every `left` or `right` must be followed immediately by `reset`.
- `reset` may not appear as the first action.
- The execution token sequence must not contain digits, JSON, punctuation, Chinese explanation, or extra text.
- CLI must display API raw output, visible reasoning summary, API token result, local validation result, and simulation result.
