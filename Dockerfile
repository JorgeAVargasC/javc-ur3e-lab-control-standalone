# Standalone image for the UR3e lab robots: ROS 2 Jazzy + UR driver + MoveIt 2 + RViz.
FROM ros:jazzy

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
        ros-jazzy-ur \
        ros-jazzy-moveit \
        ros-jazzy-rviz2 \
        ros-jazzy-xacro \
        python3-colcon-common-extensions \
        python3-pip \
        libgl1-mesa-dri \
        cmake libboost-all-dev python3-dev \
    && pip install --break-system-packages ur_rtde \
    && rm -rf /var/lib/apt/lists/*

# Runs any command with ROS and the workspace (once built) sourced.
COPY with-ros.sh /usr/local/bin/with-ros
RUN sed -i 's/\r$//' /usr/local/bin/with-ros && chmod +x /usr/local/bin/with-ros
ENTRYPOINT ["with-ros"]
