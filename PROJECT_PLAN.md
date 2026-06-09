# LLM_VLA 中文实施计划

> 当前阶段：P11 已完成，任务 4 任务计划数据结构与本地校验已实现。
> 项目根目录：`D:/il/IsaacLab/scripts/LLM_VLA`
> Git 分支规则：只在 `codex` 分支提交。
> 提交规则：不自动提交；每次提交前必须询问用户。
> API key 规则：真实 API key 只能放在本地环境变量或被忽略的本地文件中，不能提交。

## 1. 当前状态

项目已经完成最小双窗口闭环：

- CLI 调用真实 OpenAI-compatible LLM API。
- CLI 展示 API 原始输出、可见决策摘要、API token 结果、本地校验结果和仿真响应。
- Isaac Sim 服务端常驻运行，接收 CLI 发来的动作序列。
- IPC 使用 UTF-8 JSON-line。
- `harness/rag` 已作为轻量知识库，当前可被本地 RAG 检索模块读取。

本次修正：

- 删除 `left_circle` 和 `right_circle` 作为可执行动作。
- 左右转动作改为 `left_2rad` / `right_2rad`。
- 当前简化仿真只控制 `panda_joint1` 和 `panda_joint2`。
- 其它 Franka 关节保持 IsaacLab 默认目标，避免 reset 姿态异常。

## 2. 当前合法动作

```text
left_2rad
right_2rad
lift_up
put_down
reset
hold_reset
stop
```

含义：

- `left_2rad`：底部旋转关节 `panda_joint1 = -2.0 rad`。
- `right_2rad`：底部旋转关节 `panda_joint1 = +2.0 rad`。
- `lift_up`：底部上方上下运动关节 `panda_joint2` 上举。
- `put_down`：`panda_joint2` 放下，不等同于 `reset`。
- `reset`：只复位 `panda_joint1` 和 `panda_joint2`。
- `hold_reset`：空闲或任务完成后保持复位，仿真继续运行。
- `stop`：停止当前任务队列，必须单独输出。

已删除动作：

```text
left_circle
right_circle
```

删除原因：在当前两关节演示里，整圈动作会表现为多次普通转动，和普通左右转没有清晰区别，容易误导任务语义。

## 3. 阶段进度

| 阶段 | 状态 | 目标 |
| --- | --- | --- |
| P8 | 已完成 | 扩展版 spec 与中文 plan |
| P9-task1 | 已完成 | 创建 harness/RAG 文档知识源 |
| P9 | 已完成 | 实现轻量 RAG 检索模块 |
| P10 | 已完成 | 动作合同 v2 与 Franka 动作映射 |
| P10-correction | 已完成 | 锁定 Franka 其它关节，只控制两个简化关节 |
| P11 | 已完成 | 任务计划数据结构与本地校验 |
| P12 | 待执行 | 机械臂状态语义模型 |
| P13 | 待执行 | LLM prompt 接入 RAG 与任务计划 JSON |
| P14 | 待执行 | 仿真 idle hold 与任务队列执行 |
| P15 | 待执行 | CLI 对话记忆与任务队列编辑 |
| P16 | 待执行 | 双窗口集成测试与回归验证 |

## 4. 已完成任务

### 任务 1：更新 harness 与 RAG 知识目录

已创建：

- `harness/rag/action_catalog.md`
- `harness/rag/action_examples.md`
- `harness/rag/task_rules.md`
- `harness/rag/state_rules.md`
- `harness/rag/safety_rules.md`
- `harness/rag/conversation_memory.md`
- `harness/rag/two_joint_policy.md`

### 任务 2：实现轻量 RAG 检索模块

已创建：

- `llm_vla/rag.py`
- `tests/test_rag.py`

能力：

- 标准库读取 Markdown。
- 按标题切分 chunk。
- 支持中英文关键词和 token 匹配。
- 返回命中文档路径、标题、摘要和片段。

### 任务 3：设计并实现动作合同 v2

已修改：

- `llm_vla/actions.py`
- `llm_vla/sim_actions.py`
- `llm_vla/prompting.py`
- `sim/run_franka_sequence.py`
- `sim/run_franka_server.py`
- `harness/rules/output_contract.md`
- `harness/rules/llm_prompt_contract.md`
- `harness/skills/franka_arm_actions.yaml`
- `harness/scripts/check_harness.py`
- 相关测试文件

