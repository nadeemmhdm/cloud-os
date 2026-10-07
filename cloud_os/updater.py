from __future__ import annotations
import json,os,threading,time,urllib.error,urllib.request
from datetime import datetime,timezone
from pathlib import Path
from . import __version__
from .config import APP_DIR,_protect

REPO="nadeemmhdm/cloud-os";INTERVAL=3600
REPO_DIR=Path(os.getenv("CLOUD_OS_SOURCE",str(Path(os.getenv("ProgramData","C:/ProgramData"))/"CloudOs") if os.name=="nt" else "/opt/cloud-os"))
_lock=threading.Lock();_started=False

def _path():return APP_DIR/"update-status.json"
def _version(v):
 out=[]
 for part in str(v).lstrip("v").split("."):
  n="".join(c for c in part if c.isdigit());out.append(int(n or 0))
 return tuple((out+[0,0,0])[:3])
def _load():
 try:
  d=json.loads(_path().read_text(encoding="utf-8"));return d if isinstance(d,dict) else {}
 except (OSError,json.JSONDecodeError):return {}
def _save(d):
 APP_DIR.mkdir(parents=True,exist_ok=True);p=_path();tmp=p.with_suffix(".tmp");tmp.write_text(json.dumps(d,indent=2),encoding="utf-8");_protect(tmp);tmp.replace(p);_protect(p)
def _commit():
 try:
  head=(REPO_DIR/".git"/"HEAD").read_text(encoding="utf-8").strip()
  if head.startswith("ref: "):
   ref=head[5:].strip();rp=REPO_DIR/".git"/ref
   if rp.exists():head=rp.read_text(encoding="utf-8").strip()
   else:
    for line in (REPO_DIR/".git"/"packed-refs").read_text(encoding="utf-8").splitlines():
     if line and not line.startswith("#") and line.endswith(" "+ref):head=line.split()[0];break
  return head[:12] if len(head)>=12 else None
 except OSError:return None
def update_status():
 d=_load();d["current_version"]=__version__;d.setdefault("available",False);d["current_commit"]=_commit() or d.get("current_commit");return d
def check_now():
 with _lock:
  previous=_load();checked=datetime.now(timezone.utc).isoformat();req=urllib.request.Request(f"https://api.github.com/repos/{REPO}/releases/latest",headers={"Accept":"application/vnd.github+json","User-Agent":"cloud-os-update-checker"})
  try:
   with urllib.request.urlopen(req,timeout=10) as r:release=json.load(r)
   tag=str(release.get("tag_name","")).strip();latest=tag.lstrip("v");available=bool(latest and _version(latest)>_version(__version__));body=str(release.get("body") or "").strip()
   d={"current_version":__version__,"current_commit":_commit(),"latest_version":latest or None,"tag":tag or None,"available":available,"checked_at":checked,"release_name":str(release.get("name") or tag or "Cloud OS update"),"announcement":body[:1200] if available else "Cloud OS is up to date.","release_url":str(release.get("html_url") or "")}
  except urllib.error.HTTPError as e:d={"current_version":__version__,"current_commit":_commit(),"available":False,"checked_at":checked,"error":f"GitHub returned HTTP {e.code}"}
  except (urllib.error.URLError,TimeoutError,OSError,ValueError):d={"current_version":__version__,"current_commit":_commit(),"available":False,"checked_at":checked,"error":"Update service is temporarily unavailable."}
  for k in ("state","finished_at","rollback","rollback_error","previous_commit","force","channel"):
   if k in previous:d[k]=previous[k]
  _save(d);return d
def _worker():
 while True:
  try:check_now()
  except Exception:pass
  time.sleep(INTERVAL)
def start_update_checker():
 global _started
 if _started:return
 _started=True;threading.Thread(target=_worker,name="cloud-os-update-checker",daemon=True).start()
