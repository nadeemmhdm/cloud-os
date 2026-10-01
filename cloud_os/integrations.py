import socket
from .config import load

def _port_open(host,port):
    try:
        with socket.create_connection((host,port),timeout=.25): return True
    except OSError: return False

def status():
    cfg=load(); sh=str(cfg.get("ssh_host","0.0.0.0")); sp=int(cfg.get("ssh_port",2222))
    return {
      "ssh":{"enabled":bool(cfg.get("ssh_enabled")),"type":"Cloud OS isolated SSH/SFTP gateway","host":sh,"port":sp,"running":_port_open("127.0.0.1" if sh in ("0.0.0.0","::") else sh,sp),"host_shell_exposed":False},
      "cloudflare":{"enabled":bool(cfg.get("cloudflare_enabled")),"configured":bool(cfg.get("cloudflare_tunnel"))}
    }
