from fastapi import APIRouter,Request,HTTPException
from pydantic import BaseModel
from .api import require,fail
from .audit import record
from .shares import create,revoke
from .updater import check_now,start_install,update_status
router=APIRouter(prefix='/api')
class ShareCreate(BaseModel):
 path:str
 password:str=''
 expires_hours:int=168
class UpdateInstall(BaseModel):force:bool=False
@router.post('/shares')
def new_share(body:ShareCreate,req:Request):
 user=require(req,'files.read')
 try:r=create(body.path,body.password,body.expires_hours,True)
 except FileNotFoundError:fail(404,'FILE-001','Only an existing storage file or folder can be shared')
 except ValueError as e:fail(400,'FILE-002',str(e))
 base=str(req.base_url).rstrip('/');r['url']=f"{base}/share/{r['token']}";r['preview_url']=r['url'];r['permissions']=['read','download'];r['expires']='never' if r.get('expires_at') is None else 'scheduled';record('share.create',f"{user['username']}:{body.path}");return r
@router.delete('/shares/{share_token}')
def remove_share(share_token:str,req:Request):
 user=require(req,'files.read');ok=revoke(share_token);record('share.revoke',f"{user['username']}:{share_token[:8]}");return {'revoked':ok}
@router.post('/update/install')
def install_update(body:UpdateInstall,req:Request):
 user=require(req,'settings')
 try:
  if not body.force:check_now()
  result=start_install(force=body.force)
 except RuntimeError as exc:raise HTTPException(409,detail={'code':'UPDATE-001','message':str(exc)})
 record('update.install',f"{user['username']}:force={body.force}");return {'ok':True,'message':'Background update started. Cloud OS will restart automatically after success or rollback.','status':result}
@router.get('/update/progress')
def update_progress(req:Request):require(req);return update_status()
