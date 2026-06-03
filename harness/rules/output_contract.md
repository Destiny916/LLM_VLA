# Output Contract

LLM planner output must be a space-separated sequence of action names.

Allowed tokens:

- `left`
- `right`
- `reset`

Rules:

- `left` means Franka `panda_joint1 = -1.57079632679 rad` (-90 degrees).
- `right` means Franka `panda_joint1 = +1.57079632679 rad` (+90 degrees).
- `reset` means Franka `panda_joint1 = 0.0 rad`.
- Every `left` or `right` must be followed immediately by `reset`.
- `reset` may not appear as the first action.
- Output must not contain digits, JSON, punctuation, Chinese explanation, or extra text.
