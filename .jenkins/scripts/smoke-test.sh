#!/usr/bin/env sh
set -eu

cd "${DEPLOY_DIR:?DEPLOY_DIR is required}"

nginx_container="$(docker compose -p "$COMPOSE_PROJECT_NAME" ps --quiet nginx)"
test -n "$nginx_container"

for attempt in $(seq 1 12); do
    nginx_status="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$nginx_container")"
    if [ "$nginx_status" = 'healthy' ]; then
        break
    fi
    sleep 5
done

test "$nginx_status" = 'healthy'
docker compose -p "$COMPOSE_PROJECT_NAME" exec -T nginx wget -q -O /dev/null http://127.0.0.1/
docker compose -p "$COMPOSE_PROJECT_NAME" exec -T nginx wget -q -O /dev/null http://127.0.0.1/api/dashboard/summary
