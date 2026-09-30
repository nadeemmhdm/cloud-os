from __future__ import annotations
import hashlib,hmac,secrets,time
from .config import load,save
SESSIONS={}
def hash_password(password,salt=None):
 salt=salt or secrets.token_hex(16); digest=hashlib.pbkdf2_hmac("sha256",password.encode(),bytes.fromhex(salt),310000)
 return salt+":"+digest.hex()
def verify(password,stored):
 try:
  salt,digest=stored.split(":",1); candidate=hash_password(password,salt).split(":",1)[1]
  return hmac.compare_digest(candidate,digest)
 except Exception:return False
def ensure_admin(password):
 cfg=load()
 if not cfg.get("admin_password_hash"): cfg["admin_password_hash"]=hash_password(password); save(cfg)
def login(password,username="admin"):
 cfg=load()
 if username=="admin":
  if not verify(password,cfg.get("admin_password_hash","")): return None
  identity={"username":"admin","role":"owner","permissions":["*"]}
 else:
  from .teams import authenticate,permissions
  u=authenticate(username,password)
  if not u:return None
  identity={"username":username,"role":u.get("role","member"),"permissions":permissions(username)}
 token=secrets.token_urlsafe(32); SESSIONS[token]={"expires":time.time()+43200,"identity":identity}; return token
def identity(token):
 s=SESSIONS.get(token)
 if not s or s["expires"]<time.time(): SESSIONS.pop(token,None); return None
 return s["identity"]
def valid(token): return identity(token) is not None
def allowed(token,permission):
 i=identity(token); return bool(i and ("*" in i["permissions"] or permission in i["permissions"]))
def logout(token): SESSIONS.pop(token,None)
