from __future__ import annotations
import hashlib,hmac,secrets,time
from datetime import datetime,timezone
from collections import defaultdict, deque
from .config import load,save

SESSIONS={}
SECURITY_FILE=None
WINDOW=900
LOCK_THRESHOLD=5
MAX_LOCK_SECONDS=900

def _security_path():
 from .config import APP_DIR
 return APP_DIR/"login-security.json" if SECURITY_FILE is None else SECURITY_FILE

def _load_security():
 p=_security_path()
 try:
  d=__import__("json").loads(p.read_text(encoding="utf-8"))
  return d if isinstance(d,dict) else {}
 except (OSError,ValueError): return {}

def _save_security(d):
 p=_security_path(); p.parent.mkdir(parents=True,exist_ok=True)
 tmp=p.with_suffix(".tmp"); tmp.write_text(__import__("json").dumps(d),encoding="utf-8")
 try:
  if __import__("os").name!="nt": tmp.chmod(0o600)
 except OSError: pass
 tmp.replace(p)

def _cooldown_seconds(failures):
 # 5th failure=2s, then 4, 8... capped at 15 minutes.
 return min(MAX_LOCK_SECONDS,2 ** max(1,failures-4))

def login_cooldown(key):
 now=time.time(); d=_load_security(); row=d.get(key,{})
 attempts=[float(x) for x in row.get("attempts",[]) if float(x)>=now-WINDOW]
 locked=float(row.get("locked_until",0) or 0)
 if locked<=now and not attempts:
  if key in d: d.pop(key,None); _save_security(d)
  return 0
 return max(0,int(locked-now+0.999))

def login_allowed(key): return login_cooldown(key)<=0

def note_login_failure(key):
 now=time.time(); d=_load_security(); row=d.get(key,{})
 q=[float(x) for x in row.get("attempts",[]) if float(x)>=now-WINDOW]; q.append(now)
 row={"attempts":q,"locked_until":float(row.get("locked_until",0) or 0)}
 if len(q)>=LOCK_THRESHOLD: row["locked_until"]=max(row["locked_until"],now+_cooldown_seconds(len(q)))
 d[key]=row; _save_security(d)
 return max(0,int(row["locked_until"]-now+0.999))

def clear_login_failures(key):
 d=_load_security()
 if key in d: d.pop(key,None); _save_security(d)

def hash_password(password,salt=None):
 if not isinstance(password,str) or len(password)<12:
  raise ValueError("Password must be at least 12 characters")
 salt=salt or secrets.token_hex(16)
 digest=hashlib.pbkdf2_hmac("sha256",password.encode(),bytes.fromhex(salt),600000)
 return salt+":"+digest.hex()

def verify(password,stored):
 try:
  salt,digest=stored.split(":",1)
  raw=hashlib.pbkdf2_hmac("sha256",password.encode(),bytes.fromhex(salt),600000).hex()
  return hmac.compare_digest(raw,digest)
 except Exception:return False

def ensure_admin(password):
 cfg=load()
 if not cfg.get("admin_password_hash"):
  cfg["admin_password_hash"]=hash_password(password); save(cfg)

def login_allowed(key):
 now=time.time()
 if _LOCKED_UNTIL.get(key,0)>now: return False
 q=_ATTEMPTS[key]
 while q and q[0] < now-WINDOW: q.popleft()
 if not q: _LOCKED_UNTIL.pop(key,None)
 return True

def note_login_failure(key):
 now=time.time(); q=_ATTEMPTS[key]
 while q and q[0] < now-WINDOW: q.popleft()
 q.append(now)
 if len(q)>=LOCK_THRESHOLD: _LOCKED_UNTIL[key]=now+_cooldown_seconds(len(q))

def clear_login_failures(key):
 _ATTEMPTS.pop(key,None); _LOCKED_UNTIL.pop(key,None)

def login(password,username="admin"):
 cfg=load()
 if username=="admin":
  if not cfg.get("admin_password_hash") or not verify(password,cfg.get("admin_password_hash","")): return None
  now=datetime.now(timezone.utc).isoformat()
  cfg.setdefault("admin_first_login_at",now); cfg["admin_last_login_at"]=now; save(cfg)
  identity_data={"username":"admin","role":"owner","permissions":["*"]}
 else:
  from .teams import authenticate,permissions
  u=authenticate(username,password)
  if not u:return None
  from .teams import note_login
  note_login(username)
  identity_data={"username":username,"role":u.get("role","member"),"permissions":permissions(username)}
 token=secrets.token_urlsafe(32)
 SESSIONS[token]={"expires":time.time()+43200,"identity":identity_data}
 return token

def identity(token):
 s=SESSIONS.get(token)
 if not s:return None
 if s["expires"]<time.time(): SESSIONS.pop(token,None); return None
 return s["identity"]

def valid(token): return identity(token) is not None
def allowed(token,permission):
 i=identity(token)
 return bool(i and ("*" in i["permissions"] or permission in i["permissions"]))
def logout(token): SESSIONS.pop(token,None)

def revoke_user(username):
 for t,s in list(SESSIONS.items()):
  if s.get("identity",{}).get("username")==username: SESSIONS.pop(t,None)

def change_admin_password(current,new):
 cfg=load()
 if not verify(current,cfg.get("admin_password_hash","")): raise ValueError("Current password is incorrect")
 cfg["admin_password_hash"]=hash_password(new); save(cfg); revoke_user("admin")

def reset_admin_password(new):
 cfg=load(); cfg["admin_password_hash"]=hash_password(new); save(cfg); revoke_user("admin")
