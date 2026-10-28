#!/usr/bin/env bash
# Runs the auth smoke test inside the production images that were just built.
#
#   scripts/ci-smoke-auth.sh <env-file> <prod-service>...
#
# Shared by the PR gate (job `build` of ci.yml) and by the publish job of the deploy
# workflow, so both prove the same thing about the same images. The env file is the
# compose template that resolves REGISTRY and TAG; the services are the compose names
# (api-gateway-prod, vendas-prod).
#
# A green build only proves pip resolved the requirements — it never runs a line of
# the app. bcrypt 5.0 installed perfectly and then broke every login on the first
# request, because passlib could not read its version and hash() started rejecting a
# 9-character password as "longer than 72 bytes". Nothing in CI called hash(), so it
# shipped.
#
# This runs the real primitive inside the real image with the real pins. The gateway
# authenticates operators and vendas authenticates storefront customers, so the
# caller passes both.
#
# ponytail: covers password hashing only, because that is what broke and what a
# dependency bump can break without failing the build. Widen it the next time a bump
# reaches production through the same blind spot.
set -euo pipefail

cd "$(dirname "$0")/.."

env_file=${1:?usage: ci-smoke-auth.sh <env-file> <prod-service>...}
shift

# Kept on one line per statement: python -c does not dedent, so an indented block
# here is an IndentationError, not a test.
check='from passlib.context import CryptContext; ctx = CryptContext(schemes=["bcrypt"], deprecated="auto"); h = ctx.hash("smoke-test-123"); assert ctx.verify("smoke-test-123", h), "rejected the correct password"; assert not ctx.verify("wrong", h), "accepted a wrong password"; print("auth primitives ok")'

for svc in "$@"; do
  echo "== $svc"
  # docker run, not compose run: compose wants the service's external volumes to
  # exist before it starts anything, and this needs no network, no database and no
  # volume — just the interpreter inside the image. The tag still comes from the
  # compose config, so REGISTRY and TAG stay defined in one place.
  img="$(docker compose --env-file "$env_file" \
    -f docker-compose.prod.yml -f docker-compose.build.yml \
    config --format json \
    | python3 -c 'import json,sys; print(json.load(sys.stdin)["services"][sys.argv[1]]["image"])' "$svc")"
  docker run --rm --entrypoint python "$img" -c "$check"
done
