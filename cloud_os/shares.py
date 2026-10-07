from __future__ import annotations
import hashlib,json,mimetypes,secrets,time,zipfile,io
from pathlib import Path
from .config import APP_DIR
from .files import safe_path

SHARES=APP_DIR/'shares.json'
TEXT_EXT={'.txt','.md','.py','.js','.ts','.tsx','.jsx','.json','.yaml','.yml','.toml','.ini','.cfg','.css','.html','.xml','.sh','.ps1','.bat','.c','.cpp','.h','.java','.go','.rs','.sql','.log','.csv'}
DOC_EXT={'.doc','.docx','.odt','.xls','.xlsx','.ods','.ppt','.pptx','.odp'}

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
    if not p.exists(): raise FileNotFoundError(relative)
    token=secrets.token_urlsafe(32); now=int(time.time())
    d=_load(); d[token]={'path':relative,'password_hash':_hash(password) if password else '', 'created_at':now,'expires_at':now+max(1,min(int(expires_hours),8760))*3600,'allow_download':bool(allow_download),'directory':p.is_dir()}; _save(d)
    return {'token':token,'expires_at':d[token]['expires_at'],'protected':bool(password),'allow_download':bool(allow_download),'directory':p.is_dir()}

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
    if not p.exists(): return None,'missing'
    return (s,p),'ok'

def _preview_type(p:Path):
    if p.is_dir(): return 'folder'
    mime=mimetypes.guess_type(p.name)[0] or 'application/octet-stream'; ext=p.suffix.lower()
    if mime.startswith('video/'): return 'video'
    if mime.startswith('audio/'): return 'audio'
    if mime.startswith('image/'): return 'image'
    if ext=='.pdf': return 'pdf'
    if ext in TEXT_EXT: return 'text'
    if ext in DOC_EXT: return 'document'
    return 'download'

def info(token):
    d=_load(); s=d.get(token)
    if not s or int(s.get('expires_at',0))<int(time.time()): return None
    try: p=safe_path(s['path'])
    except ValueError: return None
    if not p.exists(): return None
    mime='application/octet-stream' if p.is_dir() else (mimetypes.guess_type(p.name)[0] or 'application/octet-stream')
    size=0 if p.is_dir() else p.stat().st_size
    return {'name':p.name or 'Cloud OS Share','size':size,'mime':mime,'preview':_preview_type(p),'protected':bool(s.get('password_hash')),'expires_at':s['expires_at'],'allow_download':bool(s.get('allow_download',True)),'directory':p.is_dir()}

def folder_items(token,password=''):
    r,status=resolve(token,password)
    if not r:return None,status
    _,p=r
    if not p.is_dir():return None,'not_directory'
    out=[]
    for x in sorted(p.iterdir(),key=lambda q:(not q.is_dir(),q.name.lower())):
        out.append({'name':x.name,'directory':x.is_dir(),'size':0 if x.is_dir() else x.stat().st_size,'preview':_preview_type(x)})
    return out,'ok'

def zip_folder(token,password=''):
    r,status=resolve(token,password)
    if not r:return None,status
    _,p=r
    if not p.is_dir():return None,'not_directory'
    mem=io.BytesIO()
    with zipfile.ZipFile(mem,'w',zipfile.ZIP_DEFLATED) as z:
        for x in p.rglob('*'):
            if x.is_file(): z.write(x,x.relative_to(p))
    mem.seek(0); return mem,'ok'
