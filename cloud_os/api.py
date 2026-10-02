from __future__ import annotations
import shutil,subprocess
from fastapi import APIRouter,HTTPException,Request,Response,UploadFile,File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from .auth import login,logout,allowed,identity,login_allowed,note_login_failure,clear_login_failures,verify,hash_password,revoke_user,change_admin_password
from .files import safe_path,safe_upload_path,list_items
from .terminal import execute,available_shells,create_session,close_session
from .backup import create_backup,list_backups,delete_backup,backup_info,restore_backup
from .doctor import report
from .integrations import status as integration_status
from .audit import record,recent
from .teams import create_user,users,create_team,teams,add_member,remove_member,set_password,set_disabled
from .config import load
from .errors import payload
from .ai import status as ai_status,configure as ai_configure,remove as ai_remove,chat_answer
from .booster import status as booster_status,boost as booster_enable,normal as booster_normal

router=APIRouter(prefix="/api")
SAFE_METHODS={"GET","HEAD","OPTIONS"}
MAX_UPLOAD=1024*1024*1024

class Login(BaseModel): password:str; username:str="admin"
class UserCreate(BaseModel): username:str; password:str; display_name:str=""; role:str="member"
class TeamCreate(BaseModel): name:str
class MemberChange(BaseModel): username:str; role:str="member"
class Command(BaseModel):
 command:str
 shell:str|None=None
 privileged:bool=False
 session_id:str|None=None

class TerminalSession(BaseModel):
 shell:str|None=None
class PathBody(BaseModel): path:str
class FileCreate(BaseModel): path:str; content:str=""
class RenameBody(BaseModel): path:str; new_name:str
class FileSave(BaseModel): path:str; content:str
class AIConfig(BaseModel): provider:str; api_key:str; model:str=""
class AIAsk(BaseModel): prompt:str
class BoostBody(BaseModel): enabled:bool=True
class PasswordChange(BaseModel): current_password:str; new_password:str
class AdminPasswordReset(BaseModel): new_password:str
class AccountState(BaseModel): disabled:bool

def token(req:Request): return req.cookies.get("cloudos_session","")

def fail(status:int,code:str,detail:str|None=None):
 raise HTTPException(status,detail=payload(code,detail))

def _same_origin(req:Request):
 if req.method in SAFE_METHODS: return
 origin=req.headers.get("origin")
 if not origin: return
 host=req.headers.get("host","")
 if origin not in (f"http://{host}",f"https://{host}"):
  fail(403,"PERM-001","Cross-origin state-changing request blocked")

def require(req:Request,permission:str|None=None):
 _same_origin(req)
 t=token(req); user=identity(t)
 if not user: fail(401,"AUTH-003")
 if permission and not allowed(t,permission): fail(403,"PERM-001")
 return user

@router.post("/login")
def do_login(body:Login,request:Request,response:Response):
 _same_origin(request)
 ip=request.client.host if request.client else "unknown"
 username=(body.username or "").strip()
 account_key=f"account:{username.lower()}"
 ip_key=f"ip:{ip}"
 if not login_allowed(account_key) or not login_allowed(ip_key):
  record("login.throttled",username); fail(429,"AUTH-002")
 t=login(body.password,username)
 if not t:
  note_login_failure(account_key); note_login_failure(ip_key)
  record("login.failed",username); fail(401,"AUTH-001")
 clear_login_failures(account_key); clear_login_failures(ip_key)
 cfg=load()
 response.set_cookie("cloudos_session",t,httponly=True,samesite="strict",secure=bool(cfg.get("secure_cookies")),max_age=43200,path="/")
 record("login",body.username)
 return {"ok":True,"user":identity(t)}

@router.post("/logout")
def do_logout(req:Request,response:Response):
 _same_origin(req)
 logout(token(req)); response.delete_cookie("cloudos_session",path="/"); return {"ok":True}

@router.get("/files")
def files(req:Request,path:str=""):
 require(req,"files.read")
 try:return list_items(path)
 except FileNotFoundError as e: fail(404,"FILE-001",str(e))
 except ValueError as e: fail(400,"FILE-002",str(e))

