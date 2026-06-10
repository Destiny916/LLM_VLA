# RAG 动作知识库

用途：供后续 RAG 模块检索并注入 LLM prompt。

## 合法动作 token

```text
left_2rad
right_2rad
lift_up
put_down
reset
hold_reset
stop
```

## 已删除动作

```text
left_circle
right_circle
```

删除原因：在当前简化两关节演示臂中，整圈动作无法形成独立、稳定、清晰的可视化效果，容易退化为重复的左右转动作，因此不再作为合法动作 token。

## 当前两关节控制策略

当前仿真动作层只解锁两个 Franka 关节：

- `panda_joint1`：底部旋转关节，负责 `left_2rad`、`right_2rad`。
- `panda_joint2`：底部上方的上下运动关节，负责 `lift_up`、`put_down`、`reset`、`hold_reset`。

其它 Franka 关节必须保持 IsaacLab 默认关节目标，不允许 LLM 或动作 token 直接控制。

## 动作定义

### left_2rad

- 中文含义：左转。
- 目标关节：`panda_joint1`。
- 目标：`-2.0 rad`。
- 状态含义：如果 `arm_lift = down`，表示“打招呼”；如果 `arm_lift = up`，表示“泡咖啡”。

### right_2rad

- 中文含义：右转。
- 目标关节：`panda_joint1`。
- 目标：`+2.0 rad`。
- 状态含义：如果 `arm_lift = down`，表示“握手”；如果 `arm_lift = up`，表示“做冰淇淋”。

## 复合语义

### 泡浓咖啡

- 前置状态：`arm_lift = up`。
- 动作片段：`left_2rad right_2rad right_2rad`。
- 完整任务建议：`lift_up left_2rad right_2rad right_2rad put_down reset`。

### 泡淡咖啡

- 前置状态：`arm_lift = up`。
- 动作片段：`left_2rad left_2rad left_2rad`。
- 完整任务建议：`lift_up left_2rad left_2rad left_2rad put_down reset`。

### lift_up

- 中文含义：机械臂上举。
- 目标关节：`panda_joint2`。
- 目标：`-0.8 rad`。
- 状态变化：`arm_lift` 从 `down` 变为 `up`。
- 语义影响：后续旋转动作应理解为“上举状态下旋转”。

### put_down

- 中文含义：机械臂放下。
- 目标关节：`panda_joint2`。
- 目标：`0.0 rad`。
- 状态变化：`arm_lift` 从 `up` 变为 `down`。
- 语义区别：`put_down` 不是 `reset`，它只处理上举姿态。

### reset

- 中文含义：任务级复位。
- 目标关节：`panda_joint1 = 0.0`，`panda_joint2 = 0.0`。
- 锁定关节：其它 Franka 关节保持 IsaacLab 默认目标。
- 状态变化：`arm_lift = down`，`base_target = neutral`。
- 使用位置：每个任务完成后必须执行一次。

### hold_reset

- 中文含义：空闲保持复位。
- 目标关节：`panda_joint1 = 0.0`，`panda_joint2 = 0.0`。
- 锁定关节：其它 Franka 关节保持 IsaacLab 默认目标。
- 使用位置：没有任务或全部任务完成后进入。

### stop

- 中文含义：停止当前任务队列。
- 状态变化：`task_status = stopped`，随后进入 `hold_reset`。
- 限制：不关闭 Isaac Sim 服务端。
