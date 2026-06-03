# LLM_VLA 最小实现规格说明

> 当前版本：P4 integration tests and verification  
> 项目根目录：`D:/il/IsaacLab/scripts/LLM_VLA`  
> 目标仓库：`https://github.com/Destiny916/LLM_VLA.git`  
> Git 分支：`codex`

## 1. 项目目标

`LLM_VLA` 是一个最小版的 LLM 机器人动作规划与 Isaac Sim 机械臂仿真项目。它验证的核心想法是：大模型不直接输出底层力矩或连续控制量，而是读取 `harness` 中定义的 skill、规则和记忆，只输出可验证的离散动作 token 序列，再由本地规则校验层和 Isaac Sim 执行层落地。

当前项目只实现一个最小闭环：

```text
用户自然语言
  -> OpenAI-compatible LLM planner
  -> 动作 token 序列
  -> 本地动作合同校验
  -> Franka Panda 机械臂仿真执行
```

本版本不训练模型，不接真实机械臂，不实现视觉输入，也不实现连续 VLA action head。它只验证“LLM 通过规则组合已有 skill，再交给仿真控制器执行”的最小路径。

## 2. 系统边界

### 2.1 范围内

- 使用 OpenAI-compatible Chat Completions API 作为 LLM planner。
- 每次 planner 请求前读取 `harness` 核心文件。
- 限制 LLM 最终输出只能包含动作名称。
- 校验动作 token、空格格式和复位规则。
- 使用 IsaacLab 内置 `FRANKA_PANDA_CFG` 加载 Franka Panda 机械臂。
- 将 `left`、`right`、`reset` 映射为 `panda_joint1` 的关节位置目标。
- 提供 mock planner，便于无 API key 时测试。
- 提供 headless Isaac Sim smoke test。

### 2.2 范围外

- 不做真实机器人控制。
- 不采集机器人数据。
- 不训练 VLA、Diffusion Policy、ACT 或 RL 策略。
- 不读取摄像头图像或机器人状态作为 LLM 输入。
- 不让 LLM 输出 Python 代码、JSON、坐标、关节数组或自由文本解释。

## 3. Harness 规则

`harness` 是项目的控制层。每次关于 `LLM_VLA` 的对话、分析、修改、测试、运行或 Git 提交前，必须先读取以下文件：

```text
harness/README.md
harness/rules/rule1_harness_read.md
harness/rules/output_contract.md
harness/skills/franka_arm_actions.yaml
harness/memory/project_memory.md
harness/plan_state.md
```

必须满足：

- 每次修改后按需要同步 `harness` 中的规则、skill、memory 或 plan state。
- 不自动提交。
- 每次对话后如有文件修改，必须主动询问用户是否提交。
- 每次提交只能提交到 `codex` 分支。

## 4. 动作合同

LLM planner 的最终输出必须是空格分隔的动作名称序列。

合法 token：

```text
left
right
reset
```

动作语义：

| Token | 二进制语义 | Franka 关节目标 |
| --- | --- | --- |
| `left` | `0` | `panda_joint1 = -1.57079632679 rad`，即 -90° |
| `right` | `1` | `panda_joint1 = 1.57079632679 rad`，即 +90° |
| `reset` | 复位 | `panda_joint1 = 0.0 rad` |

约束：

- `left` 或 `right` 后必须立即跟 `reset`。
- `reset` 不能作为第一个动作。
- `reset` 必须跟在 `left` 或 `right` 后面。
- 输出不能包含数字、JSON、标点、中文解释或任何额外文本。

合法示例：

```text
left reset right reset
```

非法示例：

```text
0 1
left right
left reset jump reset
["left", "reset"]
先 left 再 reset
```

## 5. 组件设计

### 5.1 动作校验层

文件：`llm_vla/actions.py`

职责：

- `parse_sequence(sequence)`：解析空格分隔 token。
- `validate_sequence(sequence)`：检查 token 白名单和复位规则。
- `sequence_to_text(tokens)`：输出规范化文本。

