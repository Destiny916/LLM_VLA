# RAG 状态规则

用途：定义机械臂姿态状态和动作语义的关系。

## 状态字段

```text
arm_lift: down | up
base_target: neutral | left_2rad | right_2rad
task_status: idle | running | stopped
```

## 上举状态

- `lift_up` 后，`arm_lift = up`。
- 上举状态会影响后续旋转动作的语义。
- `lift_up left_2rad` 表示“泡咖啡”。
- `lift_up right_2rad` 表示“做冰淇淋”。
- `lift_up left_2rad right_2rad right_2rad` 表示“泡浓咖啡”。
- `lift_up left_2rad left_2rad left_2rad` 表示“泡淡咖啡”。
- `left_2rad lift_up` 表示“先打招呼，再上举”，不能理解为泡咖啡。

## 默认放下状态

- `arm_lift = down` 时，`left_2rad` 表示“打招呼”。
- `arm_lift = down` 时，`right_2rad` 表示“握手”。

## 放下状态

- `put_down` 后，`arm_lift = down`。
- `put_down` 只处理上举相关姿态，不等同于全局 `reset`。
- `lift_up left_2rad put_down right_2rad` 表示先泡咖啡，再放下后握手。

## 复位状态

- `reset` 后，`arm_lift = down`。
- `reset` 后，`base_target = neutral`。
- `reset` 是任务完成边界。
- 全部任务完成后，服务端进入 `hold_reset`。

## 空闲状态

- 没有指令时，`task_status = idle`。
- `idle` 状态下服务端保持复位姿态。
- `idle` 状态不能关闭 Isaac Sim，也不能让主循环卡死。
