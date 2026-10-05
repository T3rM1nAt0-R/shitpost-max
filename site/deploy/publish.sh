#!/usr/bin/env bash
# Build the static export and lay it out in deploy/out/ ready to copy to Brian.
set -euo pipefail
cd "$(dirname "$0")/.."
npm ci
npm run lint
npm test
npm run build
rm -rf deploy/out && mkdir -p deploy/out
cp -a out deploy/out/site
cp deploy/compose.yaml deploy/Caddyfile deploy/out/
echo "Ready: deploy/out (copy to brian:/opt/data/selfhost/shitpostmax/)"