当前规则：

- 动作之间不强制复位。
- 每个任务结束必须复位。
- 上举后必须先放下才能 reset。
- `stop` 必须单独输出。
- 整圈动作已删除。

### 任务 4：实现任务计划数据结构

已创建：

- `llm_vla/task_plan.py`
- `llm_vla/task_validation.py`
- `tests/test_task_plan.py`
- `tests/test_task_validation.py`

核心结构：

```text
TaskPlan
TaskOperation
Subtask
```

支持操作：

```text
add
stop
remove
modify
continue
```

本地校验规则：

- 每个操作必须有 `task_id`。
- `add`、`modify`、`continue` 必须包含子任务。
- 子任务动作中不能直接写任务边界 token：`reset`、`hold_reset`、`stop`。
- `add`、`modify`、`continue` 必须 `reset_after_task=true`。
- `remove`、`modify`、`stop` 必须引用已存在任务或当前任务。
- 展开动作时每个任务自动追加 `reset`。
- 全部任务完成后自动追加 `hold_reset`。

## 5. 下一步任务

### 任务 5：实现机械臂状态模型

目标：让系统显式记录机械臂状态，区分上举状态下左转和未上举状态下左转的语义。

建议创建：

- `llm_vla/state.py`
- `tests/test_state.py`

状态字段：

```text
arm_lift: down | up
base_target: neutral | left_2rad | right_2rad
task_status: idle | running | paused | stopped
```

### 任务 6：升级 LLM prompt 与输出解析

目标：让 LLM 结合 RAG 命中内容输出任务计划 JSON，而不是只输出旧 `action_tokens` 字符串。

需要修改：

- `llm_vla/prompting.py`
- `llm_vla/planner.py`
- `tests/test_prompting.py`
- `tests/test_planner.py`

### 任务 7：升级仿真服务端 idle hold

目标：无指令或任务完成后，机械臂保持复位且仿真继续运行。

需要修改：

- `sim/run_franka_server.py`
- `llm_vla/server.py`
- `tests/test_server.py`

### 任务 8：升级 CLI 对话记忆与任务队列编辑

目标：让 CLI 支持中途停止、增加、减少、改变任务，并展示当前任务队列和机械臂状态。

建议创建或修改：

- `llm_vla/conversation.py`
- `llm_vla/cli_control.py`
- `tests/test_conversation.py`
- `tests/test_cli_control.py`

### 任务 9：双窗口集成验证

窗口 1：

```powershell
cd D:\il\IsaacLab\scripts\LLM_VLA

D:\il\env\Scripts\python.exe -B sim\run_franka_server.py `
  --host 127.0.0.1 `
  --port 8765
```

窗口 2：

```powershell
cd D:\il\IsaacLab\scripts\LLM_VLA

$env:LLM_BASE_URL="https://api.deepseek.com"
$env:LLM_API_KEY="<只在本地环境变量中设置，不能写入提交文件>"
$env:LLM_MODEL="deepseek-v4-pro"

D:\il\env\Scripts\python.exe -m llm_vla.cli_control `
  --host 127.0.0.1 `
  --port 8765
```

测试输入：

```text
机械臂上举后左转，然后放下
把刚才的任务改成上举后右转，然后放下
停止当前任务
```

## 6. 验证计划

阶段完成后运行：

```powershell
cd D:\il\IsaacLab\scripts\LLM_VLA

python harness\scripts\check_harness.py
D:\il\env\Scripts\python.exe -m pytest tests -v
D:\il\env\Scripts\python.exe -B sim\run_franka_sequence.py `
  --headless `
  --max_steps 240 `
  --sequence "lift_up left_2rad put_down right_2rad reset"
```

提交前 secret 检查：

```powershell
rg -n "sk-|LLM_API_KEY=.*sk-" .
```

## 7. Git 规则

- 所有提交都在 `codex` 分支。
- 不提交真实 API key。
- `.env`、本地启动脚本、临时日志继续保持忽略。
- 每个阶段完成后先询问用户是否提交。
- 只有用户明确要求时才 push。
