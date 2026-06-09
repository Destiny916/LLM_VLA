"""Run a persistent Franka Panda Isaac Sim server for LLM_VLA IPC requests."""

from __future__ import annotations

import argparse
import os
import sys
import traceback
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from llm_vla.server import serve_forever  # noqa: E402
from llm_vla.sim_actions import ACTION_STEPS, RESET_STEPS, joint_targets_for_sequence  # noqa: E402
from llm_vla.sim_runtime import should_force_exit_after_run  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a persistent LLM_VLA Franka IPC server.")
    parser.add_argument("--host", default="127.0.0.1", help="TCP host to bind.")
    parser.add_argument("--port", type=int, default=8765, help="TCP port to bind.")
    parser.add_argument("--action_steps", type=int, default=ACTION_STEPS, help="Simulation steps for each action token.")
    parser.add_argument("--reset_steps", type=int, default=RESET_STEPS, help="Simulation steps for each reset token.")
    parser.add_argument(
        "--graceful_close",
        action="store_true",
        help="Call SimulationApp.close() before exiting. This can hang on some Windows Isaac Sim setups.",
    )
    return parser


parser = build_parser()

try:
    from isaaclab.app import AppLauncher
except ModuleNotFoundError as exc:  # pragma: no cover - only hit outside IsaacLab Python
    raise SystemExit("IsaacLab is required. Run with D:\\il\\env\\Scripts\\python.exe from the LLM_VLA root.") from exc

AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

import torch  # noqa: E402

import isaaclab.sim as sim_utils  # noqa: E402
from isaaclab.assets import Articulation  # noqa: E402
from isaaclab_assets import FRANKA_PANDA_CFG  # noqa: E402


def design_scene() -> Articulation:
    ground_cfg = sim_utils.GroundPlaneCfg()
    ground_cfg.func("/World/defaultGroundPlane", ground_cfg)

    light_cfg = sim_utils.DomeLightCfg(intensity=3000.0, color=(0.75, 0.75, 0.75))
    light_cfg.func("/World/Light", light_cfg)

    robot_cfg = FRANKA_PANDA_CFG.replace(prim_path="/World/Robot")
    robot_cfg.init_state.pos = (0.0, 0.0, 0.0)
    return Articulation(cfg=robot_cfg)


class FrankaSequenceExecutor:
    def __init__(
        self,
        sim: sim_utils.SimulationContext,
        robot: Articulation,
        action_steps: int,
        reset_steps: int,
    ):
        self.sim = sim
        self.robot = robot
        self.action_steps = action_steps
        self.reset_steps = reset_steps
        self.joint_ids_by_name: dict[str, int] = {}

    def __call__(self, sequence: str) -> None:
        targets = joint_targets_for_sequence(
            sequence,
            action_steps=self.action_steps,
            reset_steps=self.reset_steps,
        )
        self._ensure_joint_ids(
            {
                joint_name
                for target_step in targets
                for joint_name in target_step.joint_targets
            }
        )
        for target_step in targets:
            for _ in range(target_step.step_count):
                joint_target = self.robot.data.default_joint_pos.clone()
                for joint_name, target_rad in target_step.joint_targets.items():
                    joint_target[:, self.joint_ids_by_name[joint_name]] = torch.tensor(
                        target_rad,
                        device=self.robot.device,
                    )
                self.robot.set_joint_position_target(joint_target)
                self.robot.write_data_to_sim()
                self.sim.step()
                self.robot.update(self.sim.get_physics_dt())
            print(f"{target_step.token} {target_step.joint_targets}", flush=True)

    def _ensure_joint_ids(self, joint_names: set[str]) -> None:
        for joint_name in sorted(joint_names):
            if joint_name in self.joint_ids_by_name:
                continue
            joint_ids = self.robot.find_joints(joint_name)[0]
            if not joint_ids:
                raise RuntimeError(f"joint not found: {joint_name}")
            self.joint_ids_by_name[joint_name] = joint_ids[0]


def create_executor() -> FrankaSequenceExecutor:
    sim_cfg = sim_utils.SimulationCfg(dt=0.01)
    sim = sim_utils.SimulationContext(sim_cfg)
    sim.set_camera_view([2.5, 2.0, 1.8], [0.0, 0.0, 0.4])

    robot = design_scene()
    sim.reset()

    joint_pos = robot.data.default_joint_pos.clone()
    joint_vel = robot.data.default_joint_vel.clone()
    robot.write_joint_state_to_sim(joint_pos, joint_vel)
    robot.reset()

    return FrankaSequenceExecutor(sim, robot, args_cli.action_steps, args_cli.reset_steps)


def main() -> int:
    executor = create_executor()
    print(f"LLM_VLA Franka server listening on {args_cli.host}:{args_cli.port}", flush=True)
    serve_forever(args_cli.host, args_cli.port, executor)
    return 0


if __name__ == "__main__":
    exit_code = 0
    try:
        exit_code = main()
    except KeyboardInterrupt:
        print("LLM_VLA Franka server stopped", flush=True)
    except Exception:
        traceback.print_exc()
        exit_code = 1

    sys.stdout.flush()
    sys.stderr.flush()
    if should_force_exit_after_run(args_cli.graceful_close):
        os._exit(exit_code)
    else:
        simulation_app.close()
        raise SystemExit(exit_code)
