#!/usr/bin/env sh
set -eu

cd "${DEPLOY_DIR:?DEPLOY_DIR is required}"
docker compose -p "$COMPOSE_PROJECT_NAME" --profile seed run --rm seed