@router.post("/folder")
def folder(body:PathBody,req:Request):
 require(req,"files.write")
 try:safe_path(body.path).mkdir(parents=True,exist_ok=False)
 except FileExistsError as e: fail(409,"FILE-005",str(e))
 except ValueError as e: fail(400,"FILE-002",str(e))
 record("folder.create",body.path); return {"ok":True}


@router.post("/file")
def create_file(body:FileCreate,req:Request):
 require(req,"files.write")
 try:
  p=safe_path(body.path)
  if p.exists(): fail(409,"FILE-005","File already exists")
  p.parent.mkdir(parents=True,exist_ok=True)
  p.write_text(body.content,encoding="utf-8")
 except ValueError as e: fail(400,"FILE-002",str(e))
 except OSError as e: fail(500,"FILE-005",str(e))
 record("file.create",body.path); return {"ok":True}

@router.get("/file/content")
def file_content(path:str,req:Request):
 require(req,"files.read")
 try:p=safe_path(path)
 except ValueError as e: fail(400,"FILE-002",str(e))
 if not p.is_file(): fail(404,"FILE-001")
 try:
  if p.stat().st_size>2*1024*1024: fail(413,"FILE-003","Text editor limit is 2 MiB")
  return {"path":path,"content":p.read_text(encoding="utf-8")}
 except UnicodeDecodeError: fail(400,"FILE-005","This file is not UTF-8 text")
 except OSError as e: fail(500,"FILE-005",str(e))

@router.put("/file/content")
def save_file(body:FileSave,req:Request):
 require(req,"files.write")
 if len(body.content.encode("utf-8"))>2*1024*1024: fail(413,"FILE-003","Text editor limit is 2 MiB")
 try:
  p=safe_path(body.path)
  if not p.is_file(): fail(404,"FILE-001")
  p.write_text(body.content,encoding="utf-8")
 except ValueError as e: fail(400,"FILE-002",str(e))
 except OSError as e: fail(500,"FILE-005",str(e))
 record("file.edit",body.path); return {"ok":True}

@router.post("/files/rename")
def rename_file(body:RenameBody,req:Request):
 require(req,"files.write")
 if not body.new_name or body.new_name in (".","..") or "/" in body.new_name or "\\" in body.new_name or "\x00" in body.new_name:
  fail(400,"FILE-002","Invalid name")
 try:
  src=safe_path(body.path); root=safe_path("")
  if src==root: fail(400,"FILE-004")
  if not src.exists(): fail(404,"FILE-001")
  dst=safe_path(str(src.relative_to(root).parent/body.new_name))
  if dst.exists(): fail(409,"FILE-005","Destination already exists")
  src.rename(dst)
 except ValueError as e: fail(400,"FILE-002",str(e))
 except OSError as e: fail(500,"FILE-005",str(e))
 record("file.rename",body.path+" -> "+body.new_name); return {"ok":True}

@router.delete("/files")
def remove(path:str,req:Request):
 require(req,"files.write")
 try:p=safe_path(path); root=safe_path("")
 except ValueError as e: fail(400,"FILE-002",str(e))
 if p==root: fail(400,"FILE-004")
 if not p.exists(): fail(404,"FILE-001")
 shutil.rmtree(p) if p.is_dir() else p.unlink()
 record("file.delete",path); return {"ok":True}

@router.post("/upload")
async def upload(req:Request,path:str="",file:UploadFile=File(...)):
 require(req,"files.write")
 try:dest=safe_upload_path(path,file.filename or "upload.bin")
 except FileNotFoundError as e: fail(404,"FILE-001",str(e))
 except ValueError as e: fail(400,"FILE-002",str(e))
 total=0
 try:
  with dest.open("wb") as out:
   while True:
    chunk=await file.read(1024*1024)
    if not chunk: break
    total+=len(chunk)
    if total>MAX_UPLOAD:
     out.close(); dest.unlink(missing_ok=True); fail(413,"FILE-003")
    out.write(chunk)
 except HTTPException: raise
 except OSError as e: fail(500,"FILE-005",str(e))
 record("file.upload",dest.name); return {"ok":True,"size":total}

@router.get("/download")
def download(path:str,req:Request):
 require(req,"files.read")
 try:p=safe_path(path)
 except ValueError as e: fail(400,"FILE-002",str(e))
 if not p.is_file(): fail(404,"FILE-001")
 return FileResponse(p,filename=p.name)

