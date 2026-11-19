#!/usr/bin/env python3
"""Pick a domino tile: stand up -> home -> open -> lower -> close -> home -> stand up (still holding the tile).

Run with: ./run.sh pick_domino.py
"""

import time
from math import acos, atan2, cos, pi, sin

import rclpy

from go_home import HOME_JOINTS
from gripper_open_close import PAUSE_S, Gripper
from robot_controller import RobotController
from stand_up import UPRIGHT_JOINTS

CLOSED_WIDTH_MM = 20.0  # tile lies flat and is gripped across its width (~24 mm): aim just inside it
OPEN_WIDTH_MM = 40.0  # wide enough to clear the tile, without a big stroke
FORCE_N = 3.0  # RG2 minimum force, so the tile is not squeezed
# The real table is below the robot base, so MoveIt's default floor (at the base) blocks the lowered pose.
FLOOR_TOP_Z_M = -0.10  # collision floor for this script (m, relative to the base). Raise it if you know the real table height.
DROP_M = 0.08  # how far the tool goes down from home (vertical, tool keeps pointing down). Increase in small steps.

# UR3e link lengths (m): shoulder -> elbow, elbow -> wrist_1
UPPER_ARM_M = 0.24355
FOREARM_M = 0.2132


def lowered_joints(drop_m: float) -> list[float]:
    """Home pose moved straight down by drop_m, keeping the tool vertical (planar 2-link IK)."""
    x = FOREARM_M  # horizontal reach of wrist_1 at home
    z = UPPER_ARM_M - drop_m  # height of wrist_1 above the shoulder
    d = (x * x + z * z - UPPER_ARM_M**2 - FOREARM_M**2) / (2 * UPPER_ARM_M * FOREARM_M)
    elbow = -acos(max(-1.0, min(1.0, d)))  # elbow-up solution, same branch as home
    alpha = atan2(z, x) - atan2(FOREARM_M * sin(elbow), UPPER_ARM_M + FOREARM_M * cos(elbow))
    shoulder_lift = alpha - pi
    wrist_1 = -3 * pi / 2 - shoulder_lift - elbow  # keeps the tool pointing down
    return [HOME_JOINTS[0], shoulder_lift, elbow, wrist_1, HOME_JOINTS[4], HOME_JOINTS[5]]


def main() -> None:
    """Run the pick-and-release test."""
    rclpy.init()
    robot = RobotController(floor_top_z_m=FLOOR_TOP_Z_M)
    gripper = Gripper()
    logger = robot.get_logger()
    down = lowered_joints(DROP_M)

    steps = [
        ("Standing up", lambda: robot.move_joints(UPRIGHT_JOINTS)),
        ("Moving to home", lambda: robot.move_joints(HOME_JOINTS)),
        ("Opening gripper", lambda: gripper.move(OPEN_WIDTH_MM, FORCE_N)),
        (f"Lowering {DROP_M * 100:.0f} cm", lambda: robot.move_joints(down)),
        ("Closing gripper", lambda: gripper.move(CLOSED_WIDTH_MM, FORCE_N)),
        ("Raising to home", lambda: robot.move_joints(HOME_JOINTS)),
        ("Standing up with the tile", lambda: robot.move_joints(UPRIGHT_JOINTS)),
    ]

    try:
        for label, action in steps:
            logger.info(f"{label}...")
            if not action():
                logger.error(f"{label} failed (is the teach pendant program in Play?)")
                return
            time.sleep(PAUSE_S)
        logger.info("Done.")
    finally:
        gripper.destroy_node()
        robot.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
