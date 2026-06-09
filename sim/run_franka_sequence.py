"""Run a validated LLM_VLA action sequence on a Franka Panda in Isaac Sim."""

from __future__ import annotations

import argparse
import os
import sys
import traceback
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from llm_vla.sim_actions import joint_targets_for_sequence  # noqa: E402
from llm_vla.sim_runtime import should_force_exit_after_run  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run LLM_VLA action tokens on a Franka Panda.")
    parser.add_argument("--sequence", required=True, help='Action sequence, for example: "left_2rad right_2rad reset".')
    parser.add_argument("--max_steps", type=int, default=180, help="Maximum simulation steps before stopping.")
    parser.add_argument("--action_steps", type=int, default=30, help="Simulation steps for each action token.")
    parser.add_argument("--reset_steps", type=int, default=60, help="Simulation steps for each reset token.")
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


def resolve_joint_ids(robot: Articulation, joint_names: set[str]) -> dict[str, int]:
    joint_ids_by_name: dict[str, int] = {}
    for joint_name in sorted(joint_names):
        joint_ids = robot.find_joints(joint_name)[0]
        if not joint_ids:
            raise RuntimeError(f"joint not found: {joint_name}")
        joint_ids_by_name[joint_name] = joint_ids[0]
    return joint_ids_by_name


def run_sequence() -> None:
    targets = joint_targets_for_sequence(
        args_cli.sequence,
        action_steps=args_cli.action_steps,
        reset_steps=args_cli.reset_steps,
    )

    sim_cfg = sim_utils.SimulationCfg(dt=0.01)
    sim = sim_utils.SimulationContext(sim_cfg)
    sim.set_camera_view([2.5, 2.0, 1.8], [0.0, 0.0, 0.4])

    robot = design_scene()
    sim.reset()

    joint_ids_by_name = resolve_joint_ids(
        robot,
        {
            joint_name
            for target_step in targets
            for joint_name in target_step.joint_targets
        },
    )

    joint_pos = robot.data.default_joint_pos.clone()
    joint_vel = robot.data.default_joint_vel.clone()
    robot.write_joint_state_to_sim(joint_pos, joint_vel)
    robot.reset()

    executed_steps = 0
    for target_step in targets:
        if executed_steps >= args_cli.max_steps:
            break
        steps_to_run = min(target_step.step_count, args_cli.max_steps - executed_steps)
        for _ in range(steps_to_run):
            joint_target = robot.data.default_joint_pos.clone()
            for joint_name, target_rad in target_step.joint_targets.items():
                joint_target[:, joint_ids_by_name[joint_name]] = torch.tensor(target_rad, device=robot.device)
            robot.set_joint_position_target(joint_target)
            robot.write_data_to_sim()
            sim.step()
            robot.update(sim.get_physics_dt())
            executed_steps += 1
        print(f"{target_step.token} {target_step.joint_targets}")


if __name__ == "__main__":
    exit_code = 0
    try:
        run_sequence()
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
