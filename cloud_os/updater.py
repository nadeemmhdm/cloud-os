from __future__ import annotations
import json,os,subprocess,sys,threading,time,urllib.error,urllib.request
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
 try:return subprocess.run(["git","-C",str(REPO_DIR),"rev-parse","HEAD"],capture_output=True,text=True,timeout=4,check=False).stdout.strip()[:12] or None
 except Exception:return None
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
  if previous.get("state") in {"success","failed"}:d.update({k:previous.get(k) for k in ("state","finished_at","rollback","rollback_error") if k in previous})
  _save(d);return d
def start_install(force=False,server_pid=None):
 with _lock:
  d=_load()
  if d.get("state") in {"preparing","stopping","installing"}:raise RuntimeError("An update is already running")
  source="main" if force else "release";target="origin/main" if force else str(d.get("tag") or "").strip()
  if not target:
   d=check_now();target="origin/main" if force else str(d.get("tag") or "").strip()
  if not target:raise RuntimeError("No published release is available")
  d.update({"state":"queued","force":bool(force),"channel":source,"target":target,"error":None});_save(d)
  cmd=[sys.executable,"-m","cloud_os.update_worker","--source",source,"--target",target,"--server-pid",str(server_pid or os.getpid())]
  if force:cmd.append("--force")
  flags=getattr(subprocess,"CREATE_NEW_PROCESS_GROUP",0)|getattr(subprocess,"DETACHED_PROCESS",0) if os.name=="nt" else 0
  subprocess.Popen(cmd,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=flags,close_fds=True,start_new_session=(os.name!="nt"));return update_status()
def _worker():
 while True:
  try:check_now()
  except Exception:pass
  time.sleep(INTERVAL)
def start_update_checker():
 global _started
 if _started:return
 _started=True;threading.Thread(target=_worker,name="cloud-os-update-checker",daemon=True).start()
