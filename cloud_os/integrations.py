import shutil, socket
from .config import load
from .cloudflare import status as cloudflare_status

def _port_open(host,port):
    try:
        with socket.create_connection((host,port),timeout=.25): return True
    except OSError: return False

def status():
    cfg=load(); sh=str(cfg.get("ssh_host","127.0.0.1")); sp=int(cfg.get("ssh_port",2222))
    probe="127.0.0.1" if sh in ("0.0.0.0","::") else sh
    cf=bool(shutil.which("cloudflared")); managed=cloudflare_status()
    return {
      "ssh":{
        "enabled":bool(cfg.get("ssh_enabled")),
        "type":"Cloud OS native server SSH gateway",
        "host":sh,"port":sp,"running":_port_open(probe,sp),
        "native_server_shell":True,
        "local_command":f"ssh -p {sp} USER@127.0.0.1",
        "cloudflare_origin":f"ssh://127.0.0.1:{sp}",
        "loopback_only":sh in ("127.0.0.1","::1","localhost"),
      },
      "cloudflare":{
        "enabled":bool(cfg.get("cloudflare_enabled")),
        "configured":bool(cfg.get("cloudflare_tunnel")),
        "installed":cf,
        "tunnel":str(cfg.get("cloudflare_tunnel","")),
        "web_origin":f"http://127.0.0.1:{int(cfg.get('port',8765))}",
        "ssh_origin":f"ssh://127.0.0.1:{sp}",
        "ssh_client_proxy":"cloudflared access ssh --hostname %h",
        "connector_running":managed["connector_running"],
        "token_stored":managed["token_stored"],
      }
    }
