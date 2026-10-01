from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from importlib.metadata import PackageNotFoundError, version as package_version
from pathlib import Path

import typer
import uvicorn

from .config import load, save
from .doctor import report
from .runtime import prepare_integrations

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
    if os.name == "nt":
        _warn("Windows service installation is not implemented yet.")
        typer.echo("Cloud OS itself is installed. Use 'cloud-os start' until the Windows service backend is added.")
        return

    if not shutil.which("systemctl"):
        _fail("SVC01", "systemd/systemctl is not available on this Linux system.", "Use 'cloud-os start' or install a supported service manager.")

    source = REPO_DIR / "packaging" / "cloud-os.service"
    if not source.exists():
        _fail("SVC02", f"Service template not found: {source}", "Re-run the Cloud OS installer to repair the installation.")

    target = Path("/etc/systemd/system/cloud-os.service")
    try:
        shutil.copyfile(source, target)
    except PermissionError:
        _fail("SVC03", "Administrator/root permission is required to install the service.", "Run: sudo cloud-os install-service")
    _run(["systemctl", "daemon-reload"])
    _run(["systemctl", "enable", "--now", "cloud-os"])
    _ok("Cloud OS systemd service installed and started.")


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
    if not shutil.which("git"):
        _fail("U001", "Git is required for the current updater.", "Re-run the one-command installer; it can install Git automatically.")

    if not (REPO_DIR / ".git").exists():
        _fail("U002", f"Cloud OS source checkout was not found at {REPO_DIR}.", "Re-run the one-command installer to repair the installation.")

    old = _run(["git", "-C", str(REPO_DIR), "rev-parse", "HEAD"]).stdout.strip()
    typer.echo(f"Current revision: {old[:12]}")

    if source == "release":
        release = _latest_release()
        tag = str(release.get("tag_name", "")).strip()
        if not tag:
            _fail("U003", "Latest release has no tag.")
        _run(["git", "-C", str(REPO_DIR), "fetch", "--tags", "origin"])
        _run(["git", "-C", str(REPO_DIR), "checkout", "--detach", tag])
    elif source == "main":
        _run(["git", "-C", str(REPO_DIR), "fetch", "origin", "main"])
        _run(["git", "-C", str(REPO_DIR), "checkout", "main"])
        _run(["git", "-C", str(REPO_DIR), "reset", "--hard", "origin/main"])
    else:
        _fail("U004", "Unknown update source.", "Use --source release or --source main.")

    try:
        _run([sys.executable, "-m", "pip", "install", "--upgrade", str(REPO_DIR)])
    except typer.Exit:
        typer.secho("[ROLLBACK] Update install failed; restoring previous revision.", fg=typer.colors.YELLOW)
        _run(["git", "-C", str(REPO_DIR), "checkout", "--detach", old], check=False)
        _run([sys.executable, "-m", "pip", "install", "--upgrade", str(REPO_DIR)], check=False)
        raise

    new = _run(["git", "-C", str(REPO_DIR), "rev-parse", "HEAD"]).stdout.strip()
    if new == old:
        _ok("Cloud OS is already up to date.")
    else:
        _ok(f"Cloud OS updated: {old[:12]} -> {new[:12]}")
        typer.echo("Run: cloud-os doctor")


if __name__ == "__main__":
    app()
