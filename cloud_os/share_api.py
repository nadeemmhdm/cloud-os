from fastapi import APIRouter,Request,HTTPException
from pydantic import BaseModel
from .api import require,fail
from .audit import record
from .auth import revoke_user
from .backup import list_backups,backup_info
from .shares import create,revoke
from .teams import set_role
from .updater import check_now
from .update_control import start_install,control_status
router=APIRouter(prefix='/api')
class ShareCreate(BaseModel):
 path:str
 password:str=''
 expires_hours:int=168
class UpdateInstall(BaseModel):force:bool=False
class RoleChange(BaseModel):role:str
@router.post('/shares')
def new_share(body:ShareCreate,req:Request):
 user=require(req,'files.read')
 try:r=create(body.path,body.password,body.expires_hours,True)
 except FileNotFoundError:fail(404,'FILE-001','Only an existing storage file or folder can be shared')
 except ValueError as e:fail(400,'FILE-002',str(e))
 base=str(req.base_url).rstrip('/');r['url']=f"{base}/share/{r['token']}";r['preview_url']=r['url'];r['permissions']=['read','download'];r['expires']='never' if r.get('expires_at') is None else 'scheduled';record('share.create',f"{user['username']}:{body.path}");return r
@router.delete('/shares/{share_token}')
def remove_share(share_token:str,req:Request):
 user=require(req,'files.write');ok=revoke(share_token);record('share.revoke',f"{user['username']}:{share_token[:8]}");return {'revoked':ok}
@router.post('/access/users/{username}/role')
def change_role(username:str,body:RoleChange,req:Request):
 actor=require(req)
 if actor.get('role')!='owner':fail(403,'PERM-001','Only the owner can change account roles')
 if username.lower()=='admin':fail(400,'USER-001','The built-in owner role cannot be changed')
 try:user=set_role(username,body.role)
 except ValueError as exc:fail(400,'USER-001',str(exc))
 revoke_user(username);record('user.role.change',f"{actor['username']}:{username}:{body.role}");return {'ok':True,'user':user,'sessions_revoked':True}
@router.get('/readonly/backups')
def readonly_backups(req:Request):
 user=require(req,'files.read')
 if user.get('role') not in {'viewer','owner'}:fail(403,'PERM-001')
 return list_backups()
@router.get('/readonly/backups/{name}')
def readonly_backup_info(name:str,req:Request):
 user=require(req,'files.read')
 if user.get('role') not in {'viewer','owner'}:fail(403,'PERM-001')
 try:return backup_info(name)
 except FileNotFoundError as exc:fail(404,'BACKUP-001',str(exc))
 except (ValueError,OSError) as exc:fail(400,'BACKUP-001',str(exc))
@router.post('/update/install')
def install_update(body:UpdateInstall,req:Request):
 user=require(req,'settings')
 try:
  if not body.force:check_now()
  result=start_install(force=body.force)
 except RuntimeError as exc:raise HTTPException(409,detail={'code':'UPDATE-001','message':str(exc)})
 record('update.install',f"{user['username']}:force={body.force}");return {'ok':True,'message':'Background update started. Cloud OS will restart automatically after success or rollback.','status':result}
@router.get('/update/progress')
def update_progress(req:Request):require(req);return control_status()
