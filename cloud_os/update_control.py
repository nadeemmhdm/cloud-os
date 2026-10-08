from __future__ import annotations
import os,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
import psutil
from .updater import _load,_save,check_now,update_status

REPO_DIR=Path(os.getenv("CLOUD_OS_SOURCE",str(Path(os.getenv("ProgramData","C:/ProgramData"))/"CloudOs") if os.name=="nt" else "/opt/cloud-os"))
_ACTIVE_STATES={"queued","preparing","stopping","installing"}
_QUEUE_GRACE_SECONDS=20

def _now():return datetime.now(timezone.utc).isoformat()
def current_commit():
 try:return subprocess.run(["git","-C",str(REPO_DIR),"rev-parse","HEAD"],capture_output=True,text=True,timeout=4,check=False).stdout.strip()[:12] or None
 except Exception:return None

def _age_seconds(value):
 if not value:return None
 try:
  dt=datetime.fromisoformat(str(value).replace("Z","+00:00"))
  if dt.tzinfo is None:dt=dt.replace(tzinfo=timezone.utc)
  return max(0.0,(datetime.now(timezone.utc)-dt.astimezone(timezone.utc)).total_seconds())
 except (TypeError,ValueError):return None

def _worker_alive(status):
 try:pid=int(status.get("worker_pid") or 0)
 except (TypeError,ValueError):return False
 if pid<=0:return False
 try:
  proc=psutil.Process(pid)
  if not proc.is_running() or proc.status()==psutil.STATUS_ZOMBIE:return False
  try:cmd=" ".join(proc.cmdline()).lower()
  except (psutil.AccessDenied,psutil.ZombieProcess):return True
  return not cmd or "cloud_os.update_worker" in cmd
 except (psutil.NoSuchProcess,psutil.AccessDenied,ValueError):return False

def _recover_stale(status):
 if status.get("state") not in _ACTIVE_STATES:return status
 if _worker_alive(status):return status
 if status.get("state")=="queued" and not status.get("worker_pid"):
  age=_age_seconds(status.get("queued_at"))
  if age is not None and age<_QUEUE_GRACE_SECONDS:return status
 status.update({"state":"failed","finished_at":_now(),"worker_pid":None,"error":"Previous update process stopped unexpectedly. The stale update lock was cleared automatically; retry Update or Force update."})
 _save(status);return status

def control_status():
 _recover_stale(_load());d=update_status();d["current_commit"]=current_commit() or d.get("current_commit");return d

def start_install(force=False,server_pid=None):
 d=_recover_stale(_load())
 if d.get("state") in _ACTIVE_STATES:raise RuntimeError("An update is already running. Wait for it to finish before starting another update.")
 if not force:
  d=check_now()
  d=_recover_stale(d)
 source="main" if force else "release";target="origin/main" if force else str(d.get("tag") or "").strip()
 if not target:raise RuntimeError("No published release is available. Use Force update to install the latest verified main-branch build.")
 queued_at=_now();d.update({"state":"queued","queued_at":queued_at,"started_at":None,"finished_at":None,"worker_pid":None,"force":bool(force),"channel":source,"target":target,"current_commit":current_commit(),"error":None});_save(d)
 cmd=[sys.executable,"-m","cloud_os.update_worker","--source",source,"--target",target,"--server-pid",str(server_pid or os.getpid())]
 if force:cmd.append("--force")
 kwargs={"stdin":subprocess.DEVNULL,"stdout":subprocess.DEVNULL,"stderr":subprocess.DEVNULL,"close_fds":True}
 if os.name=="nt":kwargs["creationflags"]=getattr(subprocess,"CREATE_NEW_PROCESS_GROUP",0)|getattr(subprocess,"DETACHED_PROCESS",0)
 else:kwargs["start_new_session"]=True
 try:proc=subprocess.Popen(cmd,**kwargs)
 except Exception as exc:
  failed=_load();failed.update({"state":"failed","finished_at":_now(),"worker_pid":None,"error":f"Could not start update worker: {exc}"});_save(failed);raise RuntimeError(f"Could not start update worker: {exc}") from exc
 latest=_load()
 if latest.get("state") in _ACTIVE_STATES:
  latest["worker_pid"]=proc.pid;latest.setdefault("queued_at",queued_at);_save(latest)
 return control_status()
