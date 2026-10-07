from fastapi import APIRouter,Request
from pydantic import BaseModel
from .api import require,fail
from .audit import record
from .auth import revoke_user
from .teams import set_role

router=APIRouter(prefix="/api/access")
class RoleChange(BaseModel):role:str

@router.post("/users/{username}/role")
def change_role(username:str,body:RoleChange,req:Request):
 actor=require(req)
 if actor.get("role")!="owner":fail(403,"PERM-001","Only the owner can change account roles")
 if username.lower()=="admin":fail(400,"USER-001","The built-in owner role cannot be changed")
 try:user=set_role(username,body.role)
 except ValueError as exc:fail(400,"USER-001",str(exc))
 revoke_user(username)
 record("user.role.change",f"{actor['username']}:{username}:{body.role}")
 return {"ok":True,"user":user,"sessions_revoked":True}
