from __future__ import annotations
from fastapi import APIRouter,Request,HTTPException
from pydantic import BaseModel
from .api import require
from .audit import record
from .updater import check_now,start_install,update_status

router=APIRouter(prefix="/api/update")
class InstallRequest(BaseModel):force:bool=False

@router.post("/install")
def install_update(body:InstallRequest,req:Request):
 user=require(req,"settings")
 try:
  if not body.force:check_now()
  result=start_install(force=body.force)
 except RuntimeError as exc:raise HTTPException(409,detail={"code":"UPDATE-001","message":str(exc)})
 record("update.install",f"{user['username']}:force={body.force}")
 return {"ok":True,"message":"Update started in the background. Cloud OS will restart automatically after success or rollback.","status":result}

@router.get("/progress")
def update_progress(req:Request):require(req);return update_status()
