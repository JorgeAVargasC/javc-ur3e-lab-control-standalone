"""Minimal UR3e control through MoveIt 2 (move_group): read and move the arm joints."""

import threading
import time
from typing import Any

from rclpy.action import ActionClient
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from rclpy.task import Future
from geometry_msgs.msg import Pose
from moveit_msgs.action import MoveGroup
from moveit_msgs.msg import CollisionObject, Constraints, JointConstraint, MoveItErrorCodes, PlanningScene
from moveit_msgs.srv import ApplyPlanningScene
from sensor_msgs.msg import JointState
from shape_msgs.msg import SolidPrimitive

PLANNING_GROUP = "robot"
WORLD_FRAME = "world"
ARM_JOINTS = (
    "shoulder_pan_joint",
    "shoulder_lift_joint",
    "elbow_joint",
    "wrist_1_joint",
    "wrist_2_joint",
    "wrist_3_joint",
)
SPEED_SCALING = 0.1            # fraction of the robot's maximum velocity and acceleration
JOINT_TOLERANCE_RAD = 0.001
PLANNING_ATTEMPTS = 10
PLANNING_TIME_S = 5.0
FLOOR_SIZE_M = (2.0, 2.0, 0.05)
FLOOR_TOP_Z_M = -0.001         # just below the robot base, so plans never go through the table
POLL_PERIOD_S = 0.01


class RobotController(Node):
    """Move the UR3e arm with MoveIt. Blocks until MoveIt and the joint states are available."""

    def __init__(self) -> None:
        super().__init__("robot_controller")
        self._joint_positions: dict[str, float] = {}
        self.create_subscription(JointState, "/joint_states", self._on_joint_states, 10)
        self._move_client = ActionClient(self, MoveGroup, "move_action")
        self._scene_client = self.create_client(ApplyPlanningScene, "apply_planning_scene")

        # Callbacks run in a background thread, so the public methods can block while waiting.
        executor = MultiThreadedExecutor()
        executor.add_node(self)
        threading.Thread(target=executor.spin, daemon=True).start()

        self.get_logger().info("Waiting for MoveIt (move_group)...")
        self._move_client.wait_for_server()
        self._scene_client.wait_for_service()
        while not all(joint in self._joint_positions for joint in ARM_JOINTS):
            time.sleep(POLL_PERIOD_S)
        self._add_floor()

    def current_joints(self) -> list[float]:
        """Current arm joint positions (rad), in ARM_JOINTS order."""
        return [self._joint_positions[joint] for joint in ARM_JOINTS]

    def move_joints(self, target: list[float]) -> bool:
        """Plan and execute a move to the target joint positions (rad). Returns True on success."""
        constraints = Constraints()
        for joint, position in zip(ARM_JOINTS, target):
            constraints.joint_constraints.append(JointConstraint(
                joint_name=joint, position=float(position),
                tolerance_above=JOINT_TOLERANCE_RAD, tolerance_below=JOINT_TOLERANCE_RAD, weight=1.0))

        goal = MoveGroup.Goal()
        goal.request.group_name = PLANNING_GROUP
        goal.request.goal_constraints.append(constraints)
        goal.request.num_planning_attempts = PLANNING_ATTEMPTS
        goal.request.allowed_planning_time = PLANNING_TIME_S
        goal.request.max_velocity_scaling_factor = SPEED_SCALING
        goal.request.max_acceleration_scaling_factor = SPEED_SCALING
        goal.request.start_state.is_diff = True          # plan from the current robot state
        goal.planning_options.planning_scene_diff.is_diff = True

        goal_handle = self._wait(self._move_client.send_goal_async(goal))
        if not goal_handle.accepted:
            return False
        result = self._wait(goal_handle.get_result_async()).result
        return result.error_code.val == MoveItErrorCodes.SUCCESS

    def _on_joint_states(self, msg: JointState) -> None:
        self._joint_positions.update(zip(msg.name, msg.position))

    def _add_floor(self) -> None:
        """Add a box under the robot to the planning scene as the table/floor."""
        floor_pose = Pose()
        floor_pose.position.z = FLOOR_TOP_Z_M - FLOOR_SIZE_M[2] / 2
        floor_pose.orientation.w = 1.0

        floor = CollisionObject(id="floor", operation=CollisionObject.ADD)
        floor.header.frame_id = WORLD_FRAME
        floor.primitives.append(SolidPrimitive(type=SolidPrimitive.BOX, dimensions=list(FLOOR_SIZE_M)))
        floor.primitive_poses.append(floor_pose)

        request = ApplyPlanningScene.Request(scene=PlanningScene(is_diff=True))
        request.scene.robot_state.is_diff = True
        request.scene.world.collision_objects.append(floor)
        self._wait(self._scene_client.call_async(request))

    @staticmethod
    def _wait(future: Future) -> Any:
        """Block until a ROS future (resolved by the background executor) is done."""
        while not future.done():
            time.sleep(POLL_PERIOD_S)
        return future.result()
