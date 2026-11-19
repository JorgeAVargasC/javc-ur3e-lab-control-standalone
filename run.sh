#!/usr/bin/env bash
# Run a Python script from ./scripts inside the running container: ./run.sh go_home.py [args]
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -f "scripts/${1:-}" ]; then
    echo "Usage: ./run.sh <script.py> [args]" >&2
    echo "Available scripts:" >&2
    # robot_controller.py is the shared helper module, not a runnable script
    (cd scripts && ls *.py | grep -vx robot_controller.py | sed 's/^/  /') >&2
    exit 1
fi
docker compose exec ros with-ros python3 "$@"
