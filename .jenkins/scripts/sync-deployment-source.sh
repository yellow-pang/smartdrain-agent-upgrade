#!/usr/bin/env sh
set -eu

: "${DEPLOY_DIR:?DEPLOY_DIR is required}"
: "${DEPLOY_BRANCH:?DEPLOY_BRANCH is required}"

export GIT_SSH_COMMAND="ssh -i ${GIT_SSH_KEY:?GIT_SSH_KEY is required} -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new"

if [ ! -d "$DEPLOY_DIR/.git" ]; then
    : "${GIT_REPOSITORY_SSH_URL:?GIT_REPOSITORY_SSH_URL is required for the first clone}"
    temporary_clone_dir="$(mktemp -d)"
    trap 'rm -rf "$temporary_clone_dir"' EXIT
    git clone --branch "$DEPLOY_BRANCH" "$GIT_REPOSITORY_SSH_URL" "$temporary_clone_dir"
    cp -a "$temporary_clone_dir"/. "$DEPLOY_DIR"/
    rm -rf "$temporary_clone_dir"
    trap - EXIT
fi

git -C "$DEPLOY_DIR" fetch --prune origin "$DEPLOY_BRANCH"
git -C "$DEPLOY_DIR" checkout --force "$DEPLOY_BRANCH"
git -C "$DEPLOY_DIR" reset --hard "origin/$DEPLOY_BRANCH"
git -C "$DEPLOY_DIR" rev-parse HEAD > "$DEPLOY_DIR/.deployed-revision"
