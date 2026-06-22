#!/usr/bin/env sh
set -eu

cd "${DEPLOY_DIR:?DEPLOY_DIR is required}"
docker compose -p "$COMPOSE_PROJECT_NAME" logs --tail=100 nginx backend ai-service
