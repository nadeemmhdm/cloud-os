from __future__ import annotations
import shutil, subprocess
from .config import load

def _run(cmd):
    return subprocess.run(cmd, check=False, capture_output=True, text=True)

def ensure_ssh():
    cfg=load()
    if not cfg.get("ssh_enabled"):
        return
    if shutil.which("systemctl"):
        _run(["systemctl","start","ssh"])
    elif shutil.which("powershell"):
        _run(["powershell","-NoProfile","-Command","Start-Service sshd -ErrorAction SilentlyContinue"])

def start_cloudflare():
    cfg=load()
    if not cfg.get("cloudflare_enabled"):
        return None
    tunnel=cfg.get("cloudflare_tunnel","").strip()
    exe=shutil.which("cloudflared")
    if not exe or not tunnel:
        return None
    return subprocess.Popen([exe,"tunnel","run",tunnel])

def prepare_integrations():
    ensure_ssh()
    return start_cloudflare()
