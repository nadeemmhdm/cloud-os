#!/usr/bin/env bash
set -Eeuo pipefail
REPO="https://github.com/nadeemmhdm/cloud-os.git"
DIR="/opt/cloud-os"
step(){ printf '\n[Cloud OS] %s\n' "$1"; }
fail(){ printf '[ERROR %s] %s\n' "$1" "$2" >&2; [ -z "${3:-}" ] || printf 'Fix: %s\n' "$3" >&2; exit 1; }
trap 'fail I099 "Installation stopped near line $LINENO." "Review the message above, fix the reported issue, and run the installer again."' ERR

if [ "$(id -u)" -eq 0 ]; then SUDO=""; else
  command -v sudo >/dev/null 2>&1 || fail I001 "sudo is required." "Install sudo or run this installer as root."
  SUDO="sudo"
fi

step "Checking Internet access"
if command -v curl >/dev/null 2>&1; then curl -fsSI --max-time 15 https://github.com >/dev/null || fail I002 "GitHub is not reachable." "Check Internet/DNS/proxy settings."
elif command -v wget >/dev/null 2>&1; then wget -q --spider --timeout=15 https://github.com || fail I002 "GitHub is not reachable." "Check Internet/DNS/proxy settings."
fi

install_apt(){ $SUDO apt-get update; $SUDO DEBIAN_FRONTEND=noninteractive apt-get install -y "$@"; }
install_dnf(){ $SUDO dnf install -y "$@"; }
install_pkg(){
  if command -v apt-get >/dev/null 2>&1; then install_apt "$@"
  elif command -v dnf >/dev/null 2>&1; then install_dnf "$@"
  else fail I003 "Unsupported automatic package manager." "Install Python 3.10+, python3-venv/pip and Git manually, then retry."
  fi
}

command -v git >/dev/null 2>&1 || { step "Git is missing; installing it"; install_pkg git; }
command -v python3 >/dev/null 2>&1 || { step "Python is missing; installing it"; install_pkg python3 python3-pip python3-venv; }
python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)' || fail I004 "Python 3.10 or newer is required." "Upgrade Python and retry."

if ! python3 -m pip --version >/dev/null 2>&1; then
  step "pip is missing; installing it"
  install_pkg python3-pip
fi

step "Downloading Cloud OS"
if [ -d "$DIR/.git" ]; then
  $SUDO git -C "$DIR" fetch origin main
  $SUDO git -C "$DIR" checkout main
  $SUDO git -C "$DIR" reset --hard origin/main
elif [ -e "$DIR" ]; then
  fail I005 "$DIR exists but is not a Cloud OS Git checkout." "Rename/remove that directory and retry."
else
  $SUDO git clone --depth 1 "$REPO" "$DIR"
fi

step "Creating isolated Python environment"
if [ ! -x "$DIR/.venv/bin/python" ]; then
  $SUDO python3 -m venv "$DIR/.venv" || { install_pkg python3-venv; $SUDO python3 -m venv "$DIR/.venv"; }
fi
$SUDO "$DIR/.venv/bin/python" -m pip install --upgrade pip
$SUDO "$DIR/.venv/bin/python" -m pip install --upgrade "$DIR"

step "Creating cloud-os command"
$SUDO ln -sf "$DIR/.venv/bin/cloud-os" /usr/local/bin/cloud-os

step "Running setup"
cloud-os setup

step "Startup behavior"
printf '[INFO] Linux system-wide autostart is not enabled by this development installer.\n'
printf '[INFO] Run Cloud OS as the configured user with: cloud-os start\n'
printf '[INFO] Do not run the web terminal as root.\n'

step "Verifying installation"
cloud-os doctor

printf '\n[SUCCESS] Cloud OS installation completed.\n'
printf 'Commands: cloud-os start | cloud-os status | cloud-os doctor | cloud-os update-check | cloud-os update\n'
