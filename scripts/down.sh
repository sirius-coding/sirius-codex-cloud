#!/usr/bin/env bash
set -euo pipefail

if [ "${1:-}" = "" ]; then
  docker compose down
  exit 0
fi

docker compose stop "$1"
docker compose rm -f "$1"
