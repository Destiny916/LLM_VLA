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
python -m llm_vla.plan "输出 01 的动作" `
  --mock-output '{"visible_reasoning":"用户要求表示 01；0 映射为 left，1 映射为 right。","action_tokens":"left reset right reset"}' `
  --show-details
```

## OpenAI-Compatible Planner

Set:

```powershell
$env:LLM_BASE_URL="https://api.deepseek.com"
$env:LLM_API_KEY="..."
$env:LLM_MODEL="deepseek-v4-pro"
python -m llm_vla.plan "输出 01 的动作" --show-details
```

The API key must be provided through the environment only. Do not write it into
project files or commits.

## Isaac Sim Smoke Test

```powershell
D:\il\env\Scripts\python.exe -B sim\run_franka_sequence.py --headless --max_steps 180 --sequence "left reset right reset"
```

## Persistent Isaac Sim Server

Start the server in one terminal:

```powershell
D:\il\env\Scripts\python.exe -B sim\run_franka_server.py `
  --host 127.0.0.1 `
  --port 8765
```

It accepts UTF-8 JSON-line requests such as:

```json
{"sequence":"left reset right reset"}
```

## Interactive LLM Control CLI

Start the CLI in a second terminal after the server is listening:

```powershell
$env:LLM_BASE_URL="https://api.deepseek.com"
$env:LLM_API_KEY="..."
$env:LLM_MODEL="deepseek-v4-pro"

python -m llm_vla.cli_control `
  --host 127.0.0.1 `
  --port 8765
```

Then type natural-language commands such as:

```text
表示 01
右转一次
exit
```
