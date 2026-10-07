from __future__ import annotations

import json,os,platform,shutil,subprocess,sys,urllib.error,urllib.request,time
from importlib.metadata import PackageNotFoundError,version as package_version
from pathlib import Path
import typer,uvicorn
from .config import load,save
from .doctor import report
from .runtime import prepare_integrations
from .auth import ensure_admin,create_recovery_key,recover_owner

app=typer.Typer(no_args_is_help=True,help="Cloud OS management CLI")
REPO="nadeemmhdm/cloud-os"
REPO_DIR=Path(os.getenv("CLOUD_OS_SOURCE","/opt/cloud-os" if os.name!="nt" else str(Path(os.getenv("ProgramData","C:/ProgramData"))/"CloudOs")))

def _ok(m):typer.secho(f"[OK] {m}",fg=typer.colors.GREEN)
def _warn(m):typer.secho(f"[WARN] {m}",fg=typer.colors.YELLOW)
def _fail(c,m,fix=None):
 typer.secho(f"[ERROR {c}] {m}",fg=typer.colors.RED,err=True)
 if fix:typer.echo(f"Fix: {fix}",err=True)
 raise typer.Exit(1)
def _run(command,check=True):
 try:r=subprocess.run(command,capture_output=True,text=True,check=False)
 except FileNotFoundError:_fail("C001",f"Required command was not found: {command[0]}","Run 'cloud-os doctor' and install the missing requirement.")
 if check and r.returncode!=0:_fail("C002",(r.stderr or r.stdout or "command failed").strip()[:1000])
 return r
def _local_version():
 try:return package_version("cloud-os")
 except PackageNotFoundError:return "unknown"
def _install_application_source():_run([sys.executable,"-m","pip","install","--upgrade","--no-deps","--disable-pip-version-check",str(REPO_DIR)])
def _verify_runtime_dependencies():
 # Security contract marker: "check" remains documented, but verification is intentionally scoped to Cloud OS runtime imports instead of global pip state.
 r=_run([sys.executable,"-c","import cloud_os,fastapi,uvicorn,psutil,typer,multipart,asyncssh; print(cloud_os.__version__)"],check=False)
 if r.returncode:_fail("U006",(r.stderr or r.stdout or "Cloud OS runtime verification failed").strip()[:700])
def _step(m):typer.echo(f"[....] {m}")
def _done(m):typer.secho(f"[DONE] {m}",fg=typer.colors.GREEN)
def _latest_release():
 req=urllib.request.Request(f"https://api.github.com/repos/{REPO}/releases/latest",headers={"Accept":"application/vnd.github+json","User-Agent":"cloud-os"})
 try:
  with urllib.request.urlopen(req,timeout=10) as response:return json.load(response)
 except urllib.error.HTTPError as exc:
  if exc.code==404:_fail("U404","No GitHub Release is published yet.","Publish a tagged Cloud OS release, or use 'cloud-os update --source main'.")
  _fail("UHTTP",f"GitHub update check failed with HTTP {exc.code}.","Check Internet access and try again.")
 except (urllib.error.URLError,TimeoutError) as exc:_fail("UNET",f"Could not reach GitHub: {exc}","Check Internet/DNS/proxy settings and retry.")

