from __future__ import annotations
import json,re,secrets
from datetime import datetime,timezone
from .config import APP_DIR
from .auth import hash_password,verify

DB=APP_DIR/"access.json"
NAME_RE=re.compile(r"^[A-Za-z0-9_.-]{1,64}$")
DEFAULT_ROLES={
 "owner":["*"],
 "admin":["files.read","files.write","terminal","backups","backups.read","backups.write","network","audit","teams.manage","settings"],
 "operator":["files.read","files.write","terminal","backups","backups.read","backups.write","network"],
 "member":["files.read","files.write"],
 "viewer":["files.read","backups","backups.read"]
}
ASSIGNABLE_ROLES={"operator","member","viewer"}

def _load():
 APP_DIR.mkdir(parents=True,exist_ok=True)
 if not DB.exists(): _save({"users":{},"teams":{}})
 try:
  d=json.loads(DB.read_text(encoding="utf-8"))
  if not isinstance(d,dict) or not isinstance(d.get("users"),dict) or not isinstance(d.get("teams"),dict): raise ValueError
  return d
 except (OSError,json.JSONDecodeError,TypeError,ValueError) as exc: raise RuntimeError(f"Access database is unreadable or corrupt: {exc}") from exc

def _save(data):
 APP_DIR.mkdir(parents=True,exist_ok=True);tmp=DB.with_suffix(".tmp");tmp.write_text(json.dumps(data,indent=2),encoding="utf-8")
 try:
  if __import__("os").name!="nt":tmp.chmod(0o600)
 except OSError:pass
 tmp.replace(DB)
 try:
  if __import__("os").name!="nt":DB.chmod(0o600)
 except OSError:pass

def _name(value,label):
 if not NAME_RE.fullmatch(value or ""):raise ValueError(f"Invalid {label}; use 1-64 letters, numbers, dot, underscore or hyphen")
def _key(mapping,value):
 value=(value or "").strip().lower();return next((k for k in mapping if k.lower()==value),None)
def create_user(username,password,display_name="",role="member"):
 username=(username or "").strip();role=(role or "member").strip().lower();_name(username,"username")
 if username.lower()=="admin":raise ValueError("The built-in owner username 'admin' is reserved")
 if role not in ASSIGNABLE_ROLES:raise ValueError("Invalid role; choose operator, member or viewer")
 d=_load()
 if _key(d["users"],username):raise ValueError("User already exists")
 d["users"][username]={"id":secrets.token_hex(8),"display_name":(display_name or username)[:128],"password_hash":hash_password(password),"role":role,"disabled":False,"created_at":datetime.now(timezone.utc).isoformat(),"first_login_at":None,"last_login_at":None};_save(d);return public_user(username,d["users"][username])
def authenticate(username,password):
 d=_load();key=_key(d["users"],username);u=d["users"].get(key) if key else None;return u if u and not u.get("disabled") and verify(password,u["password_hash"]) else None
def public_user(name,u):return {"username":name,"id":u["id"],"display_name":u.get("display_name",name),"role":u.get("role","member"),"disabled":u.get("disabled",False),"created_at":u.get("created_at"),"first_login_at":u.get("first_login_at"),"last_login_at":u.get("last_login_at")}
def note_login(username):
 d=_load();key=_key(d["users"],username);u=d["users"].get(key) if key else None
 if not u:return
 now=datetime.now(timezone.utc).isoformat()
 if not u.get("first_login_at"):u["first_login_at"]=now
 u["last_login_at"]=now;_save(d)
def set_password(username,password):
 d=_load();key=_key(d["users"],username)
 if not key:raise ValueError("Unknown user")
 d["users"][key]["password_hash"]=hash_password(password);_save(d)
def set_disabled(username,disabled):
 d=_load();key=_key(d["users"],username)
 if not key:raise ValueError("Unknown user")
 d["users"][key]["disabled"]=bool(disabled);_save(d)
def set_role(username,role):
 role=(role or "").strip().lower()
 if role not in ASSIGNABLE_ROLES:raise ValueError("Invalid role; choose operator, member or viewer")
 d=_load();key=_key(d["users"],username)
 if not key:raise ValueError("Unknown user")
 d["users"][key]["role"]=role;_save(d);return public_user(key,d["users"][key])
def users():return [public_user(n,u) for n,u in _load()["users"].items()]
def create_team(name):
 name=(name or "").strip();_name(name,"team name");d=_load()
 if _key(d["teams"],name):raise ValueError("Team already exists")
 d["teams"][name]={"id":secrets.token_hex(8),"members":{}};_save(d);return {"name":name,**d["teams"][name]}
def teams():return [{"name":n,**t} for n,t in _load()["teams"].items()]
def add_member(team,username,role="member"):
 role=(role or "member").strip().lower()
 if role not in ASSIGNABLE_ROLES:raise ValueError("Only operator, member or viewer can be assigned")
 d=_load();team_key=_key(d["teams"],team);user_key=_key(d["users"],username)
 if not team_key:raise ValueError("Unknown team")
 if not user_key:raise ValueError("Unknown user; create the user account before adding it to a team")
 d["teams"][team_key]["members"][user_key]=role;_save(d)
def remove_member(team,username):
 d=_load();team_key=_key(d["teams"],team)
 if not team_key:raise ValueError("Unknown team")
 user_key=_key(d["teams"][team_key].get("members",{}),username)
 if user_key:d["teams"][team_key]["members"].pop(user_key,None);_save(d)
def permissions(username):
 d=_load();key=_key(d["users"],username);u=d["users"].get(key) if key else None;perms=set(DEFAULT_ROLES.get(u.get("role","viewer"),[])) if u else set()
 for t in d["teams"].values():
  member_key=_key(t.get("members",{}),key or username)
  if member_key:perms.update(DEFAULT_ROLES.get(t["members"][member_key],[]))
 return sorted(perms)
