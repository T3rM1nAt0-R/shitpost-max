#!/usr/bin/env bash
# Runs ON BRIAN, piped over ssh by deploy/ship.sh. Never run builds here.
#   brian.sh dev-swap <sha>     put the uploaded bundle (dev/.incoming) live on dev-test
#   brian.sh promote [sha]      copy the exact release live on dev into prod
#   brian.sh rollback           put prod's go-back release (.prev) back
# Releases kept: dev candidate, prod live, prod .prev. Nothing else.
set -euo pipefail
BASE=/opt/data/selfhost
PROD=$BASE/shitpostmax        # shitpostmax.com      -> 127.0.0.1:8097
DEV=$BASE/shitpostmax-dev     # dev-test (Access)    -> 127.0.0.1:8099
ITEMS="site api Caddyfile compose.yaml RELEASE"

up() { # $1 dir, $2 project, $3 port; bind mounts hold old inodes, so always recreate
  (cd "$1" && WEB_PORT=$3 docker compose -p "$2" up -d --force-recreate --remove-orphans)
}
healthy() { # $1 port
  for _ in $(seq 1 20); do
    if curl -fsS "http://127.0.0.1:$1/" | grep -q SHITPOSTMAX \
       && curl -fsS "http://127.0.0.1:$1/api/health" | grep -q '"ok":true'; then return 0; fi
    sleep 2
  done
  return 1
}
copy_items() { # $1 from, $2 to
  for f in $ITEMS; do if [ -e "$1/$f" ]; then rm -rf "${2:?}/$f"; cp -a "$1/$f" "$2/"; fi; done
}
check_sha() { case ${1:-} in ''|*[!A-Fa-f0-9]*) echo "invalid sha: ${1:-}" >&2; exit 2 ;; esac; }

case ${1:-} in
  dev-swap)
    check_sha "${2:-}"
    [ -f "$DEV/.incoming/site/index.html" ] || { echo "nothing uploaded to $DEV/.incoming" >&2; exit 2; }
    printf '%s\n' "$2" > "$DEV/.incoming/RELEASE"
    printf 'WEB_PORT=8099\nCOMPOSE_PROJECT_NAME=shitpostmax-dev\n' > "$DEV/.env"
    copy_items "$DEV/.incoming" "$DEV"
    rm -rf "$DEV/.incoming"
    up "$DEV" shitpostmax-dev 8099
    healthy 8099 || { echo "dev-test failed its health check" >&2; exit 1; }
    echo "dev-test is serving $2"
    ;;
  promote) # sha optional: defaults to whatever dev-test serves
    dev_sha=$(cat "$DEV/RELEASE" 2>/dev/null || true)
    set -- promote "${2:-$dev_sha}"
    check_sha "$2"
    [ "$dev_sha" = "$2" ] || { echo "dev-test is on '${dev_sha}', not $2; refusing to promote an untested release" >&2; exit 2; }
    healthy 8099 || { echo "dev-test is not healthy; refusing to promote" >&2; exit 1; }
    rm -rf "$PROD/.prev.new" && mkdir "$PROD/.prev.new"
    for f in $ITEMS; do [ -e "$PROD/$f" ] && cp -a "$PROD/$f" "$PROD/.prev.new/"; done
    copy_items "$DEV" "$PROD"
    up "$PROD" shitpostmax 8097
    if healthy 8097; then
      rm -rf "$PROD/.prev" && mv "$PROD/.prev.new" "$PROD/.prev"
      echo "prod is serving $2 (go-back: $(cat "$PROD/.prev/RELEASE" 2>/dev/null || echo 'pre-pipeline release'))"
    else
      echo "prod failed its health check, restoring the previous release" >&2
      copy_items "$PROD/.prev.new" "$PROD"
      rm -rf "$PROD/.prev.new"
      up "$PROD" shitpostmax 8097
      exit 1
    fi
    ;;
  rollback)
    [ -d "$PROD/.prev/site" ] || { echo "no go-back release in $PROD/.prev" >&2; exit 2; }
    copy_items "$PROD/.prev" "$PROD"
    up "$PROD" shitpostmax 8097
    healthy 8097 || { echo "prod unhealthy after rollback" >&2; exit 1; }
    echo "prod rolled back to $(cat "$PROD/RELEASE" 2>/dev/null || echo 'pre-pipeline release')"
    ;;
  *) echo "usage: brian.sh dev-swap <sha> | promote <sha> | rollback" >&2; exit 2 ;;
esac
