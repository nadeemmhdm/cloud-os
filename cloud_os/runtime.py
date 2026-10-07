from __future__ import annotations
import json
import urllib.request
from .ssh_gateway import start_background
from .cloudflare import start_connector
from .config import load

def start_cloudflare():
    return start_connector()

def _cloud_os_already_running():
    """Return True only when the configured port belongs to a live Cloud OS instance."""
    cfg=load(); host=str(cfg.get("host","127.0.0.1")); port=int(cfg.get("port",8765))
    probe_host="127.0.0.1" if host in ("0.0.0.0","::") else host
    try:
        req=urllib.request.Request(f"http://{probe_host}:{port}/health",headers={"User-Agent":"cloud-os-startup-check"})
        with urllib.request.urlopen(req,timeout=1.5) as response:
            return response.status==200 and json.load(response).get("status")=="ok"
    except Exception:
        return False

def prepare_integrations():
    # A boot task may already own the web port. Treat that as healthy instead of
    # starting duplicate SSH/Cloudflare workers and letting Uvicorn fail with 10048.
    if _cloud_os_already_running():
        print("[OK] Cloud OS is already running; duplicate start skipped.")
        raise SystemExit(0)
    # Cloud OS owns this host-native shell SSH gateway. Host sshd is never started.
    ssh_thread=start_background()
    return {"cloudflare":start_cloudflare(),"ssh":ssh_thread}
