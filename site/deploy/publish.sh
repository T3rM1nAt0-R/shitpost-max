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
# Votes API (zero-dependency Node server) and its slug allowlist.
mkdir -p deploy/out/api
cp -a api/server.mjs api/lib.mjs deploy/out/api/
node -e '
const fs = require("fs");
const fleet = JSON.parse(fs.readFileSync("src/lib/fleet.json", "utf8"));
const slugs = fleet.map((s) => (typeof s === "string" ? s : s && s.slug)).filter((s) => typeof s === "string");
if (slugs.length === 0) throw new Error("no slugs in src/lib/fleet.json");
fs.writeFileSync("deploy/out/site/fleet-slugs.json", JSON.stringify(slugs));
console.log("fleet-slugs.json:", slugs.length, "slugs");
'
echo "Ready: deploy/out"
