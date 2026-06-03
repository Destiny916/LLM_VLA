import subprocess
import sys
import unittest


class PlanCliTests(unittest.TestCase):
    def test_show_details_prints_raw_reasoning_tokens_and_validation(self):
        raw_output = '{"visible_reasoning":"用户要求表示 01。","action_tokens":"left reset right reset"}'

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "llm_vla.plan",
                "表示 01",
                "--mock-output",
                raw_output,
                "--show-details",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("API 原始输出: " + raw_output, result.stdout)
        self.assertIn("思考摘要: 用户要求表示 01。", result.stdout)
        self.assertIn("API token: left reset right reset", result.stdout)
        self.assertIn("本地校验: ok", result.stdout)


if __name__ == "__main__":
    unittest.main()
