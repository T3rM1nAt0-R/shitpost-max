#!/usr/bin/env bash
# Runs on Monster (the CI runner). Talks to Brian over ssh; the work on Brian is deploy/brian.sh.
#   deploy/ship.sh dev <sha>       upload deploy/out (from publish.sh) to dev-test.shitpostmax.com
#   deploy/ship.sh promote <sha>   point shitpostmax.com at the release dev-test is serving
#   deploy/ship.sh rollback        put shitpostmax.com back on its previous release
set -euo pipefail
cd "$(dirname "$0")"

MODE=${1:?usage: ship.sh dev|promote <sha> | rollback}
SHA=${2:-}
REMOTE=niraj@192.168.0.21
DEV_DIR=/opt/data/selfhost/shitpostmax-dev
KEY=${BRIAN_DEPLOY_KEY_FILE:-$HOME/.ssh/brian_deploy}
[ -r "$KEY" ] || { echo "Brian deploy key not readable at $KEY" >&2; exit 2; }
SSH=(ssh -i "$KEY" -o IdentitiesOnly=yes -o BatchMode=yes -o StrictHostKeyChecking=yes
     -o "UserKnownHostsFile=$PWD/brian_known_hosts" -o ConnectTimeout=8)
on_brian() { "${SSH[@]}" "$REMOTE" bash -s -- "$@" < brian.sh; }

prod_is_live() { # through Cloudflare, from outside Brian
  for _ in 1 2 3 4 5; do
    curl -fsS --max-time 20 https://shitpostmax.com/ | grep -q SHITPOSTMAX && return 0
    sleep 3
  done
  return 1
}

case $MODE in
  dev)
    [ -f out/site/index.html ] || { echo "no bundle: run deploy/publish.sh first" >&2; exit 2; }
    [ -f out/api/server.mjs ] && [ -f out/site/fleet-slugs.json ] || { echo "bundle is missing the votes api" >&2; exit 2; }
    "${SSH[@]}" "$REMOTE" "rm -rf '$DEV_DIR/.incoming' && mkdir -p '$DEV_DIR/.incoming'"
    rsync --archive --delete -e "${SSH[*]}" out/ "$REMOTE:$DEV_DIR/.incoming/"
    on_brian dev-swap "$SHA"
    # dev-test must stay behind Cloudflare Access: anonymous requests get the login redirect.
    code=$(curl -sS -o /dev/null -w '%{http_code} %{redirect_url}' --max-time 20 https://dev-test.shitpostmax.com/ || true)
    case $code in
      30[0-9]\ https://*cloudflareaccess.com*) echo "dev-test.shitpostmax.com is up behind Access" ;;
      *) echo "dev-test.shitpostmax.com did not answer with the Access login (got: $code)" >&2; exit 1 ;;
    esac
    ;;
  promote)
    on_brian promote "$SHA"
    if prod_is_live; then echo "verified https://shitpostmax.com/ is serving"; exit 0; fi
    echo "shitpostmax.com did not serve the site after promote; rolling back" >&2
    on_brian rollback
    exit 1
    ;;
  rollback)
    on_brian rollback
    prod_is_live || { echo "shitpostmax.com is not serving after rollback" >&2; exit 1; }
    ;;
  *) echo "unknown mode: $MODE" >&2; exit 2 ;;
esac
