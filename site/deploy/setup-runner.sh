#!/usr/bin/env bash
# One-time: register a self-hosted GitHub Actions runner for this repo on Monster's
# WSL, mirroring the other repos (user gha-<name>, /var/lib/actions-runner/<name>,
# labels monster-wsl + repo name), and give it its own SSH key for deploying to Brian.
# Run from Windows:
#   wsl -d Ubuntu-24.04 -u root -- bash /mnt/f/website_stuff/repos/shitpostmax.com/site/deploy/setup-runner.sh "$(gh api -X POST repos/T3rM1nAt0-R/shitpost-max/actions/runners/registration-token --jq .token)"
# then authorize the printed public key on Brian (see the last lines of output).
set -euo pipefail
TOKEN="${1:?usage: setup-runner.sh <registration-token>}"
NAME=shitpostmax
USER_NAME="gha-$NAME"
DIR="/var/lib/actions-runner/$NAME"
TEMPLATE=/var/lib/actions-runner/nirajsangani   # copy the runner build already installed

[ "$(id -u)" = 0 ] || { echo "run as root (sudo, or wsl -u root)"; exit 1; }
id "$USER_NAME" >/dev/null 2>&1 || useradd --system --create-home --shell /usr/sbin/nologin "$USER_NAME"
if [ ! -x "$DIR/config.sh" ]; then
  mkdir -p "$DIR"
  cp -a "$TEMPLATE"/{bin,externals,config.sh,run.sh,svc.sh,env.sh,safe_sleep.sh} "$DIR"/ 2>/dev/null || cp -a "$TEMPLATE"/{bin,externals,config.sh,run.sh,svc.sh,env.sh} "$DIR"/
  chown -R "$USER_NAME:$USER_NAME" "$DIR"
fi
cd "$DIR"
sudo -u "$USER_NAME" ./config.sh --unattended --replace \
  --url https://github.com/T3rM1nAt0-R/shitpost-max \
  --token "$TOKEN" \
  --name "niraj-wsl-$NAME" \
  --labels "monster-wsl,$NAME" \
  --work _work
./svc.sh install "$USER_NAME" || true   # already installed on a re-run
./svc.sh start
./svc.sh status | head -5

# Deploy key used by deploy/ship.sh. It never leaves this runner user's home.
HOME_DIR=$(getent passwd "$USER_NAME" | cut -d: -f6)
KEY="$HOME_DIR/.ssh/brian_deploy"
if [ ! -f "$KEY" ]; then
  install -d -m 700 -o "$USER_NAME" -g "$USER_NAME" "$HOME_DIR/.ssh"
  sudo -u "$USER_NAME" ssh-keygen -q -t ed25519 -N '' -C "gha-shitpostmax deploy" -f "$KEY"
fi
echo
echo "Authorize this key on Brian (from Windows):"
echo "  wsl -d Ubuntu-24.04 -u root -- cat $KEY.pub | ssh niraj@192.168.0.21 'sed \"s/^/restrict /\" >> ~/.ssh/authorized_keys'"
