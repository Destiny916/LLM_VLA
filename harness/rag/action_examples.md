# RAG 动作与任务示例

用途：为 LLM 提供自然语言到任务计划的 few-shot 知识。

## 示例 1：打招呼

用户输入：

```text
打招呼
```

任务计划：

```text
task_1: left_2rad reset hold_reset
```

说明：未上举状态下 `left_2rad` 的语义是“打招呼”。动作之间不强制复位，但任务完成后必须 `reset`。

## 示例 2：泡咖啡

用户输入：

```text
泡咖啡
```

任务计划：

```text
task_1: lift_up left_2rad put_down reset hold_reset
```

说明：`left_2rad` 在 `lift_up` 之后执行，语义是“泡咖啡”。

## 示例 3：泡咖啡后握手

用户输入：

```text
泡咖啡后握手
```

任务计划：

```text
task_1: lift_up left_2rad put_down right_2rad reset hold_reset
```

说明：`put_down` 后 `arm_lift = down`，因此 `right_2rad` 是“握手”。

## 示例 4：泡浓咖啡

用户输入：

```text
泡浓咖啡
```

任务计划：

```text
task_1: lift_up left_2rad right_2rad right_2rad put_down reset
idle: hold_reset
```

说明：上举后 `left_2rad right_2rad right_2rad` 的复合语义是“泡浓咖啡”。

## 示例 5：泡淡咖啡

用户输入：

```text
泡淡咖啡
```

任务计划：

```text
task_1: lift_up left_2rad left_2rad left_2rad put_down reset
idle: hold_reset
```

说明：上举后 `left_2rad left_2rad left_2rad` 的复合语义是“泡淡咖啡”。

## 示例 6：整圈动作已删除

用户输入：

```text
右转一圈
```

任务计划：

```text
stop
```

说明：`right_circle` 已删除；LLM 不允许输出整圈动作 token。

## 示例 7：一句话拆成多个任务

用户输入：

```text
先上举左转，然后放下；再右转
```

任务计划：

```text
task_1: lift_up left_2rad put_down reset
task_2: right_2rad reset
idle: hold_reset
```

说明：第一个任务是“泡咖啡”，第二个任务是“握手”。每个任务完成后都要复位。

## 示例 8：中途停止

用户输入：

```text
停止当前任务
```

任务操作：

```text
stop
hold_reset
```

说明：停止任务不关闭仿真服务端。
