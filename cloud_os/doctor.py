import os,platform,shutil,socket
from .config import load,CONFIG_FILE
from .files import storage_root
from .terminal import available_shells

def report():
    cfg=load(); checks=[]
    def add(name,ok,detail=""): checks.append({"name":name,"ok":bool(ok),"detail":detail})
    add("Configuration",CONFIG_FILE.exists(),str(CONFIG_FILE))
    root=storage_root(); add("Storage",root.exists() and root.is_dir(),str(root))
    add("Owner password",bool(cfg.get("admin_password_hash")),"configured" if cfg.get("admin_password_hash") else "run cloud-os setup")
    shells=available_shells()
    expected="powershell" if os.name=="nt" else "bash"
    add("Host terminal",expected in shells,f"{expected} ({', '.join(shells) if shells else 'none detected'})")
    add("SSH client",bool(shutil.which("ssh")),"optional client; Cloud OS provides its own SSH gateway")
    add("Cloudflare",bool(shutil.which("cloudflared")),"optional cloudflared binary")
    try:
        port=int(cfg.get("port",8765))
        if not 1 <= port <= 65535: raise ValueError("port outside 1-65535")
        host=str(cfg.get("host","127.0.0.1"))
        with socket.socket() as s: in_use=s.connect_ex((host,port))==0
        add("Configured port",True,f"{host}:{port} ({'in use' if in_use else 'available'})")
    except Exception as exc: add("Configured port",False,str(exc))
    critical={"Configuration","Storage","Owner password","Host terminal","Configured port"}
    return {"platform":platform.platform(),"healthy":all(x["ok"] for x in checks if x["name"] in critical),"checks":checks}
