#!/usr/bin/env bash
# Waits for the readiness endpoint to answer 200.
#
#   scripts/health-ready.sh <url>
#
# HEALTH_TENTATIVAS (default 18) and HEALTH_INTERVALO (default 10 s) bound the wait:
# three minutes covers the stack coming back after the Coolify deploy reports done.
#
# /api/health/ready, not /api/health: the latter is liveness and answers 200 with
# Postgres dead. /ready probes the database, Redis and all seven services, so one
# request covers tunnel + frontend + gateway + backend, and the 503 body names which
# one is down (uptime.yml reads it the same way).
#
# -A is not cosmetic: the zone has a WAF rule that issues a managed challenge to any
# User-Agent containing curl or wget. Default curl gets a 403 at the edge, which
# would read as production down and, once the rollback exists, trigger a false one.
#
# No `set -e`: a refused connection makes curl exit non-zero, and that is just one
# more failed attempt, not a reason to stop before the retry.
set -u

url=${1:?usage: health-ready.sh <url>}
tentativas=${HEALTH_TENTATIVAS:-18}
intervalo=${HEALTH_INTERVALO:-10}

body=$(mktemp)
trap 'rm -f "$body"' EXIT

for i in $(seq "$tentativas"); do
  # `|| true`: curl exits non-zero on a timeout or refusal, while -w still prints
  # the code (000), which is not 200 and so counts as a failed attempt.
  code="$(curl -s -o "$body" --max-time 10 \
    -A 'Mozilla/5.0 (compatible; RunasDeploy/1.0; +github-actions)' \
    -w '%{http_code}' "$url" || true)"
  echo "attempt $i/$tentativas: $code $(head -c 300 "$body")"
  [ "$code" = 200 ] && exit 0
  if [ "$i" -lt "$tentativas" ]; then
    sleep "$intervalo"
  fi
done

# The readiness 503 carries {"down":[...]}; a 502 from nginx carries HTML and the
# grep finds nothing, which just leaves the line empty.
echo "down: $(grep -o '"down":\[[^]]*\]' "$body" | head -c 300)"
echo "::error::$url did not answer 200 after $tentativas attempts (last status $code)"
exit 1