@router.get("/terminal/shells")
def terminal_shells(req:Request):
 require(req,"terminal"); return {"shells":available_shells()}

@router.post("/terminal/session")
def terminal_session(body:TerminalSession,req:Request):
 user=require(req,"terminal")
 try:r=create_session(body.shell)
 except ValueError as e: fail(400,"TERM-001",str(e))
 record("terminal.session.open",f"{user['username']}:shell={r['shell']}")
 return r

@router.delete("/terminal/session/{session_id}")
def terminal_session_close(session_id:str,req:Request):
 user=require(req,"terminal")
 if not close_session(session_id): fail(404,"TERM-001","Terminal session was not found or already closed")
 record("terminal.session.close",user["username"])
 return {"ok":True}

@router.post("/terminal")
def terminal(body:Command,req:Request):
 user=require(req,"terminal")
 if body.privileged and user.get("role") not in ("owner","admin"): fail(403,"TERM-003")
 try:r=execute(body.command,shell=body.shell,privileged=body.privileged,session_id=body.session_id)
 except subprocess.TimeoutExpired: fail(408,"TERM-002")
 except PermissionError as e: fail(403,"TERM-003",str(e))
 except ValueError as e: fail(400,"TERM-001",str(e))
 record("terminal.command",f"{user[chr(117)+chr(115)+chr(101)+chr(114)+chr(110)+chr(97)+chr(109)+chr(101)]}:privileged={body.privileged}:shell={body.shell or chr(104)+chr(111)+chr(115)+chr(116)}:code={r.get(chr(99)+chr(111)+chr(100)+chr(101))}:command_length={len(body.command)}"); return r

@router.post("/backup")
def backup(req:Request):
 require(req,"backups")
 try: p=create_backup()
 except (OSError,shutil.Error) as e: fail(500,"BACKUP-001",str(e))
 record("backup.create",p); return {"path":p}

@router.get("/backups")
def backups(req:Request): require(req,"backups"); return list_backups()

@router.get("/backups/{name}")
def backup_details(name:str,req:Request):
 require(req,"backups")
 try:return backup_info(name)
 except FileNotFoundError as e: fail(404,"BACKUP-001",str(e))
 except (ValueError,OSError) as e: fail(400,"BACKUP-001",str(e))

@router.post("/backups/{name}/restore")
def backup_restore(name:str,req:Request):
 user=require(req,"backups")
 if user.get("role") not in ("owner","admin"): fail(403,"PERM-001")
 try:r=restore_backup(name)
 except FileNotFoundError as e: fail(404,"BACKUP-001",str(e))
 except (ValueError,OSError,shutil.Error) as e: fail(400,"BACKUP-001",str(e))
 record("backup.restore",f"{user['username']}:{name}:safety={r['safety_backup']}")
 return r

@router.delete("/backups/{name}")
def backup_delete(name:str,req:Request):
 user=require(req,"backups")
 try:deleted=delete_backup(name)
 except FileNotFoundError as e: fail(404,"BACKUP-001",str(e))
 except (ValueError,OSError,shutil.Error) as e: fail(400,"BACKUP-001",str(e))
 record("backup.delete",f"{user['username']}:{deleted}")
 return {"deleted":deleted}
@router.get("/doctor")
def doctor(req:Request): require(req,"settings"); return report()
@router.get("/integrations")
def integrations(req:Request): require(req,"network"); return integration_status()
@router.get("/audit")
def audit(req:Request): require(req,"audit"); return recent()
@router.get("/me")
def me(req:Request): return require(req)
@router.get("/users")
def list_users(req:Request):
 require(req,"teams.manage")
 cfg=load()
 return [{"username":"admin","id":"builtin-owner","display_name":"Administrator","role":"owner","disabled":False,"created_at":None,"first_login_at":cfg.get("admin_first_login_at"),"last_login_at":cfg.get("admin_last_login_at")}]+users()

@router.post("/users")
def new_user(body:UserCreate,req:Request):
 require(req,"teams.manage")
 try:u=create_user(body.username,body.password,body.display_name,body.role)
 except ValueError as e: fail(400,"USER-001",str(e))
 record("user.create",body.username); return u


