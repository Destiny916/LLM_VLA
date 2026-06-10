# RAG 会话记忆

用途：记录当前项目长期规则，供后续 RAG 注入。

## 当前动作方向

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

已删除动作：

```text
left_circle
right_circle
```

删除原因：当前两关节演示中，整圈动作展示不稳定，也不再具备独立动作意义。

## 当前规则记忆

- 左转和右转使用 2rad，不再使用 90 度目标。
- 未上举状态下左转表示“打招呼”。
- 未上举状态下右转表示“握手”。
- 上举状态下左转表示“泡咖啡”。
- 上举状态下右转表示“做冰淇淋”。
- 上举状态下左转后右转两次表示“泡浓咖啡”。
- 上举状态下左转后左转两次表示“泡淡咖啡”。
- 只有 `panda_joint1` 和 `panda_joint2` 可控。
- 其它 Franka 关节保持 IsaacLab 默认关节目标。
- 动作之间不强制复位。
- 每个任务完成后必须复位。
- 上举动作必须有对应的放下动作。
- `put_down` 不是 `reset`。
- 无任务时保持 `hold_reset`。
- 不提交真实 API key。

## CLI 会话记忆规则

- CLI 使用 `ConversationMemory` 保存当前任务队列。
- 每个任务记录包含 `task_id`、任务描述和展开后的动作序列。
- CLI 记录 `current_task_id`，用于解析“刚才的任务”“当前任务”。
- CLI 记录 `RobotState`，用于展示 `arm_lift`、`base_target`、`task_status` 和最近语义。
- 每轮 LLM 请求都会收到 `existing_task_ids`、`current_task_id` 和 `conversation_context`。
- `modify`、`remove`、`stop` 必须引用已有任务或当前任务。
- `add`、`modify`、`continue` 仍然必须由任务计划层追加任务级 `reset`。
- `remove` 没有动作要执行时进入 `hold_reset`。
- `stop` 只发送独立 `stop` token，不关闭 Isaac Sim 服务端。
- CLI 每轮执行后必须显示任务操作摘要、当前任务队列和机械臂状态。
