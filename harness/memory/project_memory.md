# Project Memory

- Project name: `LLM_VLA`
- Goal: LLM CLI natural-language control for Isaac Sim Franka arm simulation.
- API style: OpenAI-compatible chat completions.
- Environment variables: `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`.
- Valid planner output tokens: `left`, `right`, `reset`.
- Final model output must use action names, not `0` or `1`.
- `left` maps to binary `0`; `right` maps to binary `1`.
- Every `left` or `right` must be followed by `reset`.
- Simulation asset: IsaacLab built-in `FRANKA_PANDA_CFG`.
- Controlled joint: `panda_joint1`.
- Motion amplitude: `left` is -90 degrees and `right` is +90 degrees.
- Action layer status: `left`, `right`, and `reset` execution is already implemented.
- Current architecture target: a CLI window calls a real LLM API, shows API raw output, visible reasoning summary, API token result, local validation result, and sends validated tokens to a persistent Isaac Sim server window.
- Visible reasoning summary is user-facing explanation only; it is not hidden chain-of-thought and must not be used as the execution source.
- Execution source is always validated `action_tokens`.
- Commit branch: `codex`.
- Do not commit automatically. Ask the user before every commit.
