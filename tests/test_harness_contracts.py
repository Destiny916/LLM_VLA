import subprocess
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HARNESS_DIR = PROJECT_ROOT / "harness"


class HarnessContractTests(unittest.TestCase):
    def test_required_harness_files_exist(self):
        required_files = (
            "README.md",
            "rules/rule1_harness_read.md",
            "rules/output_contract.md",
            "rules/llm_prompt_contract.md",
            "skills/franka_arm_actions.yaml",
            "memory/project_memory.md",
            "plan_state.md",
            "scripts/check_harness.py",
        )

        for relative_path in required_files:
            self.assertTrue((HARNESS_DIR / relative_path).is_file(), relative_path)

    def test_rule1_requires_reading_harness_before_project_work(self):
        readme = (HARNESS_DIR / "README.md").read_text(encoding="utf-8")
        rule1 = (HARNESS_DIR / "rules" / "rule1_harness_read.md").read_text(encoding="utf-8")
        combined = readme + "\n" + rule1

        self.assertIn("Rule 1", combined)
        self.assertIn("每次", combined)
        self.assertIn("harness", combined)
        self.assertIn("必须先读取", combined)

    def test_plan_state_starts_at_p0(self):
        plan_state = (HARNESS_DIR / "plan_state.md").read_text(encoding="utf-8")

        self.assertIn("P0: spec 与 harness 设计阶段", plan_state)

    def test_harness_checker_passes(self):
        checker = HARNESS_DIR / "scripts" / "check_harness.py"

        result = subprocess.run(
            [sys.executable, str(checker)],
            cwd=PROJECT_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("harness ok", result.stdout)


if __name__ == "__main__":
    unittest.main()
