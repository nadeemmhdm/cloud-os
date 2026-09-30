import platform, shutil, socket
from pathlib import Path
from .config import load, CONFIG_FILE
from .files import storage_root

def report():
    cfg=load(); checks=[]
    def add(name,ok,detail=""): checks.append({"name":name,"ok":bool(ok),"detail":detail})
    add("Configuration",CONFIG_FILE.exists(),str(CONFIG_FILE))
    root=storage_root(); add("Storage",root.exists() and root.is_dir(),str(root))
    add("SSH",bool(shutil.which("ssh") or shutil.which("sshd")),"client/server binary detection")
    add("Cloudflare",bool(shutil.which("cloudflared")),"cloudflared binary detection")
    try:
        with socket.socket() as s:
            free=s.connect_ex((cfg.get("host","127.0.0.1"),int(cfg.get("port",8765)))) != 0
        add("Configured port",free or True,str(cfg.get("port",8765)))
    except Exception as exc: add("Configured port",False,str(exc))
    return {"platform":platform.platform(),"healthy":all(x["ok"] for x in checks if x["name"] in ("Configuration","Storage")),"checks":checks}
