# Deploying shitpostmax.com

Builds and tests run on Monster (self-hosted runner `niraj-wsl-shitpostmax`, labels
`monster-wsl,shitpostmax`). Brian only serves. Workflow: `.github/workflows/site.yml`.

| When | What runs |
| --- | --- |
| Any push or same-repo PR touching `site/` | `publish.sh` (npm ci, lint, unit tests, static build, bundle), typecheck, script syntax check. The bundle is uploaded once and reused. |
| Push to `main` | the same, then `ship.sh dev` puts that bundle on **dev-test.shitpostmax.com** (Cloudflare Access, Niraj only). |
| Run the workflow by hand on `main`, action `promote` | `ship.sh promote` copies the exact release dev-test serves onto **shitpostmax.com**. Nothing is rebuilt. Refuses if dev-test is unhealthy or on a different commit. |
| Run it by hand, action `rollback` | puts shitpostmax.com back on the previous release. |

Every step checks itself: dev and prod must answer `/` with the site and `/api/health` on
Brian, prod must serve through Cloudflare, dev must answer anonymous requests with the
Access login. A failed prod check restores the previous release automatically.

## Brian layout

- `/opt/data/selfhost/shitpostmax` – prod, compose project `shitpostmax`, `127.0.0.1:8097`.
  `.prev/` is the go-back release.
- `/opt/data/selfhost/shitpostmax-dev` – dev-test, compose project `shitpostmax-dev`,
  `127.0.0.1:8099`, its own votes volume.

Retention is three releases: dev candidate, prod live, prod go-back. Each `RELEASE` file
holds the commit it was built from.

Containers are always recreated (`--force-recreate`) because the bind mounts would
otherwise keep pointing at replaced files.

## Manual use

```bash
bash deploy/publish.sh                 # build the bundle into deploy/out
bash deploy/ship.sh dev "$(git rev-parse HEAD)"
bash deploy/ship.sh promote            # whatever dev-test serves
bash deploy/ship.sh rollback
```

`ship.sh` uses `~/.ssh/brian_deploy` (override with `BRIAN_DEPLOY_KEY_FILE`) and the pinned
host key in `brian_known_hosts`. `setup-runner.sh` registers the runner and creates that key.
