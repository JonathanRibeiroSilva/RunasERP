#!/usr/bin/env bash
# Tells Coolify to deploy and waits until it reports the deployment finished.
#
#   COOLIFY_URL=... COOLIFY_TOKEN=... COOLIFY_UUID=... scripts/coolify-deploy.sh
#
# Coolify pulls :latest and restarts the stack. It reads docker-compose.prod.yml from
# this repo, which has no build sections, so there is nothing it *can* build, only pull.
# The deploy and rollback paths of the deploy workflow share this script.
#
# COOLIFY_URL must be the Cloudflare hostname in front of the tunnel, not the VPS IP.
# Pointing it at the IP asks a GitHub runner to open an *inbound* connection to
# 187.127.10.108:8000, and that is a coin flip: run 32047638162 got a reply in 0.5s,
# run 32048659255 fifteen minutes later ate a 132s connect timeout, with the host idle,
# ufw disabled, no fail2ban, port 8000 listening and zero kernel-level drops. The SYNs
# never arrived. 187.127.0.0/18 is a block Hostinger only took over in 2025, and
# reachability depends on which Azure egress the runner happens to land on. Over the
# tunnel the VPS dials Cloudflare outbound and the runner only ever talks to the
# anycast edge, which has no such problem.
#
# The retry is a seatbelt, not the fix: it turns one 132s hang into five bounded
# attempts. Nothing reaches Coolify on a connect failure, so a retried POST cannot
# double-queue a deploy.
#
# -A is not cosmetic: the zone has a WAF rule ("User-Agent suspeito") that issues a
# managed challenge to any UA containing curl or wget. Default curl sends `curl/8.x`
# and gets a 403 in 0.2s, from the edge, with Cf-Mitigated: challenge. Run 32058772049
# died exactly there. Same IP, same path, same method, only the UA changed: curl/8.5.0
# -> 403, anything Mozilla-ish -> 401 from Coolify. The edge is what answers.
#
# `set -eu` without pipefail on purpose: this is the body the workflow ran as plain
# `bash -e`, and the polling below pipes through jq and grep, where a failure on one
# half-written response must not abort the wait.
set -eu

: "${COOLIFY_URL:?}" "${COOLIFY_TOKEN:?}" "${COOLIFY_UUID:?}"

response="$(curl -fsS -X POST \
  --connect-timeout 10 --retry 5 --retry-delay 10 \
  -A 'Mozilla/5.0 (compatible; RunasDeploy/1.0; +github-actions)' \
  -H "Authorization: Bearer $COOLIFY_TOKEN" \
  "$COOLIFY_URL/api/v1/deploy?uuid=$COOLIFY_UUID&force=false")"
echo "$response"
uuid="$(printf '%s' "$response" | jq -r '.deployments[0].deployment_uuid')"

# Coolify answers as soon as it accepts the request, not when the stack is up: without
# this wait a deploy that never comes back is a green job.
#
# This used to poll the public /health URL with default curl, and the WAF rule described
# above answered it at the edge: the request never reached the VPS. The step counted that
# 403 as a pass, so it verified nothing; every run that had it (32029262468, 31853329182,
# 32047638162) burned the full 5 minutes on 403s and went green without once seeing the
# stack. Coolify's own deployment record is the check the edge cannot intercept: same
# host, same token, already in hand, no WAF rule and no new secret. It reports what
# actually happened on the VPS and it fails loudly when the deploy fails. Whether the
# app answers is the job of scripts/health-ready.sh, which runs after this.
if [ -z "$uuid" ] || [ "$uuid" = null ]; then
  echo "::error::no deployment_uuid in the trigger response"
  exit 1
fi
echo "polling deployment $uuid"
# 90 x 10s = 15 min. A cold pull of all nine images has taken ~10.
unreachable=0
for _ in $(seq 90); do
  body="$(curl -fsS --connect-timeout 10 \
    -A 'Mozilla/5.0 (compatible; RunasDeploy/1.0; +github-actions)' \
    -H "Authorization: Bearer $COOLIFY_TOKEN" \
    "$COOLIFY_URL/api/v1/deployments/$uuid")" || body=''
  status="$(printf '%s' "$body" | jq -r '.status // empty' 2>/dev/null)"
  # Losing the API mid-deploy is expected, not a failure. cloudflared is a container in
  # the very stack being deployed, so Coolify stops the tunnel this request travels
  # through; the edge then answers 530 for COOLIFY_URL until the new stack is up. Run
  # 32060269768 polled in_progress five times and then died on that 530: it failed
  # because the deploy was working. Keep asking; only give up if the tunnel never comes
  # back, which means production is down anyway.
  if [ -z "$status" ]; then
    unreachable=$((unreachable + 1))
    echo "  unreachable ($unreachable)"
    # ~45 misses: each costs up to 10s of connect timeout plus the 10s sleep, so this
    # is roughly 10-15 minutes of silence.
    if [ "$unreachable" -ge 45 ]; then
      echo "::error::Coolify unreachable for ~15 min; last body: $body"
      exit 1
    fi
    sleep 10
    continue
  fi
  unreachable=0
  echo "  $status"
  case "$status" in
    finished|success) echo "deploy $uuid finished"; exit 0 ;;
    failed|error|cancelled*)
      # Without this the job says only "ended as failed" and the reason lives in the
      # Coolify UI. The same record already carries the deploy log; print it so the
      # failure is readable here. The grep is not cosmetic: a nine-image pull writes
      # thousands of progress lines, so an unfiltered tail shows only download bars and
      # never the error that ended the deploy.
      printf '%s' "$body" | jq -r '.logs' 2>/dev/null | jq -r '.[].output' 2>/dev/null | grep -vE 'Downloading|Pulling fs layer|Download complete|Extracting|Waiting' | tail -50
      echo "::error::deploy $uuid ended as $status"; exit 1 ;;
  esac
  sleep 10
done
echo "::error::deploy $uuid still $status after 15 minutes"
exit 1
