from __future__ import annotations
import shutil,subprocess
from fastapi import APIRouter,HTTPException,Request,Response,UploadFile,File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from .auth import login,logout,allowed,identity,login_allowed,login_cooldown,note_login_failure,clear_login_failures,verify,hash_password,revoke_user,change_admin_password,create_recovery_key,recover_owner,set_owner_locked,owner_security
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
from .updater import update_status,check_now
from .cloudflare import connect as cloudflare_connect,disconnect as cloudflare_disconnect,restart as cloudflare_restart
from .shares import create as create_share,revoke as revoke_share

router=APIRouter(prefix="/api")
SAFE_METHODS={"GET","HEAD","OPTIONS"}; MAX_UPLOAD=1024*1024*1024
class Login(BaseModel): password:str; username:str="admin"
class UserCreate(BaseModel): username:str; password:str; display_name:str=""; role:str="member"
class TeamCreate(BaseModel): name:str
class MemberChange(BaseModel): username:str; role:str="member"
class Command(BaseModel): command:str; shell:str|None=None; privileged:bool=False; session_id:str|None=None
class TerminalSession(BaseModel): shell:str|None=None
class PathBody(BaseModel): path:str
class FileCreate(BaseModel): path:str; content:str=""
class RenameBody(BaseModel): path:str; new_name:str
class FileSave(BaseModel): path:str; content:str
class ShareCreate(BaseModel): path:str; password:str=""; expires_hours:int=168; allow_download:bool=True
class AIConfig(BaseModel): provider:str; api_key:str; model:str=""
class AIAsk(BaseModel): prompt:str
class BoostBody(BaseModel): enabled:bool=True
class PasswordChange(BaseModel): current_password:str; new_password:str
class AdminPasswordReset(BaseModel): new_password:str
class AccountState(BaseModel): disabled:bool
class OwnerLock(BaseModel): locked:bool; reason:str=""
class OwnerRecovery(BaseModel): recovery_key:str; new_password:str
class CloudflareConnect(BaseModel): tunnel_token:str; label:str="Existing Cloudflare Tunnel"
def token(req): return req.cookies.get("cloudos_session","")
def fail(status,code,detail=None): raise HTTPException(status,detail=payload(code,detail))
def _same_origin(req):
 if req.method in SAFE_METHODS:return
 if (req.headers.get('sec-fetch-site') or '').lower()=='cross-site':fail(403,'PERM-001','Cross-site state-changing request blocked')
 origin=req.headers.get('origin'); host=req.headers.get('host','')
 if origin and origin not in (f'http://{host}',f'https://{host}'):fail(403,'PERM-001','Cross-origin state-changing request blocked')
def require(req,permission=None):
 _same_origin(req); t=token(req); user=identity(t)
 if not user:fail(401,'AUTH-003')
 if permission and not allowed(t,permission):fail(403,'PERM-001')
 return user
@router.get('/recovery/status')
def recovery_status(): s=owner_security(); return {'recovery_configured':s['recovery_configured']}
@router.post('/recovery/owner')
def owner_recover(body:OwnerRecovery,request:Request):
 _same_origin(request); ip=request.client.host if request.client else 'unknown'; key=f'recovery-ip:{ip}'; cooldown=login_cooldown(key)
 if cooldown: raise HTTPException(429,detail=payload('AUTH-002','Recovery temporarily locked. Try again later.'),headers={'Retry-After':str(cooldown)})
 try:ok=recover_owner(body.recovery_key,body.new_password)
 except ValueError as e:fail(400,'USER-001',str(e))
 if not ok: note_login_failure(key); fail(401,'AUTH-001','Invalid recovery key')
 clear_login_failures(key); record('owner.recovery.success','owner account unlocked and password reset'); return {'ok':True}
@router.post('/login')
def do_login(body:Login,request:Request,response:Response):
 _same_origin(request); ip=request.client.host if request.client else 'unknown'; username=body.username.strip(); ak=f'account:{username.lower()}'; ik=f'ip:{ip}'; cooldown=max(login_cooldown(ak),login_cooldown(ik))
 if cooldown:raise HTTPException(429,detail=payload('AUTH-002','Login temporarily locked. Try again shortly.'),headers={'Retry-After':str(cooldown)})
 t=login(body.password,username)
 if not t:
  wait=max(note_login_failure(ak),note_login_failure(ik)); record('login.failed',username)
  if wait:raise HTTPException(429,detail=payload('AUTH-002','Login temporarily locked. Try again shortly.'),headers={'Retry-After':str(wait)})
  fail(401,'AUTH-001')
 clear_login_failures(ak);clear_login_failures(ik);cfg=load();response.set_cookie('cloudos_session',t,httponly=True,samesite='strict',secure=bool(cfg.get('secure_cookies')),max_age=43200,path='/');record('login',username);return {'ok':True,'user':identity(t)}
