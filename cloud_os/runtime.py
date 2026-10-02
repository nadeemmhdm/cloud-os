from __future__ import annotations
import shutil,subprocess
from .config import load
from .ssh_gateway import start_background

def start_cloudflare():
    cfg=load()
    if not cfg.get("cloudflare_enabled"): return None
    tunnel=str(cfg.get("cloudflare_tunnel","")).strip()
    exe=shutil.which("cloudflared")
    if not exe or not tunnel: return None
    return subprocess.Popen([exe,"tunnel","run",tunnel],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

def prepare_integrations():
    # Cloud OS owns this host-native shell SSH gateway. Host sshd is never started.
    ssh_thread=start_background()
    return {"cloudflare":start_cloudflare(),"ssh":ssh_thread}
