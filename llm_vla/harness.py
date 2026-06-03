"""Harness loading helpers."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HARNESS_DIR = PROJECT_ROOT / "harness"
CORE_HARNESS_FILES = (
    "README.md",
    "rules/rule1_harness_read.md",
    "rules/output_contract.md",
    "rules/llm_prompt_contract.md",
    "skills/franka_arm_actions.yaml",
    "memory/project_memory.md",
    "plan_state.md",
)


def read_core_harness() -> str:
    """Read the required harness files in the declared order."""
    chunks: list[str] = []
    for relative_path in CORE_HARNESS_FILES:
        path = HARNESS_DIR / relative_path
        chunks.append(f"## {relative_path}\n{path.read_text(encoding='utf-8').strip()}")
    return "\n\n".join(chunks)
