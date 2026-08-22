#!/usr/bin/env bash
# Turn a plain Ubuntu machine into a SYLTRA hub.
#
#   sudo ./infrastructure/scripts/install-hub.sh
#
# Idempotent: run it again after a code change and it re-syncs and restarts.
# It installs nothing it does not need, and it stops before the one step a
# person has to do by hand — creating the Home Assistant token — because a
# script that invents a credential is a script that puts one somewhere.
set -euo pipefail

HUB_USER=syltra
HUB_HOME=/opt/syltra
DATA_DIR=/var/lib/syltra
ENV_FILE=/etc/syltra/hub.env
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

say() { printf '\n\033[1m%s\033[0m\n' "$*"; }

[ "$(id -u)" -eq 0 ] || { echo "run this with sudo"; exit 1; }

say "1/6  packages"
apt-get update -qq
# curl for uv's installer, git so the hub can be updated in place.
apt-get install -y -qq curl git ca-certificates >/dev/null

say "2/6  docker (Home Assistant and the MQTT broker run in it)"
if ! command -v docker >/dev/null; then
  curl -fsSL https://get.docker.com | sh >/dev/null
fi

say "3/6  uv (pinned Python 3.12 — no system Python is touched)"
if ! command -v uv >/dev/null; then
  curl -LsSf https://astral.sh/uv/install.sh | UV_INSTALL_DIR=/usr/local/bin sh >/dev/null
fi

say "4/6  the hub's own user and directories"
id -u "$HUB_USER" >/dev/null 2>&1 || useradd --system --home "$HUB_HOME" --shell /usr/sbin/nologin "$HUB_USER"
mkdir -p "$HUB_HOME" "$DATA_DIR" /etc/syltra
# The hub runs as its own user for the same reason a web server does: an
# integration that goes wrong should not be able to read the rest of the disk.
if [ "$HERE" != "$HUB_HOME" ]; then
  cp -a "$HERE/." "$HUB_HOME/"
fi
chown -R "$HUB_USER:$HUB_USER" "$HUB_HOME" "$DATA_DIR"

say "5/6  dependencies, from the lockfile"
sudo -u "$HUB_USER" env HOME="$HUB_HOME" /usr/local/bin/uv sync --all-packages --locked --directory "$HUB_HOME"

say "6/6  the service"
install -m 0644 "$HUB_HOME/infrastructure/systemd/syltra-hub.service" /etc/systemd/system/
if [ ! -f "$ENV_FILE" ]; then
  install -m 0600 "$HUB_HOME/infrastructure/systemd/hub.env.example" "$ENV_FILE"
  cat <<'NEXT'

  ──────────────────────────────────────────────────────────────────
  Two things left, and both need a person:

  1. Home Assistant, if it is not already running here:

       docker run -d --name homeassistant --restart=unless-stopped \
         --network=host -v /var/lib/syltra/homeassistant:/config \
         ghcr.io/home-assistant/home-assistant:stable

     Open http://<this-machine>:8123, create the account, add your devices.

  2. A token for SYLTRA to read the house with:

       Home Assistant → your profile → Security → Long-lived access tokens

     Put it in /etc/syltra/hub.env as HOME_ASSISTANT_TOKEN, then:

       sudo systemctl enable --now syltra-hub
       journalctl -u syltra-hub -f

     The log prints the console address and the owner token for this run.
  ──────────────────────────────────────────────────────────────────

NEXT
else
  systemctl daemon-reload
  systemctl restart syltra-hub || true
  echo "  restarted. journalctl -u syltra-hub -f"
fi
