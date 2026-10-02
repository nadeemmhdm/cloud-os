from __future__ import annotations
import hashlib,hmac,secrets,time
from datetime import datetime,timezone
from collections import defaultdict, deque
from .config import load,save

SESSIONS={}
_ATTEMPTS=defaultdict(deque)
_LOCKED_UNTIL={}
WINDOW=900
LOCK_THRESHOLD=5
MAX_LOCK_SECONDS=900

def _cooldown_seconds(failures):
 return min(MAX_LOCK_SECONDS,2 ** max(1,failures-4))

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
