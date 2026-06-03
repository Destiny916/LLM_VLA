# LLM_VLA 项目计划

> 最后更新：2026-06-03  
> 当前重点：CLI 接入真实大语言模型 API，并让 LLM 通过动作 token 直接控制 Isaac Sim 仿真  
> 分支规则：只在 `codex` 分支提交  
> 提交规则：不自动提交；每次提交前必须先询问用户

## 目标

当前机器人动作层已经完成：Franka Panda 机械臂能够执行 `left`、`right`、`reset`，其中：

- `left`：`panda_joint1 = -1.57079632679 rad`，左转 90°
- `right`：`panda_joint1 = 1.57079632679 rad`，右转 90°
- `reset`：`panda_joint1 = 0.0 rad`，复位

新的目标是构建一个 CLI 控制窗口：用户在 CLI 中输入复杂自然语言，CLI 调用真实大语言模型 API，让 LLM 理解用户意图并直接输出动作 token 序列。CLI 将该动作序列发送给正在运行的 Isaac Sim 仿真服务端，Franka 立即执行。

目标闭环：

```text
用户自然语言输入
  -> CLI 控制窗口
  -> 真实大语言模型 API
  -> LLM 输出动作 token 序列
  -> 本地 rule 校验
  -> 发送给 Isaac Sim 仿真服务端
  -> Franka 执行 left/right/reset
```

关键要求：

- CLI 窗口和 Isaac Sim 仿真窗口必须同时打开。
- 仿真服务端常驻运行，不因每次输入而重启。
- LLM 负责复杂自然语言理解。
- LLM 直接决定要执行的动作 token 序列。
- 最终进入仿真的内容必须是动作 token，不是解释文本。
- 本地仍保留最后一道 `validate_sequence()` 校验，防止非法 token 进入仿真。

## 当前事实

已经完成：

- `left`、`right`、`reset` 动作 token 校验。
- `left reset right reset` 这类序列的本地规则检查。
- Franka Panda 仿真场景创建。
- `panda_joint1` 关节目标控制。
- 90° 左右转映射。

需要重做或新增：

- CLI 控制窗口。
- CLI 中真实大语言模型 API 调用。
- 面向 LLM 的系统 prompt 和 rule。
- LLM 输出到动作 token 的强约束。
- CLI 与仿真服务端通信。
- 仿真服务端常驻等待命令。
- 多次自然语言输入、多次执行、不重启仿真的闭环。

## 修正后的架构

采用两个同时运行的进程。

### 进程 1：Isaac Sim 仿真服务端

仿真服务端负责运行 Isaac Sim 和 Franka Panda，并等待 CLI 发来的动作序列。

职责：

- 启动 Isaac Sim。
- 创建 Franka 场景。
- 监听本地通信端口。
- 接收 CLI 发来的动作 token 序列。
- 再次调用 `validate_sequence()` 校验。
- 执行动作。
- 返回执行结果。
- 继续等待下一条命令。

建议命令：

```powershell
cd D:\il\IsaacLab\scripts\LLM_VLA

D:\il\env\Scripts\python.exe -B sim\run_franka_server.py `
  --host 127.0.0.1 `
  --port 8765
```

### 进程 2：LLM CLI 控制端

CLI 控制端负责接收用户自然语言、调用真实大模型、解析模型输出并发送给仿真。

职责：

- 显示提示符 `LLM_VLA>`。
- 接收复杂自然语言输入。
- 读取 harness rule、skill 和 prompt。
- 调用真实 OpenAI-compatible 大语言模型 API。
- 要求 LLM 只输出动作 token 序列。
- 对 LLM 输出调用 `validate_sequence()`。
- 通过本地 socket 把动作序列发送给仿真服务端。
- 打印服务端返回结果。

建议命令：

```powershell
cd D:\il\IsaacLab\scripts\LLM_VLA

python -m llm_vla.cli_control `
  --host 127.0.0.1 `
  --port 8765
```

真实 API 环境变量：

```powershell
$env:LLM_BASE_URL="https://api.openai.com/v1"
$env:LLM_API_KEY="your_api_key_here"
$env:LLM_MODEL="your_model_name_here"
```

交互示例：

```text
LLM_VLA> 让机械臂表示二进制 01
LLM 输出: left reset right reset
仿真: ok

LLM_VLA> 先左转再右转
LLM 输出: left reset right reset
仿真: ok

LLM_VLA> 右转一次
LLM 输出: right reset
仿真: ok

LLM_VLA> quit
退出 CLI
```

## 通信方案

使用本地 TCP socket。

原因：