校验层是 LLM 与仿真执行层之间的安全门。任何非法输出都必须在本地被拒绝，不能进入 Isaac Sim 执行。

### 5.2 Harness 读取层

文件：`llm_vla/harness.py`

职责：

- 定义项目根目录与 `harness` 根目录。
- 按固定顺序读取核心 harness 文件。
- 为 planner prompt 提供完整规则上下文。

### 5.3 LLM Planner 层

文件：`llm_vla/planner.py`、`llm_vla/plan.py`

职责：

- 通过 `build_prompt_messages(user_request)` 构建 system/user messages。
- 使用 `OpenAICompatiblePlanner` 调用模型并校验输出。
- 使用 `OpenAIChatClient` 通过标准库 `urllib` 调用 OpenAI-compatible API。
- 支持 `MockClient` 进行无 API 测试。

API 环境变量：

```text
LLM_BASE_URL
LLM_API_KEY
LLM_MODEL
```

Mock 运行示例：

```powershell
python -m llm_vla.plan "输出 01 的动作" --mock-output "left reset right reset"
```

### 5.4 Franka 动作映射层

文件：`llm_vla/sim_actions.py`

职责：

- 定义受控关节：`panda_joint1`。
- 定义动作步数：`ACTION_STEPS = 30`。
- 将合法 token 序列转换成 `(token, target_rad, step_count)` 列表。

当前映射：

```python
ACTION_TARGETS = {
    "left": -1.57079632679,
    "right": 1.57079632679,
    "reset": 0.0,
}
```

### 5.5 Isaac Sim 执行层

文件：`sim/run_franka_sequence.py`

职责：

- 启动 Isaac Sim / IsaacLab。
- 创建 ground、light 和 Franka Panda。
- 解析 `--sequence`、`--max_steps`、`--action_steps`。
- 按序给 `panda_joint1` 写入关节位置目标。
- 打印每个执行 token 和目标弧度。

默认使用 `os._exit()` 退出，以避免部分 Windows + Isaac Sim 环境在 `SimulationApp.close()` 阶段卡住。需要正常关闭时可以显式传入：

```powershell
--graceful_close
```

## 6. 运行命令

从项目根目录运行：

```powershell
cd D:\il\IsaacLab\scripts\LLM_VLA
```

Harness 检查：

```powershell
python harness\scripts\check_harness.py
```

Mock planner：

```powershell
python -m llm_vla.plan "输出 01 的动作" --mock-output "left reset right reset"
```

Isaac Sim headless smoke test：

```powershell
D:\il\env\Scripts\python.exe -B sim\run_franka_sequence.py `
  --headless `
  --max_steps 120 `
  --sequence "left reset right reset"
```

可视化运行：

```powershell
D:\il\env\Scripts\python.exe -B sim\run_franka_sequence.py `
  --max_steps 120 `
  --sequence "left reset right reset"
```

## 7. 测试规格

测试目录：`tests/`

覆盖内容：

- `test_action_contract.py`：合法 token、非法 token、数字输出、缺少 reset。
- `test_harness_contracts.py`：harness 文件存在、Rule 1、P0 历史、harness 检查脚本。
- `test_planner.py`：mock planner、非法模型输出、prompt 读取 harness、环境变量缺失。
- `test_sim_actions.py`：动作 token 到 Franka 90° 关节目标的映射。
- `test_sim_runtime.py`：默认强制退出策略和 `--graceful_close` 策略。

完整测试命令：

```powershell
D:\il\env\Scripts\python.exe -m pytest tests -v
```

## 8. 当前验收标准

当前最小版本验收标准：

- `python harness\scripts\check_harness.py` 输出 `harness ok`。
- `D:\il\env\Scripts\python.exe -m pytest tests -v` 全部通过。
- Isaac Sim headless smoke test 输出：

```text
left -1.57079632679
reset 0.0
right 1.57079632679
reset 0.0
```

满足以上三项，即认为最小 LLM 动作规划 + Franka 90° 仿真闭环可用。