@router.post('/logout')
def do_logout(req:Request,response:Response):_same_origin(req);logout(token(req));response.delete_cookie('cloudos_session',path='/');return {'ok':True}
@router.get('/files')
def files(req:Request,path:str=''):
 require(req,'files.read')
 try:return list_items(path)
 except FileNotFoundError as e:fail(404,'FILE-001',str(e))
 except ValueError as e:fail(400,'FILE-002',str(e))
@router.post('/folder')
def folder(body:PathBody,req:Request):
 require(req,'files.write')
 try:safe_path(body.path).mkdir(parents=True,exist_ok=False)
 except FileExistsError as e:fail(409,'FILE-005',str(e))
 except ValueError as e:fail(400,'FILE-002',str(e))
 record('folder.create',body.path);return {'ok':True}
@router.post('/file')
def create_file(body:FileCreate,req:Request):
 require(req,'files.write');p=safe_path(body.path)
 if p.exists():fail(409,'FILE-005','File already exists')
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(body.content,encoding='utf-8');record('file.create',body.path);return {'ok':True}
@router.get('/file/content')
def file_content(path:str,req:Request):
 require(req,'files.read');p=safe_path(path)
 if not p.is_file():fail(404,'FILE-001')
 if p.stat().st_size>2*1024*1024:fail(413,'FILE-003','Text editor limit is 2 MiB')
 try:return {'path':path,'content':p.read_text(encoding='utf-8')}
 except UnicodeDecodeError:fail(400,'FILE-005','This file is not UTF-8 text')
@router.put('/file/content')
def save_file(body:FileSave,req:Request):require(req,'files.write');p=safe_path(body.path);p.write_text(body.content,encoding='utf-8');record('file.edit',body.path);return {'ok':True}
@router.post('/files/rename')
def rename_file(body:RenameBody,req:Request):
 require(req,'files.write')
 if not body.new_name or body.new_name in('.','..') or '/' in body.new_name or '\\' in body.new_name:fail(400,'FILE-002','Invalid name')
 src=safe_path(body.path);root=safe_path('');dst=safe_path(str(src.relative_to(root).parent/body.new_name));src.rename(dst);record('file.rename',body.path+' -> '+body.new_name);return {'ok':True}
@router.delete('/files')
def remove(path:str,req:Request):require(req,'files.write');p=safe_path(path);root=safe_path('');shutil.rmtree(p) if p.is_dir() else p.unlink();record('file.delete',path);return {'ok':True}
@router.post('/upload')
async def upload(req:Request,path:str='',file:UploadFile=File(...)):
 require(req,'files.write');dest=safe_upload_path(path,file.filename or 'upload.bin');total=0
 with dest.open('wb') as out:
  while True:
   chunk=await file.read(1024*1024)
   if not chunk:break
   total+=len(chunk)
   if total>MAX_UPLOAD:out.close();dest.unlink(missing_ok=True);fail(413,'FILE-003')
   out.write(chunk)
 record('file.upload',dest.name);return {'ok':True,'size':total}
@router.get('/download')
def download(path:str,req:Request):require(req,'files.read');p=safe_path(path);return FileResponse(p,filename=p.name)
@router.post('/shares')
def new_share(body:ShareCreate,req:Request):
 user=require(req,'files.read')
 try:r=create_share(body.path,body.password,body.expires_hours,body.allow_download)
 except FileNotFoundError:fail(404,'FILE-001','Only files can be shared')
 record('share.create',f"{user['username']}:{body.path}");return r
@router.delete('/shares/{share_token}')
def delete_share(share_token:str,req:Request):require(req,'files.read');return {'revoked':revoke_share(share_token)}
@router.get('/terminal/shells')
def terminal_shells(req:Request):require(req,'terminal');return {'shells':available_shells()}
@router.post('/terminal/session')
def terminal_session(body:TerminalSession,req:Request):user=require(req,'terminal');r=create_session(body.shell);record('terminal.session.open',f"{user['username']}:shell={r['shell']}");return r
@router.delete('/terminal/session/{session_id}')
def terminal_session_close(session_id:str,req:Request):require(req,'terminal');return {'ok':close_session(session_id)}
@router.post('/terminal')
def terminal(body:Command,req:Request):
 user=require(req,'terminal')
 if body.privileged and user.get('role') not in ('owner','admin'):fail(403,'TERM-003')
 try:r=execute(body.command,shell=body.shell,privileged=body.privileged,session_id=body.session_id)
 except subprocess.TimeoutExpired:fail(408,'TERM-002')
 record('terminal.command',f"{user['username']}:privileged={body.privileged}:code={r.get('code')}:command_length={len(body.command)}");return r
