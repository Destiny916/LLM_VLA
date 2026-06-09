# 两关节控制策略

当前仿真动作层只解锁两个 Franka 关节：

- `panda_joint1`：底部旋转关节，负责 `left_2rad`、`right_2rad`。
- `panda_joint2`：底部上方的上下运动关节，负责 `lift_up`、`put_down`、`reset`、`hold_reset`。

其它 Franka 关节必须保持 IsaacLab 默认关节目标，不允许 LLM 或动作 token 直接控制。

## 复位规则

`reset` 只复位两个解锁关节：

```text
panda_joint1 = 0.0
panda_joint2 = 0.0
```

`reset` 不能把其它 Franka 关节全部写成 0，否则 Franka 可能出现奇怪复位姿态。

## 上举和放下

`lift_up` 只控制 `panda_joint2` 到上举目标。

`put_down` 只控制 `panda_joint2` 回到放下目标。

`put_down` 不是 `reset`，它只处理上举状态；任务完成仍需要 `reset`。
