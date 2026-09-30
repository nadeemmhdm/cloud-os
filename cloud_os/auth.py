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
def login(password):
 cfg=load()
 if not verify(password,cfg.get("admin_password_hash","")): return None
 token=secrets.token_urlsafe(32); SESSIONS[token]=time.time()+43200; return token
def valid(token):
 exp=SESSIONS.get(token,0)
 if exp<time.time(): SESSIONS.pop(token,None); return False
 return True
def logout(token): SESSIONS.pop(token,None)
