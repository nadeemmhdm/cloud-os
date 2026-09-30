from datetime import datetime,timezone
import json
from .config import APP_DIR
LOG=APP_DIR/"audit.log"
def record(action,detail=""):
 APP_DIR.mkdir(parents=True,exist_ok=True)
 with LOG.open("a",encoding="utf-8") as f:f.write(json.dumps({"time":datetime.now(timezone.utc).isoformat(),"action":action,"detail":str(detail)})+"\n")
def recent(limit=100):
 if not LOG.exists(): return []
 lines=LOG.read_text(encoding="utf-8",errors="replace").splitlines()[-limit:]
 out=[]
 for line in lines:
  try:out.append(json.loads(line))
  except Exception:pass
 return out
