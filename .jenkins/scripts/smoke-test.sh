#!/usr/bin/env sh
set -eu

cd "${DEPLOY_DIR:?DEPLOY_DIR is required}"

for attempt in $(seq 1 12); do
    if docker compose -p "$COMPOSE_PROJECT_NAME" ps --format json | grep -q '"healthy"'; then
        break
    fi
    sleep 5
done

curl --fail --silent --show-error http://127.0.0.1:8099/ >/dev/null
curl --fail --silent --show-error http://127.0.0.1:8099/api/dashboard/summary >/dev/null