@router.post("/account/password")
def own_password(body:PasswordChange,req:Request):
 user=require(req)
 try:
  if user["username"]=="admin":
   change_admin_password(body.current_password,body.new_password)
  else:
   from .teams import authenticate
   if not authenticate(user["username"],body.current_password): fail(403,"AUTH-001")
   set_password(user["username"],body.new_password); revoke_user(user["username"])
 except ValueError as e: fail(400,"USER-001",str(e))
 record("account.password.change",user["username"])
 return {"ok":True,"reauthenticate":True}

@router.post("/users/{username}/password")
def admin_password(username:str,body:AdminPasswordReset,req:Request):
 actor=require(req,"teams.manage")
 if username=="admin": fail(403,"PERM-001","Owner password can only be changed from the owner's own Settings page")
 try:set_password(username,body.new_password)
 except ValueError as e: fail(400,"USER-001",str(e))
 revoke_user(username); record("user.password.reset",f"{actor['username']}:{username}")
 return {"ok":True}

@router.post("/users/{username}/state")
def admin_state(username:str,body:AccountState,req:Request):
 actor=require(req,"teams.manage")
 if username=="admin": fail(403,"PERM-001","The built-in owner account cannot be blocked")
 try:set_disabled(username,body.disabled)
 except ValueError as e: fail(400,"USER-001",str(e))
 if body.disabled: revoke_user(username)
 record("user.state",f"{actor['username']}:{username}:disabled={body.disabled}")
 return {"ok":True}

@router.get("/teams")
def list_teams(req:Request): require(req,"teams.manage"); return teams()

@router.post("/teams")
def new_team(body:TeamCreate,req:Request):
 require(req,"teams.manage")
 try:t=create_team(body.name)
 except ValueError as e: fail(400,"TEAM-001",str(e))
 record("team.create",body.name); return t

@router.post("/teams/{team}/members")
def team_add(team:str,body:MemberChange,req:Request):
 require(req,"teams.manage")
 try:add_member(team,body.username,body.role)
 except ValueError as e: fail(400,"TEAM-001",str(e))
 record("team.member.add",team+":"+body.username); return {"ok":True}

@router.delete("/teams/{team}/members/{username}")
def team_remove(team:str,username:str,req:Request):
 require(req,"teams.manage")
 try:remove_member(team,username)
 except ValueError as e: fail(400,"TEAM-001",str(e))
 record("team.member.remove",team+":"+username); return {"ok":True}

@router.get("/ai/status")
def get_ai_status(req:Request):
 require(req,"settings"); return ai_status()

@router.post("/ai/configure")
def set_ai(body:AIConfig,req:Request):
 user=require(req,"settings")
 try:r=ai_configure(body.provider,body.api_key,body.model)
 except ValueError as e: fail(400,"AI-001",str(e))
 record("ai.configure",f"{user['username']}:{body.provider}"); return r

@router.delete("/ai/{provider}")
def delete_ai(provider:str,req:Request):
 user=require(req,"settings")
 try:r=ai_remove(provider)
 except ValueError as e: fail(400,"AI-001",str(e))
 record("ai.remove",f"{user['username']}:{provider}"); return r

@router.post("/ai/chat")
def ai_chat(body:AIAsk,req:Request):
 user=require(req)
 if not body.prompt.strip(): fail(400,"AI-002","Prompt is required")
 if len(body.prompt)>8000: fail(400,"AI-002","Prompt is too long")
 try:r=chat_answer(body.prompt)
 except ValueError as e: fail(400,"AI-001",str(e))
 except RuntimeError as e: fail(502,"AI-003",str(e))
 record("ai.chat",f"{user['username']}:provider={r['provider']}:chars={len(body.prompt)}")
 return {"answer":r["answer"]}

@router.get("/booster")
def get_booster(req:Request):
 require(req,"settings"); return booster_status()

@router.post("/booster")
def set_booster(body:BoostBody,req:Request):
 user=require(req,"settings")
 r=booster_enable() if body.enabled else booster_normal()
 record("booster.change",f"{user['username']}:enabled={body.enabled}:applied={r.get('applied',False)}")
 return r
