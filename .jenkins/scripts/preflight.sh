#!/usr/bin/env sh
set -eu

: "${DEPLOY_DIR:?DEPLOY_DIR is required}"
: "${COMPOSE_PROJECT_NAME:?COMPOSE_PROJECT_NAME is required}"

command -v docker >/dev/null
command -v git >/dev/null
command -v curl >/dev/null
docker compose version >/dev/null

test -d "$DEPLOY_DIR"
test -w "$DEPLOY_DIR"
test -S /var/run/docker.sock
test -f "$DEPLOY_DIR/.env"
