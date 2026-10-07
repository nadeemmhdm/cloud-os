from fastapi import APIRouter,Request
from pydantic import BaseModel
from .api import require,fail
from .audit import record
from .shares import create,revoke
router=APIRouter(prefix='/api')
class ShareCreate(BaseModel):
 path:str
 password:str=''
 expires_hours:int=168
 allow_download:bool=True
@router.post('/shares')
def new_share(body:ShareCreate,req:Request):
 user=require(req,'files.read')
 try:r=create(body.path,body.password,body.expires_hours,body.allow_download)
 except FileNotFoundError:fail(404,'FILE-001','Only existing Cloud OS storage files or folders can be shared')
 except ValueError as e:fail(400,'FILE-002',str(e))
 record('share.create',f"{user['username']}:{body.path}")
 base=str(req.base_url).rstrip('/')
 return {**r,'share_url':f"{base}/share/{r['token']}",'preview_url':f"{base}/share/{r['token']}/view"}
@router.delete('/shares/{share_token}')
def remove_share(share_token:str,req:Request):
 user=require(req,'files.read'); ok=revoke(share_token); record('share.revoke',f"{user['username']}:{share_token[:8]}"); return {'revoked':ok}
