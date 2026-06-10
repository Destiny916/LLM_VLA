# RAG 安全规则

> 用途：定义 LLM 输出、任务执行和密钥安全边界。

## LLM 输出边界

LLM 只能输出结构化任务计划，不允许输出：

- Python 代码。
- 任意关节数组。
- 任意坐标。
- 未登记动作 token。
- 解释文本作为执行内容。
- 绕过本地校验的命令。

## 可执行内容

只有本地校验通过后的动作 token 可以发给 Isaac Sim。

`visible_reasoning` 只能显示给用户，不能作为执行依据。

## 动作安全

- 所有动作必须来自 `action_catalog.md`。
- `lift_up` 与 `put_down` 必须维护 `arm_lift` 状态。
- 每个任务完成后必须 `reset`。
- 下一个任务必须在前一个任务 `reset` 完成后才能开始。
- 全部任务完成后必须进入 `hold_reset`。
- 服务端 idle hold 不能省略任务级 `reset`。
- `stop` 不允许关闭 Isaac Sim 服务端。

## API Key 安全

- 不允许把真实 API key 写入代码、Markdown、测试或提交。
- 本地运行文件 `运行代码.md` 不允许提交。
- `.env`、`local/`、`*.local.ps1` 必须保持忽略。
- 提交前应运行 secret 检查。

建议命令：

```powershell
rg -n "sk-|LLM_API_KEY=.*sk-" .
```