- CLI 和 Isaac Sim 是两个独立窗口、两个独立进程。
- 仿真需要常驻，不能每次输入后重启。
- TCP socket 可以支持多次请求、多次执行。
- Python 标准库即可实现。
- 后续可替换为 WebSocket、GUI 或真实机器人控制端。

通信约定：

```text
host: 127.0.0.1
port: 8765
encoding: utf-8
message: 一行 JSON，以换行结束
```

CLI 发送：

```json
{"sequence": "left reset right reset"}
```

仿真返回成功：

```json
{"status": "ok", "executed": "left reset right reset"}
```

仿真返回失败：

```json
{"status": "error", "message": "left must be followed by reset"}
```

## LLM Prompt 与 Rule

LLM 的任务不是聊天，而是把自然语言转换为机器人可执行动作 token。

### 系统 Prompt

建议系统 prompt：

```text
你是 LLM_VLA 机器人动作控制器。

你必须把用户自然语言转换为机器人动作 token 序列。

机器人只有三个合法动作 token：
- left：机械臂 left turn，表示 panda_joint1 左转 90 度，同时语义上代表二进制 0。
- right：机械臂 right turn，表示 panda_joint1 右转 90 度，同时语义上代表二进制 1。
- reset：机械臂回到中立位置。

硬性规则：
1. 你只能输出由 left、right、reset 组成的空格分隔序列。
2. 每个 left 后必须立刻输出 reset。
3. 每个 right 后必须立刻输出 reset。
4. reset 不能作为第一个动作。
5. 不要输出解释、标点、JSON、Markdown、中文、数字或任何额外文本。
6. 如果用户说 0，把它映射为 left reset。
7. 如果用户说 1，把它映射为 right reset。
8. 如果用户说 01，把它映射为 left reset right reset。
9. 如果用户要求左转，输出 left reset。
10. 如果用户要求右转，输出 right reset。

最终回答必须只是一行动作 token。
```

### 用户输入示例与期望输出

```text
用户：表示 0
输出：left reset

用户：表示 1
输出：right reset

用户：表示 01
输出：left reset right reset

用户：先左转再右转
输出：left reset right reset

用户：右转两次
输出：right reset right reset
```

### LLM 输出后本地 Rule

LLM 输出后必须经过本地校验：

```text
validate_sequence(llm_output)
```

如果校验失败：

- CLI 不发送给仿真。
- CLI 打印错误。
- 可选择重新请求 LLM 一次，并把错误作为修正提示传回模型。

修正提示示例：

```text
你的上一次输出不符合规则：{error}
请重新输出，只能使用 left right reset，并确保每个 left/right 后紧跟 reset。
不要输出解释。
```

## 固定项目规则

- 工作目录固定为 `D:\il\IsaacLab\scripts\LLM_VLA`。
- 每次分析、编辑、运行或 Git 操作前，必须先读取核心 `harness` 文件。
- IsaacLab 和 Isaac Sim 命令使用 `D:\il\env\Scripts\python.exe`。
- CLI 接入真实大语言模型 API。
- LLM 负责复杂自然语言理解。
- LLM 可以直接决定仿真动作 token 序列。
- 最终进入仿真的必须是本地校验后的 token 序列。
- 合法最终 token 只有 `left`、`right`、`reset`。
- 每个 `left` 或 `right` 后必须立即跟 `reset`。
- Git 提交分支固定为 `codex`。
- 不自动提交或推送；必须等用户明确确认。

## 阶段计划

| 阶段 | 状态 | 目的 |
| --- | --- | --- |
| P0 | 已完成 | harness 与动作合同设计 |
| P1 | 已完成 | Franka 左转、右转、复位动作实现 |
| P2 | 当前修正 | LLM CLI 控制窗口设计 |
| P3 | 待实现 | 真实大语言模型 API 接入 |
| P4 | 待实现 | 仿真常驻服务端 |
| P5 | 待实现 | LLM CLI 与仿真服务端通信 |
| P6 | 待实现 | 复杂自然语言输入集成验证 |

## 实施计划

### 任务 1：更新 Harness 表达 LLM 直接控制架构

**目标：** 让 harness 明确当前重点是 LLM CLI 直接控制仿真。

**涉及文件：**

- `harness/memory/project_memory.md`
- `harness/plan_state.md`
- `harness/rules/output_contract.md`

**要求：**

- 记录“动作层已完成”。
- 记录“当前阶段要实现 CLI 接真实大语言模型 API”。
- 记录“LLM 输出动作 token 后直接发送给仿真服务端”。
- 保持动作 token 合同不变。

**验证：**

```powershell
python harness\scripts\check_harness.py
```

### 任务 2：新增 LLM Prompt 规则模块

**目标：** 把系统 prompt、few-shot 示例和修正 prompt 固化为代码或 harness 文本。

**建议新增文件：**

