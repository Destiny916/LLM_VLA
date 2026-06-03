import unittest

from llm_vla.sim_runtime import should_force_exit_after_run


class SimRuntimeTests(unittest.TestCase):
    def test_force_exit_is_default_to_avoid_isaac_close_hang(self):
        self.assertTrue(should_force_exit_after_run(graceful_close=False))

    def test_graceful_close_disables_force_exit(self):
        self.assertFalse(should_force_exit_after_run(graceful_close=True))


if __name__ == "__main__":
    unittest.main()
