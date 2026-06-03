"""Validate the LLM_VLA harness contract."""

from __future__ import annotations

import sys
from pathlib import Path


HARNESS_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = HARNESS_DIR.parent

REQUIRED_FILES = (
    "README.md",
    "rules/rule1_harness_read.md",
    "rules/output_contract.md",
    "rules/llm_prompt_contract.md",
    "skills/franka_arm_actions.yaml",
    "memory/project_memory.md",
    "plan_state.md",
    "scripts/check_harness.py",
)


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def read(relative_path: str) -> str:
    return (HARNESS_DIR / relative_path).read_text(encoding="utf-8")


def main() -> int:
    failures: list[str] = []

    for relative_path in REQUIRED_FILES:
        require((HARNESS_DIR / relative_path).is_file(), f"missing {relative_path}", failures)

    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1

    readme = read("README.md")
    rule1 = read("rules/rule1_harness_read.md")
    output_contract = read("rules/output_contract.md")
    prompt_contract = read("rules/llm_prompt_contract.md")
    skills = read("skills/franka_arm_actions.yaml")
    memory = read("memory/project_memory.md")
    plan_state = read("plan_state.md")
    combined = "\n".join((readme, rule1, output_contract, prompt_contract, skills, memory, plan_state))

    for text in ("Rule 1", "每次", "必须先读取", "left", "right", "reset", "panda_joint1"):
        require(text in combined, f"missing required harness text: {text}", failures)

    for text in ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL", "codex"):
        require(text in combined, f"missing required project memory text: {text}", failures)

    require("P0: spec 与 harness 设计阶段" in plan_state, "missing P0 plan history", failures)
    require("Current step:" in plan_state, "missing current plan step", failures)
    require("target_rad: -1.57079632679" in skills, "missing left 90 degree joint target", failures)
    require("target_rad: 1.57079632679" in skills, "missing right 90 degree joint target", failures)
    require("target_degrees: -90" in skills, "missing left target degrees", failures)
    require("target_degrees: 90" in skills, "missing right target degrees", failures)
    require("target_rad: 0.0" in skills, "missing reset joint target", failures)
    require("visible_reasoning" in prompt_contract, "missing visible_reasoning prompt contract", failures)
    require("action_tokens" in prompt_contract, "missing action_tokens prompt contract", failures)
    require("0 -> left reset" in prompt_contract, "missing binary zero prompt mapping", failures)
    require("1 -> right reset" in prompt_contract, "missing binary one prompt mapping", failures)

    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1

    print("harness ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
