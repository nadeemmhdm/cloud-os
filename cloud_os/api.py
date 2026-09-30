from __future__ import annotations
import os,shutil
from fastapi import APIRouter,HTTPException,Request,UploadFile,File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from .auth import login,valid,logout
from .files import safe_path,list_items
from .terminal import execute
from .backup import create_backup,list_backups
from .doctor import report
from .integrations import status as integration_status
from .audit import record,recent
router=APIRouter(prefix="/api")
class Login(BaseModel): password:str
class Command(BaseModel): command:str
class PathBody(BaseModel): path:str
def token(req): return req.cookies.get("cloudos_session","")
def admin(req):
 if not valid(token(req)): raise HTTPException(401,"Admin login required")
@router.post("/login")
def do_login(body:Login,response):
 t=login(body.password)
 if not t: raise HTTPException(401,"Invalid credentials")
 response.set_cookie("cloudos_session",t,httponly=True,samesite="strict",secure=False,max_age=43200); record("login"); return {"ok":True}
@router.post("/logout")
def do_logout(req:Request,response):
 logout(token(req)); response.delete_cookie("cloudos_session"); return {"ok":True}
@router.get("/files")
def files(req:Request,path:str=""):
 admin(req); return list_items(path)
@router.post("/folder")
def folder(body:PathBody,req:Request):
 admin(req); safe_path(body.path).mkdir(parents=True,exist_ok=False); record("folder.create",body.path); return {"ok":True}
@router.delete("/files")
def remove(path:str,req:Request):
 admin(req); p=safe_path(path)
 if p==safe_path(""): raise HTTPException(400,"Cannot delete storage root")
 shutil.rmtree(p) if p.is_dir() else p.unlink(); record("file.delete",path); return {"ok":True}
@router.post("/upload")
async def upload(req:Request,path:str="",file:UploadFile=File(...)):
 admin(req); dest=safe_path(str(os.path.join(path,file.filename or "upload.bin")))
 with dest.open("wb") as out:
  while chunk:=await file.read(1024*1024): out.write(chunk)
 record("file.upload",str(dest.name)); return {"ok":True}
@router.get("/download")
def download(path:str,req:Request):
 admin(req); p=safe_path(path)
 if not p.is_file(): raise HTTPException(404)
 return FileResponse(p,filename=p.name)
@router.post("/terminal")
def terminal(body:Command,req:Request):
 admin(req)
 try:r=execute(body.command)
 except Exception as e: raise HTTPException(400,str(e))
 record("terminal.command",body.command[:200]); return r
@router.post("/backup")
def backup(req:Request):
 admin(req); p=create_backup(); record("backup.create",p); return {"path":p}
@router.get("/backups")
def backups(req:Request): admin(req); return list_backups()
@router.get("/doctor")
def doctor(req:Request): admin(req); return report()
@router.get("/integrations")
def integrations(req:Request): admin(req); return integration_status()
@router.get("/audit")
def audit(req:Request): admin(req); return recent()
