# LLM_VLA

LLM_VLA is a minimal LLM-planned robot action demo for Isaac Sim.

The project has two layers:

- LLM planner: reads `harness/` rules and emits only valid action tokens.
- Isaac Sim runner: maps `left reset right reset` to Franka Panda `panda_joint1` targets.

## Rules

- Read `harness/README.md` before every project conversation or change.
- Use branch `codex` for commits.
- Do not commit automatically. Ask the user before every commit.
- Valid action tokens are `left`, `right`, and `reset`.
- Every `left` or `right` must be followed by `reset`.

## Quick Checks

```powershell
python harness\scripts\check_harness.py
python -m unittest discover -s tests -v
```

## Mock Planner

```powershell
python -m llm_vla.plan "输出 01 的动作" --mock-output "left reset right reset"
```

## OpenAI-Compatible Planner

Set:

```powershell
$env:LLM_BASE_URL="https://api.openai.com/v1"
$env:LLM_API_KEY="..."
$env:LLM_MODEL="..."
python -m llm_vla.plan "输出 01 的动作"
```

## Isaac Sim Smoke Test

```powershell
D:\il\env\Scripts\python.exe -B sim\run_franka_sequence.py --headless --max_steps 120 --sequence "left reset right reset"
```
