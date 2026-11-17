#!/usr/bin/env bash
# Stop and remove the container (on the real robot, press Stop on the teach pendant first).
set -euo pipefail
cd "$(dirname "$0")"

docker compose down