@router.post('/backup')
def backup(req:Request):require(req,'backups');p=create_backup();record('backup.create',p);return {'path':p}
@router.get('/backups')
def backups(req:Request):require(req,'backups');return list_backups()
@router.get('/backups/{name}')
def backup_details(name:str,req:Request):require(req,'backups');return backup_info(name)
@router.post('/backups/{name}/restore')
def backup_restore(name:str,req:Request):user=require(req,'backups');r=restore_backup(name);record('backup.restore',name);return r
@router.delete('/backups/{name}')
def backup_delete(name:str,req:Request):require(req,'backups');return {'deleted':delete_backup(name)}
@router.get('/doctor')
def doctor(req:Request):require(req,'settings');return report()
@router.get('/integrations')
def integrations(req:Request):require(req,'network');return integration_status()
@router.post('/integrations/cloudflare/connect')
def connect_cloudflare(body:CloudflareConnect,req:Request):user=require(req,'settings');r=cloudflare_connect(body.tunnel_token,body.label);record('cloudflare.connect',user['username']);return r
@router.post('/integrations/cloudflare/restart')
def restart_cloudflare(req:Request):user=require(req,'settings');return cloudflare_restart()
@router.delete('/integrations/cloudflare')
def disconnect_cloudflare(req:Request):user=require(req,'settings');return cloudflare_disconnect()
@router.get('/audit')
def audit(req:Request):require(req,'audit');return recent()
@router.get('/me')
def me(req:Request):return require(req)
@router.get('/security/owner')
def get_owner_security(req:Request):user=require(req,'settings');return owner_security()
@router.post('/security/owner/recovery-key')
def generate_owner_recovery(req:Request):user=require(req,'settings');key=create_recovery_key(force=True);return {'recovery_key':key,'shown_once':True}
@router.post('/security/owner/lock')
def owner_lock(body:OwnerLock,req:Request):user=require(req,'settings');set_owner_locked(True,body.reason);return {'ok':True,'reauthenticate':True}
@router.get('/users')
def list_users(req:Request):require(req,'teams.manage');cfg=load();return [{'username':'admin','id':'builtin-owner','display_name':'Administrator','role':'owner','disabled':False,'created_at':None,'first_login_at':cfg.get('admin_first_login_at'),'last_login_at':cfg.get('admin_last_login_at')}]+users()
@router.post('/users')
def new_user(body:UserCreate,req:Request):require(req,'teams.manage');return create_user(body.username,body.password,body.display_name,body.role)
@router.post('/account/password')
def own_password(body:PasswordChange,req:Request):
 user=require(req)
 if user['username']=='admin':change_admin_password(body.current_password,body.new_password)
 else:set_password(user['username'],body.new_password);revoke_user(user['username'])
 return {'ok':True,'reauthenticate':True}
@router.post('/users/{username}/password')
def admin_password(username:str,body:AdminPasswordReset,req:Request):require(req,'teams.manage');set_password(username,body.new_password);revoke_user(username);return {'ok':True}
@router.post('/users/{username}/state')
def admin_state(username:str,body:AccountState,req:Request):require(req,'teams.manage');set_disabled(username,body.disabled);return {'ok':True}
@router.get('/teams')
def list_teams(req:Request):require(req,'teams.manage');return teams()
@router.post('/teams')
def new_team(body:TeamCreate,req:Request):require(req,'teams.manage');return create_team(body.name)
@router.post('/teams/{team}/members')
def team_add(team:str,body:MemberChange,req:Request):require(req,'teams.manage');add_member(team,body.username,body.role);return {'ok':True}
@router.delete('/teams/{team}/members/{username}')
def team_remove(team:str,username:str,req:Request):require(req,'teams.manage');remove_member(team,username);return {'ok':True}
@router.get('/ai/status')
def get_ai_status(req:Request):require(req,'settings');return ai_status()
@router.post('/ai/configure')
def set_ai(body:AIConfig,req:Request):user=require(req,'settings');return ai_configure(body.provider,body.api_key,body.model)
@router.delete('/ai/{provider}')
def delete_ai(provider:str,req:Request):require(req,'settings');return ai_remove(provider)
@router.post('/ai/chat')
def ai_chat(body:AIAsk,req:Request):user=require(req);r=chat_answer(body.prompt);return {'answer':r['answer']}
@router.get('/booster')
def get_booster(req:Request):require(req,'settings');return booster_status()
@router.post('/booster')
def set_booster(body:BoostBody,req:Request):require(req,'settings');return booster_enable() if body.enabled else booster_normal()
@router.get('/update/status')
def get_update_status(req:Request):require(req);return update_status()
@router.post('/update/check')
def update_check_now(req:Request):require(req,'settings');return check_now()
