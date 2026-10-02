from __future__ import annotations
import json, os, re, shutil, subprocess, threading, time
from pathlib import Path
from .config import APP_DIR, load, save

SECRET_FILE=APP_DIR/"cloudflare-secret.json"
LOG_FILE=APP_DIR/"cloudflared.log"
_LOCK=threading.RLock()
_PROCESS: subprocess.Popen|None=None

def _protect(path:Path):
    try:
        if os.name!="nt": path.chmod(0o600)
    except OSError: pass

def _read_token()->str:
    try:
        data=json.loads(SECRET_FILE.read_text(encoding="utf-8"))
        return str(data.get("tunnel_token","")).strip() if isinstance(data,dict) else ""
    except (OSError,json.JSONDecodeError): return ""

def _write_token(token:str):
    APP_DIR.mkdir(parents=True,exist_ok=True); tmp=SECRET_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps({"tunnel_token":token}),encoding="utf-8")
    _protect(tmp); tmp.replace(SECRET_FILE); _protect(SECRET_FILE)

def configured()->bool: return bool(_read_token())
def process_running()->bool:
    return bool(_PROCESS and _PROCESS.poll() is None)

def _tail()->str:
    try:
        lines=LOG_FILE.read_text(encoding="utf-8",errors="replace").splitlines()[-20:]
        text="\n".join(lines)
        # Defense in depth: never return JWT-like/tunnel-token material to the browser.
        return re.sub(r"eyJ[A-Za-z0-9._-]{20,}","[REDACTED]",text)[-5000:]
    except OSError: return ""

def _version()->str:
    exe=shutil.which("cloudflared")
    if not exe:return ""
    try:return subprocess.run([exe,"--version"],capture_output=True,text=True,timeout=4).stdout.strip()[:160]
    except (OSError,subprocess.SubprocessError):return ""

def start_connector():
    global _PROCESS
    with _LOCK:
        if process_running(): return True
        cfg=load()
        if not cfg.get("cloudflare_enabled"): return False
        token=_read_token(); exe=shutil.which("cloudflared")
        if not exe or not token:return False
        APP_DIR.mkdir(parents=True,exist_ok=True)
        log=open(LOG_FILE,"a",encoding="utf-8")
        flags=getattr(subprocess,"CREATE_NO_WINDOW",0) if os.name=="nt" else 0
        # Official remotely-managed tunnel form: cloudflared tunnel run --token TOKEN.
        _PROCESS=subprocess.Popen([exe,"tunnel","run","--token",token],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,creationflags=flags)
        log.close()
        time.sleep(.8)
        return process_running()

def stop_connector():
    global _PROCESS
    with _LOCK:
        p=_PROCESS; _PROCESS=None
        if p and p.poll() is None:
            p.terminate()
            try:p.wait(timeout=5)
            except subprocess.TimeoutExpired:p.kill(); p.wait(timeout=3)

def connect(token:str,label:str="Existing Cloudflare Tunnel"):
    token=(token or "").strip()
    if len(token)<40 or any(ch.isspace() for ch in token):raise ValueError("A valid Cloudflare tunnel token is required")
    if not shutil.which("cloudflared"):raise RuntimeError("cloudflared is not installed or is not on PATH")
    stop_connector(); _write_token(token)
    cfg=load(); cfg["cloudflare_enabled"]=True; cfg["cloudflare_tunnel"]=(label or "Existing Cloudflare Tunnel").strip()[:120]; cfg["secure_cookies"]=True; save(cfg)
    if not start_connector():
        detail=_tail()
        raise RuntimeError("cloudflared exited during startup"+(f": {detail[-700:]}" if detail else ""))
    return status()

def disconnect():
    stop_connector()
    try:SECRET_FILE.unlink(missing_ok=True)
    except OSError:pass
    cfg=load(); cfg["cloudflare_enabled"]=False; cfg["cloudflare_tunnel"]=""; save(cfg)
    return status()

def restart():
    if not configured():raise ValueError("Cloudflare Tunnel is not configured")
    stop_connector()
    if not start_connector():
        detail=_tail(); raise RuntimeError("cloudflared connector could not be restarted"+(f": {detail[-700:]}" if detail else ""))
    return status()

def status():
    cfg=load(); running=process_running(); log=_tail()
    return {"configured":configured(),"enabled":bool(cfg.get("cloudflare_enabled")),"connector_running":running,
      "label":str(cfg.get("cloudflare_tunnel","")),"token_stored":configured(),"cloudflared_version":_version(),
      "diagnostic":("" if running else log)}
