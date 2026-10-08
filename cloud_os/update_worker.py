from __future__ import annotations
import argparse,json,os,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
from .config import APP_DIR,_protect

REPO_DIR=Path(os.getenv("CLOUD_OS_SOURCE",str(Path(os.getenv("ProgramData","C:/ProgramData"))/"CloudOs") if os.name=="nt" else "/opt/cloud-os"))
STATUS=APP_DIR/"update-status.json"

def now():return datetime.now(timezone.utc).isoformat()
def save(**values):
 APP_DIR.mkdir(parents=True,exist_ok=True)
 try:current=json.loads(STATUS.read_text(encoding="utf-8")) if STATUS.exists() else {}
 except Exception:current={}
 current.update(values);tmp=STATUS.with_suffix(".tmp");tmp.write_text(json.dumps(current,indent=2),encoding="utf-8");_protect(tmp);tmp.replace(STATUS);_protect(STATUS)
def run(args,check=True,timeout=None):
 r=subprocess.run(args,capture_output=True,text=True,check=False,timeout=timeout)
 if check and r.returncode:raise RuntimeError((r.stderr or r.stdout or "command failed").strip()[:1200])
 return r
def verify_cloud_os():
 # Verify only Cloud OS runtime dependencies. Global environment conflicts in unrelated apps must not fail this update.
 code="import cloud_os,fastapi,uvicorn,psutil,typer,multipart,asyncssh; print(cloud_os.__version__)"
 return run([sys.executable,"-c",code],timeout=20).stdout.strip()
def restart():
 if os.name=="nt":subprocess.run(["schtasks","/Run","/TN","CloudOs"],capture_output=True,check=False)
 else:subprocess.Popen([sys.executable,"-m","cloud_os.cli","start"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
def stop_server(pid):
 if not pid:return
 time.sleep(2)
 try:
  if os.name=="nt":subprocess.run(["taskkill","/PID",str(pid),"/T","/F"],capture_output=True,check=False)
  else:os.kill(pid,15)
 except Exception:pass
 time.sleep(2)
def _release_version(target):return str(target or "").strip().lstrip("vV")

def main():
 p=argparse.ArgumentParser();p.add_argument("--source",choices=["release","main"],default="release");p.add_argument("--target",required=True);p.add_argument("--server-pid",type=int,default=0);p.add_argument("--force",action="store_true");a=p.parse_args()
 old="";old_ref="";server_stopped=False
 try:
  save(state="preparing",worker_pid=os.getpid(),started_at=now(),finished_at=None,error=None,force=bool(a.force),channel=a.source,target=a.target)
  if not (REPO_DIR/".git").exists():raise RuntimeError(f"Cloud OS source checkout not found at {REPO_DIR}")
  dirty=run(["git","-C",str(REPO_DIR),"status","--porcelain","--untracked-files=normal"],timeout=15).stdout.strip()
  if dirty:raise RuntimeError("Source checkout has local changes; refusing to overwrite them: "+dirty[:500])
  old=run(["git","-C",str(REPO_DIR),"rev-parse","HEAD"],timeout=10).stdout.strip();old_ref=run(["git","-C",str(REPO_DIR),"symbolic-ref","--quiet","--short","HEAD"],False,10).stdout.strip()
  # Network fetch and target validation happen before stopping Cloud OS to minimize dashboard downtime.
  run(["git","-C",str(REPO_DIR),"fetch","--prune","--tags","origin"],timeout=90)
  target_commit=run(["git","-C",str(REPO_DIR),"rev-parse","--verify",f"{a.target}^{{commit}}"],timeout=10).stdout.strip()
  save(state="stopping",previous_commit=old[:12],target=a.target,target_commit=target_commit[:12])
  if os.name=="nt":subprocess.run(["schtasks","/End","/TN","CloudOs"],capture_output=True,check=False)
  stop_server(a.server_pid);server_stopped=True;save(state="installing")
  run(["git","-C",str(REPO_DIR),"checkout","--detach",target_commit],timeout=30)
  run([sys.executable,"-m","pip","install","--upgrade","--no-deps","--disable-pip-version-check",str(REPO_DIR)],timeout=180)
  v=verify_cloud_os()
  if a.source=="release":
   expected=_release_version(a.target)
   if expected and _release_version(v)!=expected:raise RuntimeError(f"Release version mismatch: target {expected}, installed {v}")
  new=run(["git","-C",str(REPO_DIR),"rev-parse","HEAD"],timeout=10).stdout.strip()
  save(state="success",installed_version=v,current_commit=new[:12],finished_at=now(),worker_pid=None,error=None,rollback=None,rollback_error=None)
  restart()
 except Exception as exc:
  rollback_error=None
  if old and server_stopped:
   try:
    run(["git","-C",str(REPO_DIR),"checkout","--detach",old],False,30)
    if old_ref:run(["git","-C",str(REPO_DIR),"checkout",old_ref],False,30)
    run([sys.executable,"-m","pip","install","--upgrade","--no-deps","--disable-pip-version-check",str(REPO_DIR)],False,180)
   except Exception as rb:rollback_error=str(rb)
  save(state="failed",finished_at=now(),worker_pid=None,error=str(exc)[:1500],rollback=("failed" if rollback_error else "restored") if server_stopped else "not-needed",rollback_error=(rollback_error or None))
  if server_stopped:restart()
if __name__=="__main__":main()
