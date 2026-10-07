from __future__ import annotations
import argparse,json,os,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path

REPO_DIR=Path(os.getenv("CLOUD_OS_SOURCE",str(Path(os.getenv("ProgramData","C:/ProgramData"))/"CloudOs") if os.name=="nt" else "/opt/cloud-os"))
HOME=Path(os.getenv("CLOUD_OS_HOME",str(Path.home()/".cloud-os")))
STATUS=HOME/"update-status.json"

def now():return datetime.now(timezone.utc).isoformat()
def save(**values):
 HOME.mkdir(parents=True,exist_ok=True)
 try:
  current=json.loads(STATUS.read_text(encoding="utf-8")) if STATUS.exists() else {}
 except Exception:current={}
 current.update(values);tmp=STATUS.with_suffix(".tmp");tmp.write_text(json.dumps(current,indent=2),encoding="utf-8");tmp.replace(STATUS)
def run(args,check=True):
 r=subprocess.run(args,capture_output=True,text=True,check=False)
 if check and r.returncode:raise RuntimeError((r.stderr or r.stdout or "command failed").strip()[:1200])
 return r
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
def main():
 p=argparse.ArgumentParser();p.add_argument("--source",choices=["release","main"],default="release");p.add_argument("--target",required=True);p.add_argument("--server-pid",type=int,default=0);p.add_argument("--force",action="store_true");a=p.parse_args()
 old="";old_ref=""
 try:
  save(state="preparing",started_at=now(),finished_at=None,error=None,force=bool(a.force),channel=a.source)
  if not (REPO_DIR/".git").exists():raise RuntimeError(f"Cloud OS source checkout not found at {REPO_DIR}")
  dirty=run(["git","-C",str(REPO_DIR),"status","--porcelain","--untracked-files=normal"]).stdout.strip()
  if dirty:raise RuntimeError("Source checkout has local changes; refusing to overwrite them: "+dirty[:500])
  old=run(["git","-C",str(REPO_DIR),"rev-parse","HEAD"]).stdout.strip();old_ref=run(["git","-C",str(REPO_DIR),"symbolic-ref","--quiet","--short","HEAD"],False).stdout.strip()
  save(state="stopping",previous_commit=old[:12],target=a.target)
  if os.name=="nt":subprocess.run(["schtasks","/End","/TN","CloudOs"],capture_output=True,check=False)
  stop_server(a.server_pid);save(state="installing")
  run(["git","-C",str(REPO_DIR),"fetch","--tags","origin"]);run(["git","-C",str(REPO_DIR),"checkout","--detach",a.target])
  run([sys.executable,"-m","pip","install","--upgrade","--no-deps","--disable-pip-version-check",str(REPO_DIR)])
  run([sys.executable,"-m","pip","check"]);v=run([sys.executable,"-c","import cloud_os; print(cloud_os.__version__)"]).stdout.strip();new=run(["git","-C",str(REPO_DIR),"rev-parse","HEAD"]).stdout.strip()
  save(state="success",installed_version=v,current_commit=new[:12],finished_at=now(),error=None);restart()
 except Exception as exc:
  rollback_error=None
  if old:
   try:
    run(["git","-C",str(REPO_DIR),"checkout","--detach",old],False)
    if old_ref:run(["git","-C",str(REPO_DIR),"checkout",old_ref],False)
    run([sys.executable,"-m","pip","install","--upgrade","--no-deps","--disable-pip-version-check",str(REPO_DIR)],False)
   except Exception as rb:rollback_error=str(rb)
  save(state="failed",finished_at=now(),error=str(exc)[:1500],rollback="failed" if rollback_error else "restored",rollback_error=(rollback_error or None));restart()
if __name__=="__main__":main()
