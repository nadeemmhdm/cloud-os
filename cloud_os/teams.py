from __future__ import annotations
import json,re,secrets
from .config import APP_DIR
from .auth import hash_password,verify

DB=APP_DIR/"access.json"
NAME_RE=re.compile(r"^[A-Za-z0-9_.-]{1,64}$")
DEFAULT_ROLES={
 "owner":["*"],
 "admin":["files.read","files.write","terminal","backups","network","audit","teams.manage","settings"],
 "operator":["files.read","files.write","terminal","backups","network"],
 "member":["files.read","files.write"],
 "viewer":["files.read"]
}

def _load():
 APP_DIR.mkdir(parents=True,exist_ok=True)
 if not DB.exists(): _save({"users":{},"teams":{}})
 try:
  d=json.loads(DB.read_text(encoding="utf-8"))
  if not isinstance(d,dict) or not isinstance(d.get("users"),dict) or not isinstance(d.get("teams"),dict): raise ValueError
  return d
 except Exception:return {"users":{},"teams":{}}

def _save(data):
 APP_DIR.mkdir(parents=True,exist_ok=True)
 tmp=DB.with_suffix(".tmp"); tmp.write_text(json.dumps(data,indent=2),encoding="utf-8")
 try:
  if __import__("os").name!="nt": tmp.chmod(0o600)
 except OSError: pass
 tmp.replace(DB)
 try:
  if __import__("os").name!="nt": DB.chmod(0o600)
 except OSError: pass

def _name(value,label):
 if not NAME_RE.fullmatch(value or ""): raise ValueError(f"Invalid {label}; use 1-64 letters, numbers, dot, underscore or hyphen")

def create_user(username,password,display_name="",role="member"):
 _name(username,"username")
 if username=="admin": raise ValueError("Reserved username")
 if role not in DEFAULT_ROLES: raise ValueError("Invalid role")
 d=_load()
 if username in d["users"]: raise ValueError("User already exists")
 d["users"][username]={"id":secrets.token_hex(8),"display_name":(display_name or username)[:128],"password_hash":hash_password(password),"role":role,"disabled":False}
 _save(d); return public_user(username,d["users"][username])

def authenticate(username,password):
 u=_load()["users"].get(username)
 return u if u and not u.get("disabled") and verify(password,u["password_hash"]) else None

def public_user(name,u): return {"username":name,"id":u["id"],"display_name":u.get("display_name",name),"role":u.get("role","member"),"disabled":u.get("disabled",False)}
def users(): return [public_user(n,u) for n,u in _load()["users"].items()]

def create_team(name):
 _name(name,"team name"); d=_load()
 if name in d["teams"]: raise ValueError("Team already exists")
 d["teams"][name]={"id":secrets.token_hex(8),"members":{}}; _save(d); return {"name":name,**d["teams"][name]}

def teams(): return [{"name":n,**t} for n,t in _load()["teams"].items()]

def add_member(team,username,role="member"):
 if role not in DEFAULT_ROLES: raise ValueError("Invalid role")
 d=_load()
 if team not in d["teams"] or username not in d["users"]: raise ValueError("Unknown team or user")
 d["teams"][team]["members"][username]=role; _save(d)

def remove_member(team,username):
 d=_load()
 if team not in d["teams"]: raise ValueError("Unknown team")
 d["teams"][team]["members"].pop(username,None); _save(d)

def permissions(username):
 d=_load(); u=d["users"].get(username); perms=set(DEFAULT_ROLES.get(u.get("role","viewer"),[])) if u else set()
 for t in d["teams"].values():
  if username in t["members"]: perms.update(DEFAULT_ROLES.get(t["members"][username],[]))
 return sorted(perms)
