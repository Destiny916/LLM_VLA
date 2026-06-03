# Project Memory

- Project name: `LLM_VLA`
- Goal: minimal LLM action planner plus Isaac Sim Franka arm simulation.
- API style: OpenAI-compatible chat completions.
- Environment variables: `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`.
- Valid planner output tokens: `left`, `right`, `reset`.
- Final model output must use action names, not `0` or `1`.
- `left` maps to binary `0`; `right` maps to binary `1`.
- Every `left` or `right` must be followed by `reset`.
- Simulation asset: IsaacLab built-in `FRANKA_PANDA_CFG`.
- Controlled joint: `panda_joint1`.
- Motion amplitude: `left` is -90 degrees and `right` is +90 degrees.
- Commit branch: `codex`.
- Do not commit automatically. Ask the user before every commit.