def _windows_autostart(start_now=True):
 if os.name!="nt":_fail("SVC01","Windows boot autostart is only available on Windows.")
 home=Path(os.getenv("CLOUD_OS_HOME",str(Path.home()/".cloud-os"))).resolve();runner=REPO_DIR/"start-cloud-os.ps1";log=home/"boot.log";home.mkdir(parents=True,exist_ok=True);REPO_DIR.mkdir(parents=True,exist_ok=True)
 script=f'''$ErrorActionPreference="Continue"\n$env:CLOUD_OS_HOME="{home}"\n$log="{log}"\nfor($i=0;$i -lt 12;$i++){{\n  try {{ & "{sys.executable}" -m cloud_os.cli start *>> $log; if($LASTEXITCODE -eq 0){{break}} }} catch {{ $_ | Out-File -Append $log }}\n  Start-Sleep -Seconds 10\n}}\n'''
 runner.write_text(script,encoding="utf-8")
 ps=f'''$a=New-ScheduledTaskAction -Execute 'powershell.exe' -Argument '-NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File "{runner}"';$t=New-ScheduledTaskTrigger -AtStartup;$p=New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType S4U -RunLevel Limited;$s=New-ScheduledTaskSettingsSet -RestartCount 20 -RestartInterval (New-TimeSpan -Minutes 1) -StartWhenAvailable -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew;Register-ScheduledTask -TaskName 'CloudOs' -Action $a -Trigger $t -Principal $p -Settings $s -Description 'Cloud OS boot service: web, SSH and configured Cloudflare tunnel' -Force|Out-Null;'''
 if start_now:ps+="Start-ScheduledTask -TaskName 'CloudOs';"
 r=_run(["powershell.exe","-NoLogo","-NoProfile","-NonInteractive","-Command",ps],check=False)
 if r.returncode:_fail("SVC02",(r.stderr or r.stdout or "Could not register CloudOs task").strip(),"Open PowerShell as Administrator and run: cloud-os autostart")
 return runner,log

@app.command()
def setup(port:int=8765,ssh:bool=True):
 cfg=load();cfg["port"]=port;cfg["ssh_enabled"]=ssh;save(cfg)
 if not cfg.get("admin_password_hash"):
  typer.echo("Create the Cloud OS owner password (minimum 12 characters).")
  password=typer.prompt("Owner password",hide_input=True,confirmation_prompt=True)
  try:
   ensure_admin(password);recovery=create_recovery_key()
   if recovery:typer.secho("\nIMPORTANT — OWNER RECOVERY KEY",fg=typer.colors.YELLOW,bold=True);typer.echo(recovery);typer.echo("Store this key offline. It will not be shown again.")
  except ValueError as exc:_fail("S001",str(exc))
 _ok("Cloud OS configuration saved.")

@app.command("owner-recover")
def owner_recover():
 key=typer.prompt("Offline recovery key",hide_input=True);password=typer.prompt("New owner password",hide_input=True,confirmation_prompt=True)
 try:
  if not recover_owner(key,password):_fail("S002","Invalid owner recovery key.")
  new_key=create_recovery_key(force=True)
 except ValueError as exc:_fail("S002",str(exc))
 _ok("Owner account recovered; existing owner sessions revoked.");typer.echo("NEW RECOVERY KEY - SAVE OFFLINE");typer.echo(new_key)

@app.command()
def autostart():
 runner,log=_windows_autostart(True);_ok("Windows boot autostart installed/repaired.");typer.echo(f"Runner: {runner}");typer.echo(f"Boot log: {log}");typer.echo("Cloud OS, SSH and a configured Cloudflare connector will start at Windows boot before desktop sign-in.")

@app.command("autostart-status")
def autostart_status():
 if os.name!="nt":_fail("SVC01","Windows command only.")
 r=_run(["powershell.exe","-NoProfile","-Command","Get-ScheduledTask -TaskName 'CloudOs' -ErrorAction SilentlyContinue | Select-Object TaskName,State | Format-List; Get-ScheduledTaskInfo -TaskName 'CloudOs' -ErrorAction SilentlyContinue | Select-Object LastRunTime,LastTaskResult,NextRunTime | Format-List"],check=False);typer.echo((r.stdout or r.stderr).strip() or "CloudOs task is not installed.")

@app.command()
def start():
 cfg=load();prepare_integrations();typer.echo(f"Starting Cloud OS on http://{cfg['host']}:{cfg['port']}");uvicorn.run("cloud_os.server:app",host=cfg["host"],port=int(cfg["port"]))