- `harness/rules/llm_prompt_contract.md`
- `llm_vla/prompting.py`
- `tests/test_prompting.py`

**核心接口：**

```python
def build_system_prompt(harness_context: str) -> str:
    ...

def build_repair_prompt(previous_output: str, error: str) -> str:
    ...
```

**验收要求：**

- system prompt 必须包含 `left`、`right`、`reset`。
- system prompt 必须包含“只能输出动作 token”。
- system prompt 必须说明 `0 -> left reset`、`1 -> right reset`。
- repair prompt 必须包含上一次错误和重新输出要求。

### 任务 3：接入真实大语言模型 API

**目标：** CLI 使用真实 OpenAI-compatible API，而不是 mock。

**涉及文件：**

- `llm_vla/planner.py`
- `llm_vla/cli_control.py`
- `tests/test_planner.py`

**环境变量：**

```text
LLM_BASE_URL
LLM_API_KEY
LLM_MODEL
```

**行为：**

- CLI 启动时检查环境变量。
- 调用 chat completions API。
- temperature 固定为 `0`。
- 获取 `choices[0].message.content`。
- strip 后交给 `validate_sequence()`。
- 校验失败时最多 repair 一次。

**不做：**

- 不把 API key 写入代码。
- 不把真实 API 调用放进默认 pytest。

### 任务 4：新增 IPC 协议模块

**目标：** 定义 CLI 与仿真服务端之间的 JSON 行协议。

**建议新增文件：**

- `llm_vla/ipc.py`
- `tests/test_ipc.py`

**核心接口：**

```python
def encode_request(sequence: str) -> bytes:
    ...

def decode_request(data: bytes) -> str:
    ...

def encode_response(status: str, **fields) -> bytes:
    ...

def decode_response(data: bytes) -> dict:
    ...
```

**要求：**

- 使用 UTF-8。
- 每条消息以换行结束。
- 请求只包含经过校验的 `sequence`。

### 任务 5：新增仿真服务端

**目标：** 让 Isaac Sim 常驻运行并接收 LLM CLI 命令。

**建议新增文件：**

- `sim/run_franka_server.py`

**行为：**

- 启动 Franka 仿真场景。
- 监听 `127.0.0.1:8765`。
- 收到动作序列后调用 `validate_sequence()`。
- 调用现有动作执行逻辑。
- 执行结束后返回 JSON response。
- 不退出仿真，继续等待下一条命令。

### 任务 6：新增 LLM CLI 控制端

**目标：** 提供独立 CLI 窗口，接收自然语言并调用 LLM 控制仿真。

**建议新增文件：**

- `llm_vla/cli_control.py`

**行为：**

- 启动后显示提示符 `LLM_VLA>`。
- 接收自然语言。
- 调用真实 LLM API。
- 打印 LLM 输出。
- 校验 LLM 输出。
- 发送给仿真服务端。
- 打印执行结果。
- 输入 `quit` 或 `exit` 时退出 CLI。

**运行命令：**

```powershell
python -m llm_vla.cli_control `
  --host 127.0.0.1 `
  --port 8765
```

### 任务 7：双窗口集成验证

**窗口 1：启动仿真服务端**

```powershell
cd D:\il\IsaacLab\scripts\LLM_VLA

D:\il\env\Scripts\python.exe -B sim\run_franka_server.py `
  --host 127.0.0.1 `
  --port 8765
```

**窗口 2：启动 LLM CLI 控制端**

```powershell
cd D:\il\IsaacLab\scripts\LLM_VLA

$env:LLM_BASE_URL="https://api.openai.com/v1"
$env:LLM_API_KEY="your_api_key_here"
$env:LLM_MODEL="your_model_name_here"

python -m llm_vla.cli_control `
  --host 127.0.0.1 `
  --port 8765
```

**输入序列：**

```text
表示 0
表示 1
表示 01
先左转再右转
右转两次
quit
```

**期望结果：**

- 仿真窗口保持打开。
- CLI 每次输入都会调用真实 LLM。
- LLM 输出合法 token。
- CLI 将 token 发送给仿真。
- Franka 按输出动作执行。
- 输入 `quit` 只退出 CLI，不关闭仿真服务端。

## 暂不做

- 暂不做视觉输入。
- 暂不训练 VLA 模型。
- 暂不实现真实机器人控制。
- 暂不把仿真服务端暴露到公网。
- 暂不允许 LLM 输出任意 Python、JSON、坐标或关节数组。

## Git 交接规则

提交前运行：

```powershell
git status --short --branch
python harness\scripts\check_harness.py
D:\il\env\Scripts\python.exe -m pytest tests -v
```

提交前必须询问用户。用户确认后再提交。

只有用户明确要求时才 push。
