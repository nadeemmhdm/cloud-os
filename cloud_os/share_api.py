from pathlib import Path
from fastapi import APIRouter,Request,HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from .api import require,fail
from .audit import record
from .auth import revoke_user
from .backup import list_backups,backup_info
from .shares import create,revoke
from .teams import set_role
from .updater import check_now
from .update_control import start_install,control_status
from .labs import catalog as labs_catalog_data,start_lab,get_session,run_command,verify_lab,pause_lab,resume_lab,reset_lab,complete_lab,exit_lab,set_enabled,admin_stats,reset_user_progress
router=APIRouter(prefix='/api')
class ShareCreate(BaseModel):
 path:str
 password:str=''
 expires_hours:int=168
class UpdateInstall(BaseModel):force:bool=False
class RoleChange(BaseModel):role:str
class LabCommand(BaseModel):command:str
class LabToggle(BaseModel):enabled:bool
class LabProgressReset(BaseModel):username:str
@router.get('/ui/share-core.js')
def share_core_ui():return FileResponse(Path(__file__).with_name('share-ui-core.js'),media_type='application/javascript')
@router.get('/ui/terminal.js')
def terminal_ui():return FileResponse(Path(__file__).with_name('terminal-ui.js'),media_type='application/javascript')
@router.get('/ui/labs.js')
def labs_ui():return FileResponse(Path(__file__).with_name('labs-ui.js'),media_type='application/javascript')
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
 except RuntimeError as exc:fail(409,'UPDATE-001',str(exc))
 except OSError as exc:fail(500,'UPDATE-001',f'Could not launch update worker: {exc}')
 record('update.install',f"{user['username']}:force={body.force}");return {'ok':True,'message':'Background update started. Cloud OS will restart automatically after success or rollback.','status':result}
@router.get('/update/progress')
def update_progress(req:Request):require(req);return control_status()

def _lab_user(req:Request):
 user=require(req)
 if user.get('role') not in {'owner','admin','operator','member','viewer'}:fail(403,'PERM-001','Labs are unavailable for this account')
 return user
def _lab_owner(req:Request):
 user=require(req)
 if user.get('role')!='owner':fail(403,'PERM-001','Only the owner can manage lab definitions and progress')
 return user
def _lab_error(exc:Exception):
 if isinstance(exc,KeyError):fail(404,'LAB-1002','Lab definition was not found')
 if isinstance(exc,FileNotFoundError):fail(404,'LAB-1004','Lab session expired or was already cleaned up')
 if isinstance(exc,PermissionError):
  text=str(exc);fail(403,'LAB-1008' if 'path' in text else 'LAB-1005',text)
 if isinstance(exc,ValueError):fail(400,'LAB-1008',str(exc))
 if isinstance(exc,RuntimeError):
  text=str(exc);fail(429 if 'rate limit' in text else 409,'LAB-1007' if 'rate limit' in text else 'LAB-1003',text)
 fail(500,'LAB-1001',str(exc))
@router.get('/labs/catalog')
def labs_catalog(req:Request):
 user=_lab_user(req)
 try:return labs_catalog_data(user['username'])
 except Exception as exc:_lab_error(exc)
@router.post('/labs/{lab_id}/start')
def labs_start(lab_id:str,req:Request):
 user=_lab_user(req)
 try:
  result=start_lab(lab_id,user['username']);record('lab.start',f"{user['username']}:{lab_id}");return result
 except Exception as exc:_lab_error(exc)
@router.get('/labs/session/{session_id}')
def labs_session(session_id:str,req:Request):
 user=_lab_user(req)
 try:return get_session(session_id,user['username'])
 except Exception as exc:_lab_error(exc)
@router.post('/labs/session/{session_id}/command')
def labs_command(session_id:str,body:LabCommand,req:Request):
 user=_lab_user(req)
 try:
  result=run_command(session_id,user['username'],body.command);record('lab.command',f"{user['username']}:{session_id[:8]}");return result
 except Exception as exc:_lab_error(exc)
@router.post('/labs/session/{session_id}/verify')
def labs_verify(session_id:str,req:Request):
 user=_lab_user(req)
 try:
  result=verify_lab(session_id,user['username']);record('lab.verify',f"{user['username']}:{session_id[:8]}:score={result['score']}");return result
 except Exception as exc:_lab_error(exc)
@router.post('/labs/session/{session_id}/pause')
def labs_pause(session_id:str,req:Request):
 user=_lab_user(req)
 try:return pause_lab(session_id,user['username'])
 except Exception as exc:_lab_error(exc)
@router.post('/labs/session/{session_id}/resume')
def labs_resume(session_id:str,req:Request):
 user=_lab_user(req)
 try:return resume_lab(session_id,user['username'])
 except Exception as exc:_lab_error(exc)
@router.post('/labs/session/{session_id}/reset')
def labs_reset(session_id:str,req:Request):
 user=_lab_user(req)
 try:
  result=reset_lab(session_id,user['username']);record('lab.reset',f"{user['username']}:{result['lab_id']}");return result
 except Exception as exc:_lab_error(exc)
@router.post('/labs/session/{session_id}/complete')
def labs_complete(session_id:str,req:Request):
 user=_lab_user(req)
 try:
  result=complete_lab(session_id,user['username']);record('lab.complete',f"{user['username']}:{session_id[:8]}");return result
 except Exception as exc:_lab_error(exc)
@router.delete('/labs/session/{session_id}')
def labs_exit(session_id:str,req:Request):
 user=_lab_user(req)
 try:
  result=exit_lab(session_id,user['username']);record('lab.exit',f"{user['username']}:{session_id[:8]}");return result
 except Exception as exc:_lab_error(exc)
@router.get('/labs/admin')
def labs_admin(req:Request):
 _lab_owner(req)
 try:return admin_stats()
 except Exception as exc:_lab_error(exc)
@router.post('/labs/admin/{lab_id}/enabled')
def labs_admin_toggle(lab_id:str,body:LabToggle,req:Request):
 user=_lab_owner(req)
 try:
  result=set_enabled(lab_id,body.enabled);record('lab.definition.toggle',f"{user['username']}:{lab_id}:{body.enabled}");return result
 except Exception as exc:_lab_error(exc)
@router.post('/labs/admin/progress/reset')
def labs_admin_reset_progress(body:LabProgressReset,req:Request):
 user=_lab_owner(req);username=body.username.strip()
 if not username:fail(400,'USER-001','Username is required')
 try:
  reset_user_progress(username);record('lab.progress.reset',f"{user['username']}:{username}");return {'ok':True}
 except Exception as exc:_lab_error(exc)