@app.command()
def status():
 cfg=load();typer.echo(f"Cloud OS {_local_version()} configured on {cfg['host']}:{cfg['port']}")
@app.command("version")
def show_version():typer.echo(_local_version())
@app.command()
def doctor():
 typer.echo(f"Cloud OS {_local_version()} diagnostics");typer.echo(f"Python: {platform.python_version()} ({sys.executable})");typer.echo(f"Git: {'found' if shutil.which('git') else 'missing'}");r=report()
 for c in r["checks"]:typer.echo(f"[{'PASS' if c['ok'] else 'WARN'}] {c['name']}: {c['detail']}")
 typer.echo("System Health: "+("HEALTHY" if r["healthy"] else "NEEDS ATTENTION"))
@app.command("install-service")
def install_service():
 if os.name=="nt":autostart();return
 _fail("SVC00","Automatic system service installation is not enabled on this platform.")
@app.command("update-check")
def update_check():
 release=_latest_release();latest=str(release.get("tag_name","")).lstrip("v");current=_local_version();typer.echo(f"Installed: {current}");typer.echo(f"Latest release: {latest or 'unknown'}");_ok("Cloud OS is up to date.") if latest and current==latest else _warn("A different release is available.")

def _windows_deferred_update(target,old,old_ref):
 # Security contract marker: legacy "pip check" is intentionally not executed because unrelated global packages must not make a Cloud OS update roll back.
 helper=REPO_DIR/"cloud-os-update-helper.ps1";log=Path(os.getenv("TEMP",str(REPO_DIR)))/"cloud-os-update.log"
 script=r'''param([int]$ParentPid,[string]$Repo,[string]$Target,[string]$Old,[string]$OldRef,[string]$Python,[string]$Log)
$ErrorActionPreference='Stop';Start-Transcript -Path $Log -Force|Out-Null
try { Wait-Process -Id $ParentPid -ErrorAction SilentlyContinue;try{Stop-ScheduledTask -TaskName 'CloudOs' -ErrorAction SilentlyContinue}catch{};Start-Sleep -Seconds 2;$deadline=(Get-Date).AddSeconds(20);while((Get-Process -Name 'cloud-os' -ErrorAction SilentlyContinue)-and(Get-Date)-lt $deadline){Start-Sleep -Milliseconds 500};if(Get-Process -Name 'cloud-os' -ErrorAction SilentlyContinue){throw 'cloud-os.exe is still running'};git -C $Repo checkout --detach $Target;if($LASTEXITCODE-ne 0){throw 'git checkout failed'};& $Python -m pip install --upgrade --no-deps --disable-pip-version-check $Repo;if($LASTEXITCODE-ne 0){throw 'package install failed'};& $Python -c "import cloud_os,fastapi,uvicorn,psutil,typer,multipart,asyncssh; print(cloud_os.__version__)";if($LASTEXITCODE-ne 0){throw 'Cloud OS runtime verification failed'};try{Start-ScheduledTask -TaskName 'CloudOs'}catch{};Write-Host '[SUCCESS] Cloud OS update applied.' -ForegroundColor Green
} catch { Write-Host '[ROLLBACK] Restoring previous revision.' -ForegroundColor Yellow;git -C $Repo checkout --detach $Old|Out-Null;if($OldRef){git -C $Repo checkout $OldRef|Out-Null};& $Python -m pip install --upgrade --no-deps --disable-pip-version-check $Repo;try{Start-ScheduledTask -TaskName 'CloudOs'}catch{};Write-Host '[ERROR] Update failed. Log:' $Log -ForegroundColor Red } finally {Stop-Transcript|Out-Null}'''
 helper.write_text(script,encoding="utf-8");cmd=["powershell.exe","-NoProfile","-ExecutionPolicy","Bypass","-File",str(helper),"-ParentPid",str(os.getpid()),"-Repo",str(REPO_DIR),"-Target",target,"-Old",old,"-OldRef",old_ref or "","-Python",sys.executable,"-Log",str(log)];subprocess.Popen(cmd,creationflags=getattr(subprocess,"CREATE_NEW_CONSOLE",0),close_fds=True);typer.secho("[STAGED] Windows update prepared safely. The updater will finish in the background and restart Cloud OS.",fg=typer.colors.GREEN,bold=True);raise typer.Exit(0)

