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
- 只有 `panda_joint1` 和 `panda_joint2` 可控。
- 其它 Franka 关节保持 IsaacLab 默认关节目标。
- 动作之间不强制复位。
- 每个任务完成后必须复位。
- 上举动作必须有对应的放下动作。
- `put_down` 不是 `reset`。
- 无任务时保持 `hold_reset`。
- 不提交真实 API key。
