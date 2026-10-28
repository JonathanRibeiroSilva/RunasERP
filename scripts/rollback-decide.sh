#!/usr/bin/env bash
# Decides what the automatic rollback of the deploy workflow may do. Prints one word:
#
#   git diff --name-only "$LIVE" "$TAG" | scripts/rollback-decide.sh "$LIVE"
#
#   sem-producao  no live sha (the producao git tag does not exist yet): nowhere to go back to
#   migration     the jump from live to the new sha added or changed an alembic migration
#   reverter      safe to put the live images back
#
# A rollback puts the old images back and nothing else: migrations run at boot, so a
# migration that already ran stays in the database, and the old code would be started
# against the new schema. That is worse than the failed deploy, so it is a human's call.
#
# Only alembic/versions/ counts. alembic.ini and env.py do not change the schema.
set -eu

live=${1-}

if [ -z "$live" ]; then
  echo sem-producao
elif grep -qE '(^|/)alembic/versions/'; then
  echo migration
else
  echo reverter
fi
