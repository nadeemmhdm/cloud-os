from __future__ import annotations
import asyncio, os, shlex, threading
from pathlib import Path
import asyncssh
from .audit import record
from .auth import verify
from .config import APP_DIR, load
from .files import safe_path, storage_root
from .teams import authenticate, permissions

def _identity(username, password):
    cfg=load()
    if username=="admin":
        if not cfg.get("admin_password_hash") or not verify(password,cfg["admin_password_hash"]): return None
        return {"username":"admin","permissions":["*"]}
    u=authenticate(username,password)
    return {"username":username,"permissions":permissions(username)} if u else None

def _can(identity, perm):
    p=identity.get("permissions",[])
    return "*" in p or perm in p

class CloudOSSSHServer(asyncssh.SSHServer):
    def __init__(self): self.identity=None
    def connection_made(self, conn): self.conn=conn
    def begin_auth(self, username): return True
    def password_auth_supported(self): return True
    def validate_password(self, username, password):
        self.identity=_identity(username,password)
        if self.identity: record("ssh.login",username)
        return self.identity is not None

class CloudOSSFTPServer(asyncssh.SFTPServer):
    def __init__(self, chan):
        super().__init__(chan, chroot=str(storage_root()))

async def _shell(process):
    username=process.get_extra_info("username") or "unknown"
    ident=getattr(process.channel.get_connection().get_server(), "identity", None)
    if not ident:
        process.exit(1); return
    cwd=""
    process.stdout.write("Cloud OS SSH Workspace\nHost operating-system shell is not exposed.\nType 'help' for commands.\n\n")
    while not process.stdin.at_eof():
        process.stdout.write(f"cloud-os:{('/'+cwd) if cwd else '/'}$ ")
        line=await process.stdin.readline()
        if not line: break
        try: args=shlex.split(line.strip())
        except ValueError as e:
            process.stdout.write(f"error: {e}\n"); continue
        if not args: continue
        cmd,*rest=args
        try:
            if cmd in ("exit","quit"): break
            if cmd=="help":
                process.stdout.write("Commands: help, pwd, ls [path], cd [path], cat <file>, mkdir <dir>, touch <file>, rm <path>, mv <path> <name>, exit\nFile operations are restricted to this Cloud OS workspace.\n")
            elif cmd=="pwd": process.stdout.write("/"+cwd+"\n")
            elif cmd=="ls":
                p=safe_path(str(Path(cwd)/(rest[0] if rest else "")))
                if not p.is_dir(): raise ValueError("not a directory")
                process.stdout.write("\n".join(x.name+("/" if x.is_dir() else "") for x in sorted(p.iterdir()))+"\n")
            elif cmd=="cd":
                target=str(Path(cwd)/(rest[0] if rest else ""))
                p=safe_path(target)
                if not p.is_dir(): raise ValueError("not a directory")
                cwd="" if p==storage_root() else str(p.relative_to(storage_root())).replace("\\","/")
            elif cmd=="cat":
                if not _can(ident,"files.read"): raise PermissionError("files.read required")
                if not rest: raise ValueError("usage: cat <file>")
                p=safe_path(str(Path(cwd)/rest[0]))
                if not p.is_file(): raise ValueError("not a file")
                if p.stat().st_size>2*1024*1024: raise ValueError("file too large for terminal cat")
                process.stdout.write(p.read_text(encoding="utf-8")+"\n")
            elif cmd in ("mkdir","touch","rm","mv"):
                if not _can(ident,"files.write"): raise PermissionError("files.write required")
                if not rest: raise ValueError(f"usage: {cmd} <path>")
                p=safe_path(str(Path(cwd)/rest[0]))
                if cmd=="mkdir": p.mkdir(parents=False,exist_ok=False)
                elif cmd=="touch": p.touch(exist_ok=True)
                elif cmd=="rm":
                    if p==storage_root(): raise ValueError("cannot remove storage root")
                    if p.is_dir(): p.rmdir()
                    else: p.unlink()
                else:
                    if len(rest)!=2: raise ValueError("usage: mv <path> <new-name>")
                    name=rest[1]
                    if not name or name in (".","..") or "/" in name or "\\" in name: raise ValueError("invalid new name")
                    p.rename(p.with_name(name))
                record("ssh.file."+cmd,f"{username}:{rest[0]}")
            else:
                process.stdout.write("Command not available in Cloud OS workspace. Type 'help'.\n")
        except (OSError,ValueError,PermissionError,UnicodeError) as e:
            process.stdout.write(f"error: {e}\n")
    process.exit(0)

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
    host=str(cfg.get("ssh_host","0.0.0.0"))
    port=int(cfg.get("ssh_port",2222))
    await asyncssh.create_server(CloudOSSSHServer,host,port,server_host_keys=[_host_key()],process_factory=_shell)
    await asyncio.Future()

def start_background():
    cfg=load()
    if not cfg.get("ssh_enabled",False): return None
    def runner():
        try: asyncio.run(serve())
        except Exception as exc: record("ssh.gateway.error",str(exc))
    t=threading.Thread(target=runner,name="cloud-os-ssh",daemon=True); t.start(); return t
