from __future__ import annotations
import asyncio, os, shutil, threading
import asyncssh
from .audit import record
from .auth import verify,login_allowed,note_login_failure,clear_login_failures
from .config import APP_DIR, load
from .files import storage_root
from .teams import authenticate, permissions

def _identity(username,password):
    cfg=load()
    if username=="admin":
        return {"username":"admin","role":"owner","permissions":["*"]} if cfg.get("admin_password_hash") and verify(password,cfg["admin_password_hash"]) else None
    u=authenticate(username,password)
    return {"username":username,"role":u.get("role","member"),"permissions":permissions(username)} if u else None

def _can_terminal(identity):
    p=identity.get("permissions",[])
    return "*" in p or "terminal" in p

def _is_admin(identity):
    return bool(identity and (identity.get("role") in ("owner","admin") or "*" in identity.get("permissions",[])))

class CloudOSSSHServer(asyncssh.SSHServer):
    def __init__(self): self.identity=None
    def begin_auth(self,username): return True
    def password_auth_supported(self): return True
    def validate_password(self,username,password):
        key=f"ssh-account:{str(username).lower()}"
        if not login_allowed(key):
            record("ssh.login.throttled",username)
            return False
        self.identity=_identity(username,password)
        ok=bool(self.identity and _can_terminal(self.identity))
        if ok:
            clear_login_failures(key)
        else:
            note_login_failure(key)
        record("ssh.login" if ok else "ssh.login.denied",username)
        return ok

def _shell_argv():
    if os.name=="nt":
        exe=shutil.which("pwsh") or shutil.which("powershell")
        if not exe: raise RuntimeError("PowerShell is not installed")
        return [exe,"-NoLogo"]
    exe=shutil.which("bash")
    if not exe: raise RuntimeError("Bash is not installed")
    return [exe,"--noprofile","--norc","-i"]

async def _process(process):
    username=process.get_extra_info("username") or "unknown"
    record("ssh.shell.open",username)
    try:
        proc=await asyncio.create_subprocess_exec(*_shell_argv(),cwd=str(storage_root()),stdin=asyncio.subprocess.PIPE,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
        async def client_to_shell():
            while True:
                data=await process.stdin.read(4096)
                if not data: break
                proc.stdin.write(data.encode() if isinstance(data,str) else data)
                await proc.stdin.drain()
            if proc.stdin: proc.stdin.close()
        async def shell_to_client(stream,target):
            while True:
                data=await stream.read(4096)
                if not data: break
                target.write(data.decode(errors="replace"))
        await asyncio.gather(client_to_shell(),shell_to_client(proc.stdout,process.stdout),shell_to_client(proc.stderr,process.stderr))
        code=await proc.wait()
        process.exit(code)
    finally:
        record("ssh.shell.close",username)

def _host_key():
    APP_DIR.mkdir(parents=True,exist_ok=True)
    path=APP_DIR/"ssh_host_key"
    if not path.exists():
        key=asyncssh.generate_private_key("ssh-ed25519")
        path.write_text(key.export_private_key().decode(),encoding="utf-8")
        if os.name!="nt": path.chmod(0o600)
    return str(path)

async def serve():
    cfg=load()
    if not cfg.get("ssh_enabled",False): return
    await asyncssh.create_server(CloudOSSSHServer,str(cfg.get("ssh_host","0.0.0.0")),int(cfg.get("ssh_port",2222)),server_host_keys=[_host_key()],process_factory=_process)
    await asyncio.Future()

def start_background():
    if not load().get("ssh_enabled",False): return None
    def runner():
        try: asyncio.run(serve())
        except Exception as exc: record("ssh.gateway.error",str(exc))
    t=threading.Thread(target=runner,name="cloud-os-ssh",daemon=True); t.start(); return t
