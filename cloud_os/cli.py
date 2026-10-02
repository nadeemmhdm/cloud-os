from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
import time
from importlib.metadata import PackageNotFoundError, version as package_version
from pathlib import Path

import typer
import uvicorn

from .config import load, save
from .doctor import report
from .runtime import prepare_integrations
from .auth import ensure_admin

app = typer.Typer(no_args_is_help=True, help="Cloud OS management CLI")
REPO = "nadeemmhdm/cloud-os"
REPO_DIR = Path(os.getenv("CLOUD_OS_SOURCE", "/opt/cloud-os" if os.name != "nt" else str(Path(os.getenv("ProgramData", "C:/ProgramData")) / "CloudOs")))


def _ok(message: str) -> None:
    typer.secho(f"[OK] {message}", fg=typer.colors.GREEN)


def _warn(message: str) -> None:
    typer.secho(f"[WARN] {message}", fg=typer.colors.YELLOW)


def _fail(code: str, message: str, fix: str | None = None) -> None:
    typer.secho(f"[ERROR {code}] {message}", fg=typer.colors.RED, err=True)
    if fix:
        typer.echo(f"Fix: {fix}", err=True)
    raise typer.Exit(1)


def _run(command: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
    except FileNotFoundError:
        _fail("C001", f"Required command was not found: {command[0]}", "Run 'cloud-os doctor' and install the missing requirement.")
    if check and result.returncode != 0:
        detail = (result.stderr or result.stdout or "command failed").strip()
        _fail("C002", detail[:1000])
    return result


def _local_version() -> str:
    try:
        return package_version("cloud-os")
    except PackageNotFoundError:
        return "unknown"


def _step(message: str) -> None:
    frames="|/-\\"
    if not sys.stdout.isatty():
        typer.echo(f"[....] {message}"); return
    for i in range(6):
        typer.echo(f"\r[{frames[i%4]}] {message}",nl=False); time.sleep(0.05)
    typer.echo(f"\r[OK] {message}")

def _done(message: str) -> None:
    typer.secho(f"[DONE] {message}",fg=typer.colors.GREEN)

def _latest_release() -> dict:
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/releases/latest",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "cloud-os"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            _fail("U404", "No GitHub Release is published yet.", "Publish a tagged Cloud OS release, or use 'cloud-os update --source main'.")
        _fail("UHTTP", f"GitHub update check failed with HTTP {exc.code}.", "Check Internet access and try again.")
    except (urllib.error.URLError, TimeoutError) as exc:
        _fail("UNET", f"Could not reach GitHub: {exc}", "Check Internet/DNS/proxy settings and retry.")


@app.command()
def setup(port: int = 8765, ssh: bool = True):
    cfg = load()
    cfg["port"] = port
    cfg["ssh_enabled"] = ssh
    save(cfg)
    if not cfg.get("admin_password_hash"):
        typer.echo("Create the Cloud OS owner password (minimum 12 characters).")
        password = typer.prompt("Owner password", hide_input=True, confirmation_prompt=True)
        try:
            ensure_admin(password)
        except ValueError as exc:
            _fail("S001", str(exc), "Run 'cloud-os setup' again and choose a stronger password.")
    _ok("Cloud OS configuration saved.")


@app.command()
def start():
    cfg = load()
    prepare_integrations()
    typer.echo(f"Starting Cloud OS on http://{cfg['host']}:{cfg['port']}")
    uvicorn.run("cloud_os.server:app", host=cfg["host"], port=int(cfg["port"]))


@app.command()
def status():
    cfg = load()
    typer.echo(f"Cloud OS {_local_version()} configured on {cfg['host']}:{cfg['port']}")


@app.command("version")
def show_version():
    typer.echo(_local_version())


@app.command()
def doctor():
    typer.echo(f"Cloud OS {_local_version()} diagnostics")
    typer.echo(f"Python: {platform.python_version()} ({sys.executable})")
    typer.echo(f"Git: {'found' if shutil.which('git') else 'missing'}")
    r = report()
    for c in r["checks"]:
        label = "PASS" if c["ok"] else "WARN"
        typer.echo(f"[{label}] {c['name']}: {c['detail']}")
    typer.echo("System Health: " + ("HEALTHY" if r["healthy"] else "NEEDS ATTENTION"))


@app.command("install-service")
def install_service():
    _fail(
        "SVC00",
        "Automatic system service installation is disabled in this development build.",
        "Use 'cloud-os start'. A dedicated unprivileged service account will be required before service mode is enabled.",
    )


@app.command("update-check")
def update_check():
    release = _latest_release()
    latest = str(release.get("tag_name", "")).lstrip("v")
    current = _local_version()
    typer.echo(f"Installed: {current}")
    typer.echo(f"Latest release: {latest or 'unknown'}")
    if latest and current == latest:
        _ok("Cloud OS is up to date.")
    else:
        _warn("A different release is available.")
        typer.echo("Run: cloud-os update")


@app.command()
def update(source: str = typer.Option("release", help="release or main")):
    if not shutil.which("git"): _fail("U001","Git is required for updates.","Re-run the installer to repair Git.")
    if not (REPO_DIR/".git").exists(): _fail("U002",f"Cloud OS source checkout was not found at {REPO_DIR}.","Re-run the installer.")
    if _run(["git","-C",str(REPO_DIR),"status","--porcelain"]).stdout.strip():
        _fail("U005","Update stopped because the source checkout has local changes.","Commit or stash them first; Cloud OS will not destroy local work.")
    old=_run(["git","-C",str(REPO_DIR),"rev-parse","HEAD"]).stdout.strip()
    old_ref=_run(["git","-C",str(REPO_DIR),"symbolic-ref","--quiet","--short","HEAD"],check=False).stdout.strip()
    current=_local_version(); _step("Checking for updates")
    if source=="release":
        rel=_latest_release(); target=str(rel.get("tag_name","")).strip()
        if not target: _fail("U003","Latest release has no tag.")
        label=target.lstrip("v")
    elif source=="main": target="origin/main"; label="main"
    else: _fail("U004","Unknown update source.","Use --source release or --source main.")
    _done(f"Update target resolved: {label}")
    try:
        _step("Fetching update resources"); _run(["git","-C",str(REPO_DIR),"fetch","--tags","origin"]); _done("Repository resources fetched")
        _step("Downloading and preparing update"); _run(["git","-C",str(REPO_DIR),"checkout","--detach",target]); _done("Update source prepared")
        _step("Installing Cloud OS update"); _run([sys.executable,"-m","pip","install","--upgrade",str(REPO_DIR)]); _done("Package installation completed")
        _step("Verifying installed update"); _run([sys.executable,"-c","import cloud_os; print(cloud_os.__version__)"])
    except typer.Exit:
        typer.secho("[ROLLBACK] Update failed; restoring previous revision.",fg=typer.colors.YELLOW)
        _run(["git","-C",str(REPO_DIR),"checkout","--detach",old],check=False)
        if old_ref: _run(["git","-C",str(REPO_DIR),"checkout",old_ref],check=False)
        _run([sys.executable,"-m","pip","install","--upgrade",str(REPO_DIR)],check=False)
        raise
    new=_run(["git","-C",str(REPO_DIR),"rev-parse","HEAD"]).stdout.strip()
    installed=_run([sys.executable,"-c","import cloud_os; print(cloud_os.__version__)"],check=False).stdout.strip() or "unknown"
    typer.secho("\n[SUCCESS] Cloud OS updated successfully.",fg=typer.colors.GREEN,bold=True)
    typer.echo(f"Version: {current} -> {installed}"); typer.echo(f"Revision: {old[:12]} -> {new[:12]}"); typer.echo(f"Channel: {source}"); typer.echo("Next: cloud-os doctor")

@app.command()
def uninstall(
    yes: bool = typer.Option(False,"--yes","-y",help="Skip confirmation"),
    purge_data: bool = typer.Option(False,"--purge-data",help="Also remove Cloud OS configuration, backups and configured storage"),
):
    """Uninstall Cloud OS; preserve user data unless purge is explicitly requested."""
    if not yes:
        typer.secho("Cloud OS program files will be removed. Data is preserved by default.",fg=typer.colors.YELLOW)
        if not typer.confirm("Continue?"): raise typer.Abort()
    _step("Removing automatic startup")
    if os.name=="nt": _run(["schtasks","/Delete","/TN","CloudOs","/F"],check=False)
    else: _run(["systemctl","--user","disable","--now","cloud-os.service"],check=False)
    _done("Automatic startup removed")
    cfg=load(); data_dir=Path(os.getenv("CLOUD_OS_HOME",Path.home()/".cloud-os")); storage=Path(str(cfg.get("storage_root",Path.home()/"CloudOsStorage"))).expanduser()
    _step("Removing installed package")
    _run([sys.executable,"-m","pip","uninstall","-y","cloud-os"],check=False); _done("Installed package removed")
    if purge_data:
        if data_dir.exists(): shutil.rmtree(data_dir,ignore_errors=True)
        if storage.exists() and storage.is_dir(): shutil.rmtree(storage,ignore_errors=True)
        _done("Configuration, backups and configured storage removed")
    else:
        typer.echo(f"Preserved state/backups: {data_dir}"); typer.echo(f"Preserved storage: {storage}")
    typer.secho("[SUCCESS] Cloud OS uninstall completed.",fg=typer.colors.GREEN)


if __name__ == "__main__":
    app()
