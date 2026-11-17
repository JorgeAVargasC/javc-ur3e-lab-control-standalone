#!/usr/bin/env python3
"""Hello world for the real UR3e: turn the base 15 degrees and come back.

Only the base joint moves, starting from wherever the robot is, at 10% speed.
Run with: ./run.sh hello_robot.py
"""

from math import radians

import rclpy

from robot_controller import RobotController

BASE_JOINT_INDEX = 0  # shoulder_pan_joint
BASE_ROTATION_RAD = radians(15)


def main() -> None:
    """Rotate the base forth and back, reporting each step."""
    rclpy.init()
    robot = RobotController()
    logger = robot.get_logger()

    start = robot.current_joints()
    target = list(start)
    target[BASE_JOINT_INDEX] += BASE_ROTATION_RAD

    logger.info("Hello! Turning the base 15 degrees...")
    if robot.move_joints(target):
        logger.info("Going back to the start position...")
        robot.move_joints(start)
        logger.info("Done.")
    else:
        logger.error("Move failed (is the teach pendant program in Play?)")

    robot.destroy_node()
    rclpy.try_shutdown()


if __name__ == "__main__":
    main()
