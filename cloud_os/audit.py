from datetime import datetime,timezone
import json,os
from .config import APP_DIR
LOG=APP_DIR/"audit.log"
MAX_BYTES=5*1024*1024

def _protect():
    try:
        if os.name!="nt" and LOG.exists(): LOG.chmod(0o600)
    except OSError: pass

def _rotate():
    if LOG.exists() and LOG.stat().st_size>=MAX_BYTES:
        old=LOG.with_suffix(".log.1")
        old.unlink(missing_ok=True)
        LOG.replace(old)
        try:
            if os.name!="nt": old.chmod(0o600)
        except OSError: pass

def record(action,detail=""):
    APP_DIR.mkdir(parents=True,exist_ok=True); _rotate()
    entry={"time":datetime.now(timezone.utc).isoformat(),"action":str(action)[:128],"detail":str(detail)[:4096]}
    with LOG.open("a",encoding="utf-8") as f: f.write(json.dumps(entry,ensure_ascii=False)+"\n")
    _protect()

def recent(limit=100):
    if not LOG.exists(): return []
    limit=max(1,min(int(limit),1000))
    lines=LOG.read_text(encoding="utf-8",errors="replace").splitlines()[-limit:]
    out=[]
    for line in lines:
        try: out.append(json.loads(line))
        except Exception: pass
    return out
