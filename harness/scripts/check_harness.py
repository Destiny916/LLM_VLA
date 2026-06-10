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
    "rag/action_catalog.md",
    "rag/action_examples.md",
    "rag/task_rules.md",
    "rag/state_rules.md",
    "rag/safety_rules.md",
    "rag/conversation_memory.md",
    "rag/two_joint_policy.md",
    "plan_state.md",
    "scripts/check_harness.py",
)

CURRENT_TOKENS = (
    "left_2rad",
    "right_2rad",
    "lift_up",
    "put_down",
    "reset",
    "hold_reset",
    "stop",
)

REMOVED_TOKENS = ("left_circle", "right_circle")


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
        _print_failures(failures)
        return 1

    readme = read("README.md")
    rule1 = read("rules/rule1_harness_read.md")
    output_contract = read("rules/output_contract.md")
    prompt_contract = read("rules/llm_prompt_contract.md")
    skills = read("skills/franka_arm_actions.yaml")
    memory = read("memory/project_memory.md")
    plan_state = read("plan_state.md")
    rag_docs = "\n".join(
        read(relative_path)
        for relative_path in (
            "rag/action_catalog.md",
            "rag/action_examples.md",
            "rag/task_rules.md",
            "rag/state_rules.md",
            "rag/safety_rules.md",
            "rag/conversation_memory.md",
            "rag/two_joint_policy.md",
        )
    )
    combined = "\n".join((readme, rule1, output_contract, prompt_contract, skills, memory, rag_docs, plan_state))

    for text in ("Rule 1", "harness", "reset", "panda_joint1"):
        require(text in combined, f"missing required harness text: {text}", failures)

    for text in ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL", "codex"):
        require(text in combined, f"missing required project memory text: {text}", failures)

    require("P0:" in plan_state, "missing P0 plan history", failures)
    require("Current step:" in plan_state, "missing current plan step", failures)
    require("P11-complete" in plan_state, "missing P11 plan state", failures)
    require("P12-complete" in plan_state, "missing P12 plan state", failures)
    require("P13-complete" in plan_state, "missing P13 plan state", failures)
    require("P14-complete" in plan_state, "missing P14 plan state", failures)
    require("P15-complete" in plan_state, "missing P15 plan state", failures)

    for token in CURRENT_TOKENS:
        require(token in output_contract, f"missing output contract token: {token}", failures)
        require(token in prompt_contract, f"missing prompt contract token: {token}", failures)
        require(token in skills, f"missing skill token: {token}", failures)
        require(token in rag_docs, f"missing RAG action token: {token}", failures)
        require(token in memory, f"missing memory action token: {token}", failures)

    for token in REMOVED_TOKENS:
        require(token in output_contract, f"missing removed output token note: {token}", failures)
        require(token in prompt_contract, f"missing removed prompt token note: {token}", failures)
        require(token in skills, f"missing removed skill token note: {token}", failures)
        require(token in rag_docs, f"missing removed RAG token note: {token}", failures)
        require(token in memory, f"missing removed memory token note: {token}", failures)

    require("target_rad: -2.0" in skills, "missing left_2rad joint target", failures)
    require("target_rad: 2.0" in skills, "missing right_2rad joint target", failures)
    require("reset_steps: 60" in skills, "missing reset step duration", failures)
    require("requires_put_down_before_reset: true" in skills, "missing lift_up put_down constraint", failures)
    require("equivalent_to_reset: false" in skills, "missing put_down reset distinction", failures)
    require("unlocked_joints:" in skills, "missing unlocked joint policy", failures)
    require("panda_joint2" in skills, "missing vertical joint target", failures)
    require("locked_joints: keep_default" in skills, "missing locked joint reset policy", failures)
    for locked_joint in ("panda_joint3", "panda_joint4", "panda_joint5", "panda_joint6", "panda_joint7"):
        require(locked_joint not in skills, f"locked joint must not be directly targeted: {locked_joint}", failures)

    require("visible_reasoning" in prompt_contract, "missing visible_reasoning prompt contract", failures)
    require("action_tokens" in prompt_contract, "missing action_tokens prompt contract", failures)
    require("0 -> left_2rad reset" in prompt_contract, "missing binary zero prompt mapping", failures)
    require("1 -> right_2rad reset" in prompt_contract, "missing binary one prompt mapping", failures)
    require("Actions are not forced to reset after every motion" in output_contract, "missing task-level reset rule", failures)
    require("each task must finish its `reset` before the next task starts" in output_contract, "missing multi-task reset boundary rule", failures)
    require("does not replace the per-task `reset`" in output_contract, "missing idle hold reset distinction", failures)
    require("lift_up` must be followed by `put_down`" in output_contract, "missing lift/put_down output rule", failures)

    for text in ("打招呼", "握手", "泡咖啡", "做冰淇淋", "泡浓咖啡", "泡淡咖啡"):
        require(text in combined, f"missing state semantic text: {text}", failures)

    for text in ("TaskPlan", "TaskOperation", "Subtask", "task_operations", "reset_after_task"):
        require(text in memory or text in combined, f"missing task-plan contract text: {text}", failures)
    for text in ("RobotState", "semantic_history", "arm_lift", "base_target"):
        require(text in memory or text in combined, f"missing robot-state contract text: {text}", failures)
    for text in ("RAG", "task-plan JSON", "task_operations"):
        require(text in memory or text in combined, f"missing task-6 contract text: {text}", failures)
    for text in ("idle hold", "polls for CLI requests", "replaces_task_reset: false"):
        require(text in memory or text in combined, f"missing task-7 contract text: {text}", failures)
    for text in ("ConversationMemory", "existing_task_ids", "current_task_id", "conversation_context"):
        require(text in memory or text in combined, f"missing task-8 conversation text: {text}", failures)

    for relative_path in (
        "llm_vla/rag.py",
        "llm_vla/conversation.py",
        "llm_vla/state.py",
        "llm_vla/task_plan.py",
        "llm_vla/task_validation.py",
        "tests/test_rag.py",
        "tests/test_conversation.py",
        "tests/test_state.py",
        "tests/test_task_plan.py",
        "tests/test_task_validation.py",
    ):
        require((PROJECT_ROOT / relative_path).is_file(), f"missing project file: {relative_path}", failures)

    if failures:
        _print_failures(failures)
        return 1

    print("harness ok")
    return 0


def _print_failures(failures: list[str]) -> None:
    for failure in failures:
        print(failure, file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
