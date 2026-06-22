#!/usr/bin/env sh
set -eu

cd "${DEPLOY_DIR:?DEPLOY_DIR is required}"

docker compose -p "$COMPOSE_PROJECT_NAME" config --quiet
docker build --target lint --file frontend/Dockerfile .
docker build --target test --tag smartdrain-ai-test --file ai_service/Dockerfile .
docker run --rm smartdrain-ai-test
