#!/usr/bin/env bash
set -euo pipefail
REPO="https://github.com/nadeemmhdm/cloud-os.git"
DIR="/opt/cloud-os"
if ! command -v git >/dev/null; then echo "git is required"; exit 1; fi
if [ -d "$DIR/.git" ]; then git -C "$DIR" pull --ff-only; else sudo git clone "$REPO" "$DIR"; fi
sudo python3 -m pip install "$DIR"
cloud-os setup
sudo cloud-os install-service
echo "Cloud Os installed. It will start automatically after Linux boots."
