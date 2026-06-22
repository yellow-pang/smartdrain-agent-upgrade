#!/usr/bin/env sh
set -eu

cd "${DEPLOY_DIR:?DEPLOY_DIR is required}"
docker compose -p "$COMPOSE_PROJECT_NAME" up --detach --build --remove-orphans
docker compose -p "$COMPOSE_PROJECT_NAME" ps
