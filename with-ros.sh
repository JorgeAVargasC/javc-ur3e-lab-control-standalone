#!/usr/bin/env bash
# Source ROS 2 and the workspace (if built), then run the given command.
source /opt/ros/jazzy/setup.bash
if [ -f /ws/install/setup.bash ]; then source /ws/install/setup.bash; fi
exec "$@"
