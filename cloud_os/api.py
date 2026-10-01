from __future__ import annotations
import shutil
from fastapi import APIRouter,HTTPException,Request,Response,UploadFile,File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from .auth import login,logout,allowed,identity,login_allowed,note_login_failure,clear_login_failures
from .files import safe_path,safe_upload_path,list_items
from .terminal import execute
from .backup import create_backup,list_backups
from .doctor import report
from .integrations import status as integration_status
from .audit import record,recent
from .teams import create_user,users,create_team,teams,add_member,remove_member
from .config import load

router=APIRouter(prefix="/api")
MAX_UPLOAD=1024*1024*1024

class Login(BaseModel): password:str; username:str="admin"
class UserCreate(BaseModel): username:str; password:str; display_name:str=""; role:str="member"
class TeamCreate(BaseModel): name:str
class MemberChange(BaseModel): username:str; role:str="member"
class Command(BaseModel): command:str
class PathBody(BaseModel): path:str

def token(req:Request): return req.cookies.get("cloudos_session","")

def require(req:Request,permission:str|None=None):
 t=token(req); user=identity(t)
 if not user: raise HTTPException(401,"Login required")
 if permission and not allowed(t,permission): raise HTTPException(403,"Permission denied")
 return user

@router.post("/login")
def do_login(body:Login,request:Request,response:Response):
 key=f"{request.client.host if request.client else 'unknown'}:{body.username}"
 if not login_allowed(key): raise HTTPException(429,"Too many login attempts. Try again later.")
 t=login(body.password,body.username)
 if not t:
  note_login_failure(key); record("login.failed",body.username); raise HTTPException(401,"Invalid credentials")
 clear_login_failures(key)
 cfg=load()
 response.set_cookie("cloudos_session",t,httponly=True,samesite="strict",secure=bool(cfg.get("secure_cookies")),max_age=43200,path="/")
 record("login",body.username)
 return {"ok":True,"user":identity(t)}

@router.post("/logout")
def do_logout(req:Request,response:Response):
 logout(token(req)); response.delete_cookie("cloudos_session",path="/"); return {"ok":True}

@router.get("/files")
def files(req:Request,path:str=""):
 require(req,"files.read")
 try:return list_items(path)
 except (ValueError,FileNotFoundError) as e: raise HTTPException(400,str(e))

@router.post("/folder")
def folder(body:PathBody,req:Request):
 require(req,"files.write")
 try:safe_path(body.path).mkdir(parents=True,exist_ok=False)
 except (ValueError,FileExistsError) as e: raise HTTPException(400,str(e))
 record("folder.create",body.path); return {"ok":True}

@router.delete("/files")
def remove(path:str,req:Request):
 require(req,"files.write")
 try:p=safe_path(path); root=safe_path("")
 except ValueError as e: raise HTTPException(400,str(e))
 if p==root: raise HTTPException(400,"Cannot delete storage root")
 if not p.exists(): raise HTTPException(404,"Path not found")
 shutil.rmtree(p) if p.is_dir() else p.unlink()
 record("file.delete",path); return {"ok":True}

@router.post("/upload")
async def upload(req:Request,path:str="",file:UploadFile=File(...)):
 require(req,"files.write")
 try:dest=safe_upload_path(path,file.filename or "upload.bin")
 except (ValueError,FileNotFoundError) as e: raise HTTPException(400,str(e))
 total=0
 try:
  with dest.open("wb") as out:
   while True:
    chunk=await file.read(1024*1024)
    if not chunk: break
    total+=len(chunk)
    if total>MAX_UPLOAD:
     out.close(); dest.unlink(missing_ok=True); raise HTTPException(413,"Upload exceeds 1 GiB limit")
    out.write(chunk)
 except HTTPException: raise
 except OSError as e: raise HTTPException(500,f"Upload failed: {e}")
 record("file.upload",dest.name); return {"ok":True,"size":total}

@router.get("/download")
def download(path:str,req:Request):
 require(req,"files.read")
 try:p=safe_path(path)
 except ValueError as e: raise HTTPException(400,str(e))
 if not p.is_file(): raise HTTPException(404,"File not found")
 return FileResponse(p,filename=p.name)

@router.post("/terminal")
def terminal(body:Command,req:Request):
 user=require(req,"terminal")
 try:r=execute(body.command)
 except Exception as e: raise HTTPException(400,str(e))
 record("terminal.command",f"{user['username']}:{body.command[:200]}"); return r

@router.post("/backup")
def backup(req:Request):
 require(req,"backups"); p=create_backup(); record("backup.create",p); return {"path":p}

@router.get("/backups")
def backups(req:Request): require(req,"backups"); return list_backups()
@router.get("/doctor")
def doctor(req:Request): require(req,"settings"); return report()
@router.get("/integrations")
def integrations(req:Request): require(req,"network"); return integration_status()
@router.get("/audit")
def audit(req:Request): require(req,"audit"); return recent()
@router.get("/me")
def me(req:Request): return require(req)
@router.get("/users")
def list_users(req:Request): require(req,"teams.manage"); return users()

@router.post("/users")
def new_user(body:UserCreate,req:Request):
 require(req,"teams.manage")
 try:u=create_user(body.username,body.password,body.display_name,body.role)
 except ValueError as e: raise HTTPException(400,str(e))
 record("user.create",body.username); return u

@router.get("/teams")
def list_teams(req:Request): require(req,"teams.manage"); return teams()

@router.post("/teams")
def new_team(body:TeamCreate,req:Request):
 require(req,"teams.manage")
 try:t=create_team(body.name)
 except ValueError as e: raise HTTPException(400,str(e))
 record("team.create",body.name); return t

@router.post("/teams/{team}/members")
def team_add(team:str,body:MemberChange,req:Request):
 require(req,"teams.manage")
 try:add_member(team,body.username,body.role)
 except ValueError as e: raise HTTPException(400,str(e))
 record("team.member.add",team+":"+body.username); return {"ok":True}

@router.delete("/teams/{team}/members/{username}")
def team_remove(team:str,username:str,req:Request):
 require(req,"teams.manage")
 try:remove_member(team,username)
 except ValueError as e: raise HTTPException(400,str(e))
 record("team.member.remove",team+":"+username); return {"ok":True}
