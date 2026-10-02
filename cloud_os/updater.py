from __future__ import annotations
import json,threading,time,urllib.error,urllib.request
from datetime import datetime,timezone
from . import __version__
from .config import APP_DIR,_protect

REPO="nadeemmhdm/cloud-os"
INTERVAL=3600
_lock=threading.Lock(); _started=False

def _path(): return APP_DIR/"update-status.json"
def _version(v):
 out=[]
 for part in str(v).lstrip("v").split("."):
  n="".join(c for c in part if c.isdigit()); out.append(int(n or 0))
 return tuple((out+[0,0,0])[:3])
def _load():
 try:
  d=json.loads(_path().read_text(encoding="utf-8")); return d if isinstance(d,dict) else {}
 except (OSError,json.JSONDecodeError): return {}
def _save(d):
 APP_DIR.mkdir(parents=True,exist_ok=True); p=_path(); tmp=p.with_suffix(".tmp")
 tmp.write_text(json.dumps(d,indent=2),encoding="utf-8"); _protect(tmp); tmp.replace(p); _protect(p)
def update_status():
 d=_load(); d.setdefault("current_version",__version__); d.setdefault("available",False); return d
def check_now():
 with _lock:
  checked=datetime.now(timezone.utc).isoformat()
  req=urllib.request.Request(f"https://api.github.com/repos/{REPO}/releases/latest",headers={"Accept":"application/vnd.github+json","User-Agent":"cloud-os-update-checker"})
  try:
   with urllib.request.urlopen(req,timeout=10) as r: release=json.load(r)
   tag=str(release.get("tag_name","")).strip(); latest=tag.lstrip("v")
   available=bool(latest and _version(latest)>_version(__version__))
   body=str(release.get("body") or "").strip()
   d={"current_version":__version__,"latest_version":latest or None,"tag":tag or None,"available":available,"checked_at":checked,"release_name":str(release.get("name") or tag or "Cloud OS update"),"announcement":body[:1200] if available else "Cloud OS is up to date.","release_url":str(release.get("html_url") or "")}
  except urllib.error.HTTPError as e:
   d={"current_version":__version__,"available":False,"checked_at":checked,"error":f"GitHub returned HTTP {e.code}"}
  except (urllib.error.URLError,TimeoutError,OSError,ValueError):
   d={"current_version":__version__,"available":False,"checked_at":checked,"error":"Update service is temporarily unavailable."}
  _save(d); return d
def _worker():
 while True:
  try: check_now()
  except Exception: pass
  time.sleep(INTERVAL)
def start_update_checker():
 global _started
 if _started:return
 _started=True
 threading.Thread(target=_worker,name="cloud-os-update-checker",daemon=True).start()
