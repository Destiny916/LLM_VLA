# RAG 状态规则

用途：定义机械臂姿态状态和动作语义的关系。

## 状态字段

```text
arm_lift: down | up
base_orientation: neutral | left_2rad | right_2rad
task_status: idle | running | paused | stopped
```

## 上举状态

- `lift_up` 后，`arm_lift = up`。
- 上举状态会影响后续旋转动作的语义。
- `lift_up left_2rad` 表示“上举状态下左转 2rad”。
- `left_2rad lift_up` 表示“先默认姿态左转 2rad，再上举”，两者不能混淆。

## 放下状态

- `put_down` 后，`arm_lift = down`。
- `put_down` 只处理上举相关姿态，不等同于全局 `reset`。
- `lift_up left_2rad put_down right_2rad` 表示先上举左转，再放下后右转。

## 复位状态

- `reset` 后，`arm_lift = down`。
- `reset` 后，`base_orientation = neutral`。
- `reset` 是任务完成边界。
- 全部任务完成后，服务端进入 `hold_reset`。

## 空闲状态

- 没有指令时，`task_status = idle`。
- `idle` 状态下服务端保持复位姿态。
- `idle` 状态不能关闭 Isaac Sim，也不能让主循环卡死。