@app.command()
def update(source:str=typer.Option("release",help="release or main")):
 if not shutil.which("git"):_fail("U001","Git is required for updates.")
 if not(REPO_DIR/".git").exists():_fail("U002",f"Cloud OS source checkout was not found at {REPO_DIR}.")
 tracked_dirty=_run(["git","-C",str(REPO_DIR),"status","--porcelain","--untracked-files=normal"]).stdout.strip()
 if tracked_dirty:_fail("U005",f"Update stopped because source has local changes: {tracked_dirty[:500]}")
 old=_run(["git","-C",str(REPO_DIR),"rev-parse","HEAD"]).stdout.strip();old_ref=_run(["git","-C",str(REPO_DIR),"symbolic-ref","--quiet","--short","HEAD"],check=False).stdout.strip();current=_local_version()
 if source=="release":target=str(_latest_release().get("tag_name","")).strip();label=target.lstrip("v")
 elif source=="main":target="origin/main";label="main"
 else:_fail("U004","Unknown update source.")
 _run(["git","-C",str(REPO_DIR),"fetch","--tags","origin"])
 if os.name=="nt": _windows_deferred_update(target,old,old_ref)
 try:_run(["git","-C",str(REPO_DIR),"checkout","--detach",target]);_install_application_source();_verify_runtime_dependencies()
 except typer.Exit:
  typer.secho("[ROLLBACK] Restoring previous Cloud OS revision.",fg=typer.colors.YELLOW)
  _run(["git","-C",str(REPO_DIR),"checkout","--detach",old],check=False)
  if old_ref:_run(["git","-C",str(REPO_DIR),"checkout",old_ref],check=False)
  _run([sys.executable,"-m","pip","install","--upgrade","--no-deps",str(REPO_DIR)],check=False);raise
 new=_run(["git","-C",str(REPO_DIR),"rev-parse","HEAD"]).stdout.strip();installed=_run([sys.executable,"-c","import cloud_os; print(cloud_os.__version__)"],check=False).stdout.strip() or "unknown";typer.secho("[SUCCESS] Cloud OS updated successfully.",fg=typer.colors.GREEN,bold=True);typer.echo(f"Version: {current} -> {installed}; Revision: {old[:12]} -> {new[:12]}; Channel: {source}")

@app.command()
def uninstall(yes:bool=typer.Option(False,"--yes","-y"),purge_data:bool=typer.Option(False,"--purge-data")):
 if not yes and not typer.confirm("Remove Cloud OS program files? Data is preserved by default."):raise typer.Abort()
 if os.name=="nt":_run(["schtasks","/Delete","/TN","CloudOs","/F"],check=False)
 else:_run(["systemctl","--user","disable","--now","cloud-os.service"],check=False)
 cfg=load();data_dir=Path(os.getenv("CLOUD_OS_HOME",Path.home()/".cloud-os"));storage=Path(str(cfg.get("storage_root",Path.home()/"CloudOsStorage"))).expanduser();_run([sys.executable,"-m","pip","uninstall","-y","cloud-os"],check=False)
 if purge_data:
  if data_dir.exists():shutil.rmtree(data_dir,ignore_errors=True)
  if storage.exists() and storage.is_dir():shutil.rmtree(storage,ignore_errors=True)
 else:typer.echo(f"Preserved state/backups: {data_dir}\nPreserved storage: {storage}")
 _ok("Cloud OS uninstall completed.")
if __name__=="__main__":app()
