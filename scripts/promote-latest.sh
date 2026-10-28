#!/usr/bin/env bash
# Points :latest at images that are already in ghcr under :<sha>.
#
#   FILES='-f docker-compose.prod.yml -f docker-compose.build.yml' scripts/promote-latest.sh <sha>
#
# Coolify and the build cache both read :latest, so moving it is the moment a
# release goes live. The deploy workflow calls this only after the test and publish
# jobs are green, and the rollback reuses it with the sha it wants back.
#
# `imagetools create` copies the manifest inside the registry: nothing is pulled to
# the runner and the layers are not rewritten, so promoting nine images is seconds
# and :latest ends up byte-identical to :<sha>.
#
# Needs the build .env in the working directory: compose refuses to resolve the
# ${VAR:?} entries without it, even for `config --images`.
set -euo pipefail

cd "$(dirname "$0")/.."

sha=${1:?usage: promote-latest.sh <sha>}
: "${FILES:?FILES must list the compose files, e.g. -f docker-compose.prod.yml -f docker-compose.build.yml}"

# $FILES is a word list on purpose. With pipefail, a config that yields no ghcr image
# (grep exits 1) fails the script instead of promoting nothing and reporting success.
TAG="$sha" docker compose $FILES config --images | grep '^ghcr\.io/' | while read -r img; do
  echo "promote $img -> ${img%:*}:latest"
  docker buildx imagetools create -t "${img%:*}:latest" "$img"
done
