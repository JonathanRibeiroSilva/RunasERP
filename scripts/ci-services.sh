#!/usr/bin/env bash
# Runs the test suite of every service (or of the dirs given) in ONE CI job.
#
#   scripts/ci-services.sh --listar        prints api-gateway + services/<dir>, one per line
#   scripts/ci-services.sh [<dir>...]      no arguments = all of them
#
# Why one job and not a matrix leg per service: GitHub rounds every job up to the
# minute, so eight legs of ~0.8 min bill 8 minutes for ~3 s of tests each. The cost
# that is left is pip and the Postgres container, and both are paid once here.
#
# Each service still gets what a leg of its own had:
# - its own process of pytest, run from its own directory: the services import flat
#   (`from main import app`, `from config import settings`), so two of them in one
#   process fight over which `main` sits on sys.path first;
# - its own virtualenv, because the pins differ between services;
# - its own database (erp_<name>) and Redis DB (<i>, 0..15), because the conftests
#   truncate tables and flush Redis, and alembic stamps one version table per schema.
# It runs them all and fails at the end, so one red service does not hide the others.
#
# Expects Postgres and Redis on localhost and PGPASSWORD / SECRET_KEY / the gateway's
# *_URL variables in the environment (the ci.yml job sets them).
set -uo pipefail

cd "$(dirname "$0")/.."

listar() {
  echo api-gateway
  # LC_ALL=C: the order must not depend on the runner's locale.
  LC_ALL=C ls -d services/*/ | sed 's:/$::'
}

if [ "${1:-}" = "--listar" ]; then
  listar
  exit 0
fi

if [ "$#" -gt 0 ]; then dirs=("$@"); else mapfile -t dirs < <(listar); fi

# One Redis DB per service: redis-server ships 16 of them.
if [ "${#dirs[@]}" -gt 16 ]; then
  echo "::error::${#dirs[@]} services, but Redis only has DBs 0..15" >&2
  exit 1
fi

tmp="${RUNNER_TEMP:-/tmp}"

# Runs under `set -e` in its own subshell (see the loop), so the first failing
# command ends this service and nothing else.
roda_servico() {
  local dir=$1 i=$2 nome=$3 venv=$4 log=$5
  createdb -h localhost -U erp "erp_$nome"
  python -m venv "$venv"
  # The service's own pins, not a test-only list: the point is to run the code
  # against the versions the image ships. pip's cache is shared between venvs.
  "$venv/bin/pip" install -q -r "$dir/requirements.txt" -r tests/requirements.txt
  # What db-init does in production before any service boots: schemas, grants,
  # and the shared audit function the 2026-08-28 revisions attach triggers to.
  psql -h localhost -U erp -d "erp_$nome" -v ON_ERROR_STOP=1 -q -f postgres/init-schemas.sql
  export DATABASE_URL="postgresql+asyncpg://erp:erp@localhost:5432/erp_$nome"
  export REDIS_URL="redis://localhost:6379/$i"
  export PATH="$venv/bin:$PATH"
  cd "$dir"
  # The whole chain against an empty database. Production was stamped at a
  # baseline and never did this; without this step the first to try would be
  # a new VPS, with the container dying on boot.
  alembic upgrade head
  pytest tests -p no:cacheprovider 2>&1 | tee "$log"
}

tabela="| serviço | resultado |"$'\n'"|---|---|"
falhou=0
i=0
for dir in "${dirs[@]}"; do
  nome=$(basename "$dir" | tr - _)
  log="$tmp/pytest-$nome.log"
  : > "$log"
  echo "::group::$dir"
  # A standalone statement, not `if ( ... )`: set -e is ignored inside a condition.
  ( set -e; roda_servico "$dir" "$i" "$nome" "$tmp/venv-$nome" "$log" )
  rc=$?
  echo "::endgroup::"
  resumo=$(grep -E '[0-9]+ (passed|failed|error)' "$log" | tail -1)
  if [ "$rc" -eq 0 ]; then
    tabela+=$'\n'"| $dir | ok · ${resumo:-sem resumo} |"
  else
    falhou=1
    tabela+=$'\n'"| $dir | FALHOU · ${resumo:-parou antes do pytest} |"
  fi
  i=$((i + 1))
done

echo
echo "$tabela"
if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then echo "$tabela" >> "$GITHUB_STEP_SUMMARY"; fi
exit "$falhou"
