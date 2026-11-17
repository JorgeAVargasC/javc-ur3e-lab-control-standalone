#!/usr/bin/env python3
"""Move the UR3e to the home position (arm up, tool pointing down).

Run with: ./run.sh go_home.py
"""

from math import pi

import rclpy

from robot_controller import RobotController

# Same order as the arm joints: shoulder_pan, shoulder_lift, elbow, wrist_1, wrist_2, wrist_3 (rad)
HOME_JOINTS = [0.0, -pi / 2, -pi / 2, -pi / 2, pi / 2, 0.0]


def main() -> None:
    """Send the arm to HOME_JOINTS and report the result."""
    rclpy.init()
    robot = RobotController()
    logger = robot.get_logger()

    logger.info("Moving to home...")
    if robot.move_joints(HOME_JOINTS):
        logger.info("At home.")
    else:
        logger.error("Move failed (is the teach pendant program in Play?)")

    robot.destroy_node()
    rclpy.try_shutdown()


if __name__ == "__main__":
    main()
