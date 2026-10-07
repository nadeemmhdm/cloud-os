from __future__ import annotations
import os,subprocess,sys
from pathlib import Path
from .updater import _load,_save,check_now,update_status
REPO_DIR=Path(os.getenv("CLOUD_OS_SOURCE",str(Path(os.getenv("ProgramData","C:/ProgramData"))/"CloudOs") if os.name=="nt" else "/opt/cloud-os"))
def current_commit():
 try:return subprocess.run(["git","-C",str(REPO_DIR),"rev-parse","HEAD"],capture_output=True,text=True,timeout=4,check=False).stdout.strip()[:12] or None
 except Exception:return None
def control_status():
 d=update_status();d["current_commit"]=current_commit() or d.get("current_commit");return d
def start_install(force=False,server_pid=None):
 d=_load()
 if d.get("state") in {"queued","preparing","stopping","installing"}:raise RuntimeError("An update is already running")
 if not force and not str(d.get("tag") or "").strip():d=check_now()
 source="main" if force else "release";target="origin/main" if force else str(d.get("tag") or "").strip()
 if not target:raise RuntimeError("No published release is available")
 d.update({"state":"queued","force":bool(force),"channel":source,"target":target,"current_commit":current_commit(),"error":None});_save(d)
 cmd=[sys.executable,"-m","cloud_os.update_worker","--source",source,"--target",target,"--server-pid",str(server_pid or os.getpid())]
 if force:cmd.append("--force")
 kwargs={"stdin":subprocess.DEVNULL,"stdout":subprocess.DEVNULL,"stderr":subprocess.DEVNULL,"close_fds":True}
 if os.name=="nt":kwargs["creationflags"]=getattr(subprocess,"CREATE_NEW_PROCESS_GROUP",0)|getattr(subprocess,"DETACHED_PROCESS",0)
 else:kwargs["start_new_session"]=True
 subprocess.Popen(cmd,**kwargs);return control_status()
