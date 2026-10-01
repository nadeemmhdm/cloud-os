from __future__ import annotations
import os,shutil,subprocess,threading,uuid
from pathlib import Path
from .files import storage_root
MAX_OUTPUT=20000
MAX_COMMAND=8000
ALLOWED_SHELLS={"powershell","bash"}
_SESSIONS={}
_LOCK=threading.Lock()

def available_shells():
 out=[]
 if os.name=="nt" and (shutil.which("pwsh") or shutil.which("powershell")): out.append("powershell")
 if os.name!="nt" and shutil.which("bash"): out.append("bash")
 return out

def _exe(shell):
 if shell not in ALLOWED_SHELLS: raise ValueError("Unsupported shell")
 if shell=="powershell":
  x=shutil.which("pwsh") or shutil.which("powershell")
  if not x: raise ValueError("PowerShell is not installed")
  return x
 x=shutil.which("bash")
 if not x: raise ValueError("bash is not installed")
 return x

def create_session(shell=None):
 shell=shell or ("powershell" if os.name=="nt" else "bash")
 _exe(shell)
 sid=uuid.uuid4().hex
 with _LOCK:_SESSIONS[sid]={"shell":shell,"cwd":str(storage_root()),"env":os.environ.copy()}
 return {"session_id":sid,"shell":shell,"cwd":str(storage_root())}

def close_session(sid):
 with _LOCK:return _SESSIONS.pop(sid,None) is not None

def _state(sid,shell=None):
 if not sid:return None
 with _LOCK:return _SESSIONS.get(sid)

def execute(command,timeout=60,shell=None,privileged=False,session_id=None):
 if not isinstance(command,str) or not command.strip() or len(command)>MAX_COMMAND: raise ValueError("Invalid command")
 st=_state(session_id)
 shell=(st or {}).get("shell") or shell or ("powershell" if os.name=="nt" else "bash")
 if privileged and os.name=="nt": raise PermissionError("Administrative PowerShell requires Cloud OS itself to be running elevated; UAC is never bypassed")
 exe=_exe(shell)
 cwd=(st or {}).get("cwd") if st else str(storage_root())
 env=(st or {}).get("env") if st else os.environ.copy()
 if privileged:
  if os.name=="nt": raise PermissionError("Administrative PowerShell requires Cloud OS itself to be running elevated; UAC is never bypassed")
  sudo=shutil.which("sudo")
  if not sudo: raise PermissionError("sudo is not installed")
  argv=[sudo,"-n","--",exe,"--noprofile","--norc","-c",command] if shell=="bash" else [sudo,"-n","--",exe,"-NoLogo","-NoProfile","-NonInteractive","-Command",command]
 else:
  if shell=="powershell":
   wrapped=f'& {{ {command} }}; $c=(Get-Location).Path; Write-Output "__CLOUDOS_CWD__$c"'
   argv=[exe,"-NoLogo","-NoProfile","-NonInteractive","-Command",wrapped]
  else:
   wrapped=command+'; rc=$?; printf "\
__CLOUDOS_CWD__%s" "$PWD"; exit $rc'
   argv=[exe,"--noprofile","--norc","-c",wrapped]
 proc=subprocess.run(argv,cwd=cwd,env=env,capture_output=True,text=True,timeout=timeout,shell=False)
 out=proc.stdout
 marker="__CLOUDOS_CWD__"
 if not privileged and marker in out:
  visible,newcwd=out.rsplit(marker,1)
  candidate=newcwd.strip()
  if candidate and Path(candidate).is_dir():
   cwd=str(Path(candidate).resolve())
   if st:
    with _LOCK:st["cwd"]=cwd
  out=visible.rstrip("\r
")+"
" if visible else ""
 return {"code":proc.returncode,"stdout":out[-MAX_OUTPUT:],"stderr":proc.stderr[-MAX_OUTPUT:],"shell":shell,"privileged":bool(privileged),"session_id":session_id,"cwd":cwd}
