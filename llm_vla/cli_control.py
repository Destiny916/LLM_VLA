"""Interactive LLM CLI controller for the persistent Franka simulation server."""

from __future__ import annotations

import argparse
from collections.abc import Callable
from typing import Any, Protocol

from .client import send_sequence
from .conversation import ConversationMemory
from .planner import OpenAICompatiblePlanner, PlanningResult


class PlannerLike(Protocol):
    def plan_details(
        self,
        request: str,
        **kwargs: Any,
    ) -> PlanningResult:
        """Return detailed LLM planning output."""


SendSequence = Callable[[str, int, str], dict[str, Any]]
InputFunc = Callable[[str], str]
OutputFunc = Callable[[str], None]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the LLM_VLA interactive control CLI.")
    parser.add_argument("--host", default="127.0.0.1", help="Simulation server host.")
    parser.add_argument("--port", type=int, default=8765, help="Simulation server port.")
    return parser


def run_cli(
    *,
    planner: PlannerLike,
    send_sequence_func: SendSequence,
    input_func: InputFunc = input,
    output_func: OutputFunc = print,
    host: str = "127.0.0.1",
    port: int = 8765,
) -> int:
    """Run the interactive CLI loop."""
    conversation = ConversationMemory()
    while True:
        try:
            user_input = input_func("LLM_VLA> ")
        except EOFError:
            output_func("退出 CLI")
            return 0

        request = user_input.strip()
        if not request:
            continue
        if request.lower() in {"quit", "exit"}:
            output_func("退出 CLI")
            return 0

        output_func(f"用户输入: {request}")
        try:
            result = planner.plan_details(
                request,
                existing_task_ids=conversation.existing_task_ids,
                current_task_id=conversation.current_task_id,
                conversation_context=conversation.prompt_context(),
            )
            update = conversation.apply_planning_result(result)
            output_func(f"API 原始输出: {result.raw_output}")
            output_func(f"思考摘要: {result.visible_reasoning}")
            output_func(f"API token: {update.action_tokens}")
            output_func("本地校验: ok")
            output_func(f"任务操作: {update.operations_summary}")
            output_func("当前任务队列:")
            output_func(update.queue_summary)
            output_func("机械臂状态:")
            output_func(update.state_summary)
            sim_response = send_sequence_func(host, port, update.action_tokens)
            status = sim_response.get("status")
            output_func(f"仿真结果: {status}")
            if status == "ok":
                executed = sim_response.get("executed")
                if executed:
                    output_func(f"执行序列: {executed}")
            else:
                message = sim_response.get("message")
                if message:
                    output_func(str(message))
        except Exception as exc:
            output_func("本地校验: error")
            output_func(str(exc))


def main() -> int:
    args = build_parser().parse_args()
    planner = OpenAICompatiblePlanner.from_environment()
    return run_cli(
        planner=planner,
        send_sequence_func=lambda host, port, sequence: send_sequence(host, port, sequence),
        host=args.host,
        port=args.port,
    )


if __name__ == "__main__":
    raise SystemExit(main())
