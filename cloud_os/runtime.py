from __future__ import annotations
import shutil,subprocess
from .config import load

def start_cloudflare():
    cfg=load()
    if not cfg.get("cloudflare_enabled"): return None
    tunnel=str(cfg.get("cloudflare_tunnel","")).strip()
    exe=shutil.which("cloudflared")
    if not exe or not tunnel: return None
    return subprocess.Popen([exe,"tunnel","run",tunnel],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

def prepare_integrations():
    # Cloud OS never starts/stops the host SSH daemon implicitly.
    # Host services remain under the operating system administrator's control.
    return start_cloudflare()
