# LLM_VLA 扩展版 Spec

> 当前状态：P15 已完成 CLI 会话记忆与任务队列编辑。
> 项目根目录：`D:/il/IsaacLab/scripts/LLM_VLA`
> 目标仓库：`https://github.com/Destiny916/LLM_VLA.git`
> Git 分支：`codex`

## 1. 背景

`LLM_VLA` 当前已经具备双窗口最小闭环：

- CLI 窗口调用 OpenAI-compatible LLM API，接收自然语言输入。
- CLI 展示 API 原始输出、可见决策摘要、API token 结果、本地校验结果和仿真响应。
- CLI 维护当前会话的任务队列、当前任务 ID 和机械臂语义状态。
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

状态语义：

- 未上举状态下 `left_2rad` 表示“打招呼”。
- 未上举状态下 `right_2rad` 表示“握手”。
- 上举状态下 `left_2rad` 表示“泡咖啡”。
- 上举状态下 `right_2rad` 表示“做冰淇淋”。
- 上举状态下 `left_2rad right_2rad right_2rad` 表示“泡浓咖啡”。
- 上举状态下 `left_2rad left_2rad left_2rad` 表示“泡淡咖啡”。

## 3. 本地校验规则

- 可执行动作序列只能由合法 token 组成，空格分隔。
- 不允许输出数字、JSON、标点、中文解释或额外文本作为可执行序列。
- 动作之间不再强制复位。
- 每个任务完成后必须追加一次 `reset`。
- 多个任务连续执行时，必须是“任务动作 -> `reset` -> 下一个任务动作 -> `reset`”。
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
- 从 P13 开始，任务计划 JSON 是 LLM prompt 的优先输出路径。
- CLI 旧路径仍兼容 `visible_reasoning` + `action_tokens` JSON。
- planner 会把 `harness/rag` 检索结果注入 prompt，再把任务计划展开为仿真可执行 token。

## 7. 机械臂状态模型

任务 5 引入 `RobotState`，用于记录机械臂高层状态和动作语义，不直接改变 Isaac Sim 关节执行层。

状态字段：

```text
arm_lift: down | up
base_target: neutral | left_2rad | right_2rad
task_status: idle | running | stopped
last_semantic: 最近一次语义
semantic_history: 当前序列语义历史
```

状态转换：

- `lift_up`：`arm_lift = up`，语义“上举”。
- `put_down`：`arm_lift = down`，语义“放下”。
- `reset`：`arm_lift = down`，`base_target = neutral`，`task_status = idle`，语义“任务复位”。
- `hold_reset`：保持复位和 idle，语义“保持复位”。
- `stop`：停止任务并回到复位姿态，语义“停止任务”。

## 8. RAG 与任务计划输出

任务 6 将 LLM 输出从单纯动作字符串推进为结构化任务计划：

- `build_prompt_messages()` 会按用户输入从 `harness/rag` 检索相关动作、状态、示例和规则。
- `parse_planning_result()` 同时支持任务计划 JSON 和旧 `action_tokens` JSON。
- 任务计划 JSON 会通过 `TaskPlan` 校验并展开为 `action_tokens`，再进入 Isaac Sim。
- `visible_reasoning` 仍只作为 CLI 可见摘要，不作为执行依据。

## 9. 仿真服务端 idle hold

任务 7 已升级 Isaac Sim 服务端运行方式：

- `llm_vla.server.serve_forever()` 支持轮询式服务循环。
- 服务循环在没有 TCP 请求时调用 idle 回调。
- `sim/run_franka_server.py` 的 idle 回调会推进一帧仿真，并持续把 `panda_joint1` 和 `panda_joint2` 保持在 `reset` 目标。
- 其它 Franka 关节不由动作 token 控制，继续保持 IsaacLab 默认关节目标。
- CLI 无输入、LLM 没有新指令、或全部任务完成后，仿真服务端都不会退出，也不会停在阻塞状态。
- idle hold 不改变任务边界规则；多个任务之间仍必须先执行 `reset` 再执行下一个任务。

## 10. CLI 会话记忆与任务队列编辑

任务 8 已引入 `ConversationMemory`：

- 记录当前任务队列，任务项包含 `task_id`、任务描述和展开后的动作序列。
- 记录当前任务 ID，供下一轮 LLM 对“刚才的任务”“当前任务”做 `modify`、`remove`、`stop`。
- 记录 `RobotState`，包括 `arm_lift`、`base_target`、`task_status` 和最近语义。
- CLI 每轮请求会向 planner 传入 `existing_task_ids`、`current_task_id` 和 `conversation_context`。
- `conversation_context` 包含当前任务队列、当前任务和机械臂状态。
- planner 在解析任务计划 JSON 时会使用这些上下文校验引用型操作。
- CLI 执行后展示任务操作摘要、当前任务队列和机械臂状态。
- 旧版 `visible_reasoning` + `action_tokens` JSON 仍兼容，并会作为 legacy 任务记录到会话记忆中。

任务编辑规则：

- `add`：新增任务并立即执行该任务序列。
- `modify`：替换已有任务记录，并执行修改后的任务序列。
- `remove`：删除已有任务；没有动作要执行时进入 `hold_reset`。
- `continue`：按任务计划层规则继续已有任务或当前任务。
- `stop`：停止当前任务，发送独立 `stop` token，不关闭 Isaac Sim 服务端。
- 所有动作型任务仍必须在任务结束时 `reset`，全部动作型任务完成后进入 `hold_reset`。

## 11. 后续扩展

- P16：执行双窗口集成验证，确认真实 LLM CLI 与 Isaac Sim 服务端联动。
