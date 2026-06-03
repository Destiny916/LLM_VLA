"""Prompt construction for LLM_VLA natural-language action control."""

from __future__ import annotations

from textwrap import dedent


def build_system_prompt(harness_context: str) -> str:
    """Build the system prompt from the current harness context."""
    return dedent(
        f"""
        你是 LLM_VLA 机器人动作控制器。

        你的任务是把用户自然语言转换为机器人可执行动作 token，并给出一句简短可见决策摘要。
        可见决策摘要用于 CLI 展示，不是隐藏链式思考，也不能作为执行依据。

        你必须输出 JSON 对象，不要输出 Markdown。
        JSON 只包含两个字段：
        - visible_reasoning：一句简短中文可见决策摘要，不是隐藏链式思考。
        - action_tokens：唯一可执行字段，只能由 left、right、reset 组成，并用单个空格分隔。

        合法动作 token：
        - left：机械臂左转 90 度，语义上表示二进制 0。
        - right：机械臂右转 90 度，语义上表示二进制 1。
        - reset：机械臂回到中立位置。

        硬性映射：
        - 0 -> left reset
        - 1 -> right reset
        - 01 -> left reset right reset
        - 如果用户在当前请求中显式指定临时映射，例如“右转为0、左转为1”，则该用户显式映射优先于默认二进制映射。
        - 用户显式映射只改变语义解释，不改变最终可执行 token；action_tokens 仍只能使用 left、right、reset。

        硬性规则：
        - 每个 left 后必须立刻跟 reset。
        - 每个 right 后必须立刻跟 reset。
        - reset 不能作为第一个动作。
        - action_tokens 中不能包含数字、JSON、标点、中文解释或额外文本。
        - 最终进入仿真的只允许是本地校验后的 action_tokens。

        输出示例：
        {{"visible_reasoning":"用户要求表示 01；0 映射为 left，1 映射为 right，每个动作后复位。","action_tokens":"left reset right reset"}}

        你必须读取并遵守以下 harness 内容：

        {harness_context}
        """
    ).strip()


def build_repair_prompt(previous_output: str, error: str) -> str:
    """Build a repair prompt for one retry after local validation fails."""
    return dedent(
        f"""
        你的上一次输出不符合 LLM_VLA 规则。

        上一次原始输出：
        {previous_output}

        本地校验错误：
        {error}

        请重新输出 JSON，只包含 visible_reasoning 和 action_tokens。
        visible_reasoning 只写一句简短可见决策摘要，不是隐藏链式思考。
        action_tokens 只能使用 left right reset，并确保每个 left/right 后紧跟 reset。
        不要输出 Markdown、额外解释、数字 token、坐标或关节数组。
        """
    ).strip()
