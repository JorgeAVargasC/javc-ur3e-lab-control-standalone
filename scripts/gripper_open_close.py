#!/usr/bin/env python3
"""Open, close and re-open the OnRobot RG2 gripper through the rg2_driver action server.

Run with: ./run.sh gripper_open_close.py
"""

import time

import rclpy
from control_msgs.action import GripperCommand
from rclpy.action import ActionClient
from rclpy.node import Node

ACTION_NAME = "/rg2_action_server"
# Gentle settings for testing on the real robot: small stroke, low force.
OPEN_WIDTH_MM = 60.0  # RG2 maximum is 100 mm
CLOSED_WIDTH_MM = 30.0  # does not close fully, so fingers never squeeze each other
FORCE_N = 5.0  # RG2 range is 3-40 N
PAUSE_S = 2.0  # wait between moves
MOVE_TIME_S = 2.0  # time given to each move, since the driver cannot confirm it finished


class Gripper(Node):
    """Minimal client for the RG2 GripperCommand action."""

    def __init__(self) -> None:
        super().__init__("gripper_open_close")
        self._client = ActionClient(self, GripperCommand, ACTION_NAME)

    def move(self, width_mm: float, force_n: float = FORCE_N) -> bool:
        """Move the fingers to width_mm and wait until the gripper stops."""
        if not self._client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error(f"Action server {ACTION_NAME} not available (is the gripper driver running?)")
            return False

        goal = GripperCommand.Goal()
        goal.command.position = float(width_mm)
        goal.command.max_effort = float(force_n)

        send_future = self._client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, send_future)
        handle = send_future.result()
        if handle is None or not handle.accepted:
            self.get_logger().error("Goal rejected")
            return False

        result_future = handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future)
        result = result_future.result().result
        # The driver's width reading is not available on this robot (it always reports 0 mm),
        # so reached_goal is unreliable: the command itself works. Give the fingers time to move.
        if not result.reached_goal:
            self.get_logger().warn("Driver could not confirm the width; assuming the move happened")
        time.sleep(MOVE_TIME_S)
        return True


def main() -> None:
    """Open the gripper, close it, then open it again."""
    rclpy.init()
    gripper = Gripper()
    logger = gripper.get_logger()

    for label, width in (("Opening", OPEN_WIDTH_MM), ("Closing", CLOSED_WIDTH_MM), ("Opening", OPEN_WIDTH_MM)):
        logger.info(f"{label} gripper...")
        if not gripper.move(width):
            logger.error(f"{label} failed")
            break
        time.sleep(PAUSE_S)
    else:
        logger.info("Done.")

    gripper.destroy_node()
    rclpy.try_shutdown()


if __name__ == "__main__":
    main()
