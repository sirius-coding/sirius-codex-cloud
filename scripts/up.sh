#!/usr/bin/env bash
set -euo pipefail

service="${1:-freelance-api}"

case "$service" in
  freelance-api)
    docker compose up -d --build freelance-api
    ;;
  web-crawler)
    docker compose --profile crawler up -d --build web-crawler
    ;;
  booking-api)
    docker compose --profile booking up -d --build booking-api
    ;;
  expense-tracker)
    docker compose --profile expense up -d --build expense-tracker
    ;;
  file-backup-worker)
    docker compose --profile backup up -d --build file-backup-worker
    ;;
  crm-api)
    docker compose --profile crm up -d --build crm-api
    ;;
  invoice-service)
    docker compose --profile invoice up -d --build invoice-service
    ;;
  helpdesk-api)
    docker compose --profile helpdesk up -d --build helpdesk-api
    ;;
  inventory-api)
    docker compose --profile inventory up -d --build inventory-api
    ;;
  subscription-billing-api)
    docker compose --profile billing up -d --build subscription-billing-api
    ;;
  notification-hub)
    docker compose --profile notification up -d --build notification-hub
    ;;
  contract-lifecycle-api)
    docker compose --profile contract up -d --build contract-lifecycle-api
    ;;
  timesheet-api)
    docker compose --profile timesheet up -d --build timesheet-api
    ;;
  lead-scoring-api)
    docker compose --profile lead up -d --build lead-scoring-api
    ;;
  knowledge-base-api)
    docker compose --profile knowledge up -d --build knowledge-base-api
    ;;
  docs)
    docker compose --profile docs up -d docs
    ;;
  *)
    echo "Unsupported service: $service" >&2
    exit 1
    ;;
esac

docker compose ps
