# LLM_VLA

LLM_VLA is a minimal LLM-planned robot action demo for Isaac Sim.

The project has two layers:

- LLM planner: reads `harness/` rules and emits validated action tokens.
- Isaac Sim runner: maps validated action tokens to Franka Panda joint targets.

## Rules

- Read `harness/README.md` before every project conversation or change.
- Use branch `codex` for commits.
- Do not commit automatically. Ask the user before every commit.
- Do not write real API keys into files or commits.

## Action Contract

Valid action tokens:

```text
left_2rad right_2rad lift_up put_down reset hold_reset stop
```

Removed action tokens:

```text
left_circle right_circle
```

Key rules:

- Only `panda_joint1` and `panda_joint2` are unlocked.
- Other Franka joints keep IsaacLab default joint targets.
- `left_2rad` and `right_2rad` rotate the base joint by `-2.0/+2.0` rad.
- In the down state, `left_2rad` means `打招呼` and `right_2rad` means `握手`.
- In the lifted state, `left_2rad` means `泡咖啡` and `right_2rad` means `做冰淇淋`.
- In the lifted state, `left_2rad right_2rad right_2rad` means `泡浓咖啡`.
- In the lifted state, `left_2rad left_2rad left_2rad` means `泡淡咖啡`.
- `lift_up` and `put_down` only move `panda_joint2`.
- Actions are not forced to reset after every motion.
- A task sequence must end with `reset` or `reset hold_reset`.
- Several tasks execute with a reset boundary between tasks.
- `lift_up` must be followed by `put_down` before `reset`.
- `stop` must be standalone.

## Quick Checks

```powershell
python harness\scripts\check_harness.py
D:\il\env\Scripts\python.exe -m pytest tests -v
```

## Mock Planner

```powershell
python -m llm_vla.plan "输出 01 的动作" `
  --mock-output '{"visible_reasoning":"用户要求表示 01；0 映射为 left_2rad，1 映射为 right_2rad，任务结束后复位。","action_tokens":"left_2rad right_2rad reset"}' `
  --show-details
```

## OpenAI-Compatible Planner

Set the API environment variables in PowerShell:

```powershell
$env:LLM_BASE_URL="https://api.deepseek.com"
$env:LLM_API_KEY="<local-only-api-key>"
$env:LLM_MODEL="deepseek-v4-pro"

python -m llm_vla.plan "输出 01 的动作" --show-details
```

## Isaac Sim Smoke Test

```powershell
cd D:\il\IsaacLab\scripts\LLM_VLA

D:\il\env\Scripts\python.exe -B sim\run_franka_sequence.py `
  --headless `
  --max_steps 180 `
  --sequence "lift_up left_2rad put_down right_2rad reset"
```

## Persistent Isaac Sim Server

Start the server in one terminal:

```powershell
cd D:\il\IsaacLab\scripts\LLM_VLA

D:\il\env\Scripts\python.exe -B sim\run_franka_server.py `
  --host 127.0.0.1 `
  --port 8765
```

It accepts UTF-8 JSON-line requests such as:

```json
{"sequence":"left_2rad right_2rad reset"}
```

## Interactive LLM Control CLI

Start the CLI in a second terminal after the server is listening:

```powershell
cd D:\il\IsaacLab\scripts\LLM_VLA

$env:LLM_BASE_URL="https://api.deepseek.com"
$env:LLM_API_KEY="<local-only-api-key>"
$env:LLM_MODEL="deepseek-v4-pro"

python -m llm_vla.cli_control `
  --host 127.0.0.1 `
  --port 8765
```

Then type natural-language commands such as:

```text
表示 01
机械臂上举后左转，放下后再右转
把刚才的任务改成右转握手
停止当前任务
exit
```

The CLI keeps an in-memory task queue for the current session. After each LLM
response it prints the task operation summary, current task queue, robot state,
validation result, and simulation result.
