from __future__ import annotations
import hashlib,json,mimetypes,secrets,time
from pathlib import Path
from .config import APP_DIR
from .files import safe_path
SHARES=APP_DIR/'shares.json'

def _load():
 try:
  d=json.loads(SHARES.read_text(encoding='utf-8')) if SHARES.exists() else {}
  return d if isinstance(d,dict) else {}
 except (OSError,json.JSONDecodeError):return {}
def _save(d):
 APP_DIR.mkdir(parents=True,exist_ok=True);t=SHARES.with_suffix('.tmp');t.write_text(json.dumps(d,indent=2),encoding='utf-8');t.replace(SHARES)
def _hash(v):return hashlib.sha256(v.encode()).hexdigest()
def create(relative,password='',expires_hours=168,allow_download=True):
 p=safe_path(relative)
 if not p.exists() or p==safe_path(''):raise FileNotFoundError(relative)
 token=secrets.token_urlsafe(32);now=int(time.time());d=_load();d[token]={'path':relative,'password_hash':_hash(password) if password else '','created_at':now,'expires_at':now+max(1,min(int(expires_hours),8760))*3600,'allow_download':bool(allow_download)};_save(d)
 return {'token':token,'expires_at':d[token]['expires_at'],'protected':bool(password),'allow_download':bool(allow_download),'kind':'folder' if p.is_dir() else 'file'}
def revoke(token):
 d=_load();ok=token in d
 if ok:d.pop(token);_save(d)
 return ok
def _entry(token):
 s=_load().get(token)
 if not s or int(s.get('expires_at',0))<int(time.time()):return None
 try:p=safe_path(s['path'])
 except ValueError:return None
 return (s,p) if p.exists() else None
def resolve(token,password=''):
 item=_entry(token)
 if not item:return None,'missing'
 s,p=item
 if s.get('password_hash') and not secrets.compare_digest(s['password_hash'],_hash(password)):return None,'password'
 return (s,p),'ok'
def preview_type(p:Path):
 if p.is_dir():return 'folder'
 mime=mimetypes.guess_type(p.name)[0] or 'application/octet-stream';ext=p.suffix.lower()
 return 'video' if mime.startswith('video/') else 'audio' if mime.startswith('audio/') else 'image' if mime.startswith('image/') else 'pdf' if ext=='.pdf' else 'code' if ext in {'.py','.js','.ts','.tsx','.jsx','.json','.yaml','.yml','.toml','.ini','.cfg','.css','.html','.xml','.sh','.ps1','.bat','.c','.cpp','.h','.java','.go','.rs','.sql'} else 'text' if ext in {'.txt','.md','.log','.csv'} else 'document' if ext in {'.docx','.odt','.xlsx','.ods','.pptx','.odp'} else 'download'
def info(token):
 item=_entry(token)
 if not item:return None
 s,p=item;mime='inode/directory' if p.is_dir() else (mimetypes.guess_type(p.name)[0] or 'application/octet-stream')
 return {'name':p.name,'size':0 if p.is_dir() else p.stat().st_size,'mime':mime,'preview':preview_type(p),'kind':'folder' if p.is_dir() else 'file','protected':bool(s.get('password_hash')),'expires_at':s['expires_at'],'allow_download':bool(s.get('allow_download',True))}
def resolve_child(token,child,password=''):
 r,status=resolve(token,password)
 if not r:return None,status
 s,root=r
 if not root.is_dir():return None,'missing'
 try:
  target=(root/child).resolve()
  if target!=root and root.resolve() not in target.parents:return None,'missing'
 except (OSError,ValueError):return None,'missing'
 return ((s,target),'ok') if target.exists() else (None,'missing')
