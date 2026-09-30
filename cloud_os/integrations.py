import shutil
from .config import load

def status():
    cfg=load()
    return {
      "ssh":{"enabled":bool(cfg.get("ssh_enabled")),"available":bool(shutil.which("sshd") or shutil.which("ssh"))},
      "cloudflare":{"enabled":bool(cfg.get("cloudflare_enabled")),"available":bool(shutil.which("cloudflared")),"configured":bool(cfg.get("cloudflare_tunnel"))}
    }
