from datetime import datetime,timezone
import json,os,threading
from collections import deque
from .config import APP_DIR
LOG=APP_DIR/"audit.log"
MAX_BYTES=5*1024*1024
_LOCK=threading.RLock()

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
    entry={"time":datetime.now(timezone.utc).isoformat(),"action":str(action)[:128],"detail":str(detail)[:4096]}
    with _LOCK:
        APP_DIR.mkdir(parents=True,exist_ok=True); _rotate()
        with LOG.open("a",encoding="utf-8") as f: f.write(json.dumps(entry,ensure_ascii=False)+"\n")
        _protect()

def recent(limit=100):
    limit=max(1,min(int(limit),1000))
    if not LOG.exists(): return []
    with _LOCK:
        try:
            with LOG.open("r",encoding="utf-8",errors="replace") as f:
                lines=deque(f,maxlen=limit)
        except OSError:return []
    out=[]
    for line in lines:
        try: out.append(json.loads(line))
        except (json.JSONDecodeError,TypeError): pass
    return out
