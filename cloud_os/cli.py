from __future__ import annotations
import json, typer, uvicorn
from .config import load, save
from .runtime import prepare_integrations
from .doctor import report\nfrom .auth import ensure_admin
app=typer.Typer(no_args_is_help=True)
@app.command()
def setup(port:int=8765,ssh:bool=True):
 cfg=load(); cfg["port"]=port; cfg["ssh_enabled"]=ssh; save(cfg); typer.echo("Cloud Os configuration saved.")
@app.command()
def start():
 cfg=load(); prepare_integrations(); uvicorn.run("cloud_os.server:app",host=cfg["host"],port=int(cfg["port"]))
@app.command()
def status():
 cfg=load(); typer.echo(f"Cloud Os configured on {cfg['host']}:{cfg['port']}")
@app.command()
def doctor():
 r=report()
 for c in r["checks"]: typer.echo(f"[{'PASS' if c['ok'] else 'WARN'}] {c['name']}: {c['detail']}")
 typer.echo("System Health: "+("HEALTHY" if r["healthy"] else "NEEDS ATTENTION"))
if __name__=="__main__": app()
