# LLM_VLA 扩展版 Spec

> 当前状态：P11 已完成任务计划数据结构与本地校验。
> 项目根目录：`D:/il/IsaacLab/scripts/LLM_VLA`
> 目标仓库：`https://github.com/Destiny916/LLM_VLA.git`
> Git 分支：`codex`

## 1. 背景

`LLM_VLA` 当前已经具备双窗口最小闭环：

- CLI 窗口调用 OpenAI-compatible LLM API，接收自然语言输入。
- CLI 展示 API 原始输出、可见决策摘要、API token 结果、本地校验结果和仿真响应。
- Isaac Sim 服务窗口常驻运行 Franka Panda 仿真。
- CLI 通过 UTF-8 JSON-line IPC 把本地校验通过的动作序列传给 Isaac Sim 服务端。

本阶段修正动作设计：删除“左转一整圈”和“右转一整圈”动作，因为它们在当前简化两关节演示中会退化成多次普通左转/右转，不具备独立展示意义。左右转动作改为 2rad 目标。

## 2. 当前合法动作合同

合法动作 token：

```text
left_2rad
right_2rad
lift_up
put_down
reset
hold_reset
stop
```

已删除且不允许 LLM 输出的动作：

```text
left_circle
right_circle
```

动作语义：

- `left_2rad`：`panda_joint1 = -2.0 rad`。
- `right_2rad`：`panda_joint1 = +2.0 rad`。
- `lift_up`：只控制 `panda_joint2`，进入上举状态。
- `put_down`：只控制 `panda_joint2`，从上举状态放下；它不是 `reset`。
- `reset`：只把 `panda_joint1` 和 `panda_joint2` 回到 `0.0`，其它 Franka 关节保持 IsaacLab 默认关节目标。
- `hold_reset`：无任务或全部任务完成后持续保持复位目标，仿真不退出、不卡死。
- `stop`：停止当前任务队列，必须单独输出。

## 3. 本地校验规则

- 可执行动作序列只能由合法 token 组成，空格分隔。
- 不允许输出数字、JSON、标点、中文解释或额外文本作为可执行序列。
- 动作之间不再强制复位。
- 每个任务完成后必须追加一次 `reset`。
- 全部任务完成后进入 `hold_reset`，或由服务端 idle hold 维持复位。
- `lift_up` 后必须在任务 `reset` 前出现 `put_down`。
- `put_down` 只能在同一任务上下文中已有 `lift_up` 后出现。
- `stop` 必须单独作为控制 token。

## 4. Franka 控制范围

当前简化机械臂只解锁两个关节：

- `panda_joint1`：底部旋转关节，用于 `left_2rad` 和 `right_2rad`。
- `panda_joint2`：底部上方的上下运动关节，用于 `lift_up` 和 `put_down`。

其它 Franka 关节不由动作 token 直接控制，仿真执行层每步使用 IsaacLab 默认关节目标锁定它们，避免 reset 时出现奇怪姿态。

默认执行步数：

- 普通动作：30 simulation steps。
- `reset` / `hold_reset`：60 simulation steps。

## 5. LLM 输出路径

当前 CLI 仍支持旧的两字段 JSON：

```json
{
  "visible_reasoning": "一句简短中文可见决策摘要，不是隐藏链式思考。",
  "action_tokens": "left_2rad right_2rad reset"
}
```

规则：

- `visible_reasoning` 只用于 CLI 展示。
- `action_tokens` 是唯一可执行字段。
- 只有通过本地校验的 `action_tokens` 会发送给 Isaac Sim。
- 用户显式覆盖映射时，用户映射优先；但最终仍必须输出合法动作 token。

默认二进制语义：

- `0 -> left_2rad reset`
- `1 -> right_2rad reset`
- `01 -> left_2rad right_2rad reset`

## 6. 任务计划 JSON

任务 4 引入结构化任务计划，用于后续支持类似 Codex 的持续对话、停止、增加、减少、改变任务和记忆能力。

建议 LLM 后续输出：

```json
{
  "visible_reasoning": "一句简短中文可见决策摘要。",
  "intent": "用户意图摘要",
  "task_operations": [
    {
      "operation": "add",
      "task_id": "task_1",
      "description": "任务描述",
      "subtasks": [
        {
          "description": "子任务描述",
          "action_tokens": "lift_up left_2rad put_down"
        }
      ],
      "reset_after_task": true
    }
  ]
}
```

支持的 `operation`：

```text
add
stop
remove
modify
continue
```

任务计划校验：

- 每个任务操作必须有 `task_id`。
- `add`、`modify`、`continue` 必须有至少一个子任务。
- 子任务动作中不允许直接写 `reset`、`hold_reset` 或 `stop`，任务边界由任务计划层统一追加。
- `add`、`modify`、`continue` 必须 `reset_after_task=true`。
- `remove`、`modify`、`stop` 必须引用已存在任务或当前任务。
- 任务展开后每个任务自动追加 `reset`。
- 全部任务展开后自动追加 `hold_reset`。

## 7. 后续扩展

- P12：实现机械臂状态模型，显式记录上举/放下和底座转向状态。
- P13：让 LLM prompt 接入 RAG 检索内容，并从旧 `action_tokens` 输出升级到任务计划 JSON。
- P14：升级 Isaac Sim 服务端 idle hold，让没有指令和全部任务完成后仍持续复位运行。
- P15：实现 CLI 会话记忆和任务队列编辑。
