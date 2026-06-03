"""Runtime policy helpers for Isaac Sim scripts."""

from __future__ import annotations


def should_force_exit_after_run(graceful_close: bool) -> bool:
    """Return whether the script should skip SimulationApp.close()."""
    return not graceful_close
