#!/usr/bin/env bash
set -euo pipefail

if [ ! -f .env ]; then
  cp .env.example .env
  echo "[bootstrap] 已创建 .env，请按需修改 API_TOKEN"
fi

docker compose up -d --build
docker compose ps
