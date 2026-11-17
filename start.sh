#!/usr/bin/env bash
# (Re)start the container with the settings in .env and follow the log.
# The first run builds the image (several minutes; after editing the Dockerfile: docker compose build). Ctrl+C only stops following the log; stop with ./stop.sh
set -euo pipefail
cd "$(dirname "$0")"

docker compose down
docker compose up -d
docker compose logs -f
