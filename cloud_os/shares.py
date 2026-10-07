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
    except (OSError,json.JSONDecodeError): return {}

def _save(d):
    APP_DIR.mkdir(parents=True,exist_ok=True)
    t=SHARES.with_suffix('.tmp'); t.write_text(json.dumps(d,indent=2),encoding='utf-8'); t.replace(SHARES)

def _hash(v): return hashlib.sha256(v.encode()).hexdigest()

def create(relative,password='',expires_hours=168,allow_download=True):
    p=safe_path(relative)
    if not p.is_file(): raise FileNotFoundError(relative)
    token=secrets.token_urlsafe(32); now=int(time.time())
    d=_load(); d[token]={'path':relative,'password_hash':_hash(password) if password else '', 'created_at':now,'expires_at':now+max(1,min(int(expires_hours),8760))*3600,'allow_download':bool(allow_download)}; _save(d)
    return {'token':token,'expires_at':d[token]['expires_at'],'protected':bool(password),'allow_download':bool(allow_download)}

def revoke(token):
    d=_load(); ok=token in d
    if ok: d.pop(token); _save(d)
    return ok

def resolve(token,password=''):
    d=_load(); s=d.get(token)
    if not s: return None,'missing'
    if int(s.get('expires_at',0))<int(time.time()): return None,'expired'
    if s.get('password_hash') and not secrets.compare_digest(s['password_hash'],_hash(password)): return None,'password'
    try: p=safe_path(s['path'])
    except ValueError: return None,'missing'
    if not p.is_file(): return None,'missing'
    return (s,p),'ok'

def info(token):
    d=_load(); s=d.get(token)
    if not s or int(s.get('expires_at',0))<int(time.time()): return None
    try: p=safe_path(s['path'])
    except ValueError: return None
    if not p.is_file(): return None
    mime=mimetypes.guess_type(p.name)[0] or 'application/octet-stream'
    ext=p.suffix.lower()
    preview='video' if mime.startswith('video/') else 'audio' if mime.startswith('audio/') else 'image' if mime.startswith('image/') else 'pdf' if ext=='.pdf' else 'text' if ext in {'.txt','.md','.py','.js','.ts','.tsx','.jsx','.json','.yaml','.yml','.toml','.ini','.cfg','.css','.html','.xml','.sh','.ps1','.bat','.c','.cpp','.h','.java','.go','.rs','.sql'} else 'document' if ext in {'.doc','.docx','.odt','.xls','.xlsx','.ods','.ppt','.pptx','.odp'} else 'download'
    return {'name':p.name,'size':p.stat().st_size,'mime':mime,'preview':preview,'protected':bool(s.get('password_hash')),'expires_at':s['expires_at'],'allow_download':bool(s.get('allow_download',True))}
