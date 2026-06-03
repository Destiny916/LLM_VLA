"""CLI for the LLM_VLA planner."""

from __future__ import annotations

import argparse

from .planner import MockClient, OpenAICompatiblePlanner


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Plan a Franka action sequence from a natural-language task.")
    parser.add_argument("request", help="Natural-language task request.")
    parser.add_argument(
        "--mock-output",
        help="Use this raw model output instead of calling an OpenAI-compatible API.",
    )
    parser.add_argument(
        "--show-details",
        action="store_true",
        help="Print raw API output, visible reasoning, validated API token, and local validation status.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.mock_output is not None:
        planner = OpenAICompatiblePlanner(client=MockClient(args.mock_output))
    else:
        planner = OpenAICompatiblePlanner.from_environment()
    if args.show_details:
        result = planner.plan_details(args.request)
        print(f"API 原始输出: {result.raw_output}")
        print(f"思考摘要: {result.visible_reasoning}")
        print(f"API token: {result.action_tokens}")
        print("本地校验: ok")
    else:
        print(planner.plan(args.request))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
