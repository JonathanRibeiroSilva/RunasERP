#!/usr/bin/env bash
# The sha that is live, kept as the newest successful deployment of the `production`
# environment on GitHub.
#
#   GH_TOKEN=... GITHUB_REPOSITORY=owner/repo scripts/production-sha.sh get
#   GH_TOKEN=... GITHUB_REPOSITORY=owner/repo scripts/production-sha.sh set <sha>
#
# `get` prints the sha, or nothing when none was recorded yet. `set` is called only
# after a green health check, by the deploy workflow.
#
# Not a git tag on purpose: moving a tag back to a commit whose .github/workflows
# differ (a manual rollback to an older sha) is refused to GITHUB_TOKEN, by `git push`
# and by the REST API alike (card 114). A deployment is only a record, so any sha goes.
set -euo pipefail

repo=${GITHUB_REPOSITORY:?GITHUB_REPOSITORY must be owner/repo}

case ${1:-} in
  get)
    # Fails here, not inside the loop, if the API call does.
    lista=$(gh api "repos/$repo/deployments?environment=production&per_page=10" --jq '.[] | "\(.id) \(.sha)"')
    # The newest one without a success status (a `set` that died half way) is skipped.
    while read -r id sha; do
      if [ "$(gh api "repos/$repo/deployments/$id/statuses?per_page=1" --jq '.[0].state')" = success ]; then
        echo "$sha"
        break
      fi
    done <<<"$lista" ;;
  set)
    sha=${2:?usage: production-sha.sh set <sha>}
    id=$(jq -n --arg ref "$sha" '{ref: $ref, environment: "production", auto_merge: false, required_contexts: [], description: "sha no ar"}' |
      gh api -X POST "repos/$repo/deployments" --input - --jq .id)
    gh api -X POST "repos/$repo/deployments/$id/statuses" -f state=success --silent ;;
  *)
    echo "usage: production-sha.sh get | set <sha>" >&2
    exit 2 ;;
esac
