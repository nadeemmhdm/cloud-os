import platform,time,shutil,subprocess,os,socket,html,zipfile,re
from pathlib import Path
from urllib.parse import quote
from contextlib import asynccontextmanager
import psutil
from fastapi import FastAPI,Request,Form,HTTPException
from fastapi.responses import HTMLResponse,FileResponse
from . import __version__
from .api import router,require
from .share_api import router as share_router
from .updater import start_update_checker
from .shares import info as share_info,resolve as share_resolve,resolve_child,preview_type
from .config import load
@asynccontextmanager
async def lifespan(app):start_update_checker();yield
app=FastAPI(title='Cloud Os',version=__version__,docs_url=None,redoc_url=None,lifespan=lifespan);app.include_router(router);app.include_router(share_router);BOOT=time.time()
@app.middleware('http')
async def security_headers(request:Request,call_next):
 response=await call_next(request);response.headers['X-Content-Type-Options']='nosniff';response.headers['X-Frame-Options']='DENY';response.headers['Referrer-Policy']='no-referrer';response.headers['Permissions-Policy']='camera=(), microphone=(), geolocation=()';response.headers['Content-Security-Policy']="default-src 'self'; img-src 'self' data: blob:; media-src 'self' blob:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'";response.headers['Cache-Control']='no-store';return response
@app.get('/health')
def health():return {'status':'ok'}
@app.get('/api/system')
def system(req:Request):require(req);root=os.path.abspath(os.sep) if os.name=='nt' else '/';d=psutil.disk_usage(root);return {'cpu':psutil.cpu_percent(),'ram':psutil.virtual_memory().percent,'disk':d.percent,'uptime':int(time.time()-BOOT),'platform':platform.system(),'version':__version__}
@app.get('/api/system/details')
def system_details(req:Request):
 require(req);vm=psutil.virtual_memory();drives=[]
 try:
  for p in psutil.disk_partitions(all=False):
   try:u=psutil.disk_usage(p.mountpoint);drives.append({'device':p.device,'mount':p.mountpoint,'total':u.total,'used':u.used,'free':u.free})
   except (PermissionError,OSError):pass
 except Exception:pass
 gpu='Unavailable'
 try:
  if os.name=='nt':
   r=subprocess.run(['powershell','-NoLogo','-NoProfile','-NonInteractive','-Command',"(Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name) -join ', '"],capture_output=True,text=True,timeout=5,shell=False)
   if r.returncode==0 and r.stdout.strip():gpu=r.stdout.strip()
 except Exception:pass
 ips=[]
 try:
  for inf in socket.getaddrinfo(socket.gethostname(),None,socket.AF_INET):
   ip=inf[4][0]
   if ip and not ip.startswith('127.') and ip not in ips:ips.append(ip)
 except OSError:pass
 return {'system_name':platform.node() or 'Unknown','ip_addresses':ips,'os':platform.system(),'os_release':platform.release(),'os_version':platform.version(),'architecture':platform.machine(),'processor':platform.processor() or 'Unknown','cpu_physical_cores':psutil.cpu_count(logical=False),'cpu_logical_cores':psutil.cpu_count(logical=True),'ram_total':vm.total,'ram_available':vm.available,'graphics':gpu,'python':platform.python_version(),'cloud_os_version':__version__,'drives':drives}
@app.get('/cloud-os-logo.svg')
def cloud_os_logo():return FileResponse(Path(__file__).with_name('cloud-os-logo.svg'),media_type='image/svg+xml')
@app.get('/share-ui.js')
def share_ui():return FileResponse(Path(__file__).with_name('share-ui.js'),media_type='application/javascript')
def _share_password(request,token):return request.cookies.get('cloudos_share_'+token,'')
def _doc_text(p:Path):
 ext=p.suffix.lower()
 if ext not in {'.docx','.xlsx','.pptx','.odt','.ods','.odp'}:return ''
 try:
  with zipfile.ZipFile(p) as z:
   names=z.namelist();wanted=[]
   if ext=='.docx':wanted=[n for n in names if n=='word/document.xml']
   elif ext=='.xlsx':wanted=[n for n in names if n.startswith('xl/worksheets/sheet') or n=='xl/sharedStrings.xml']
   elif ext=='.pptx':wanted=[n for n in names if n.startswith('ppt/slides/slide') and n.endswith('.xml')]
   else:wanted=[n for n in names if n=='content.xml']
   chunks=[]
   for n in wanted[:80]:
    raw=z.read(n).decode('utf-8','replace');text=re.sub(r'<[^>]+>',' ',raw);text=html.unescape(re.sub(r'\s+',' ',text)).strip()
    if text:chunks.append(text)
   return '\n\n'.join(chunks)[:2_000_000]
 except (OSError,zipfile.BadZipFile,KeyError):return ''
def _share_shell(title,body):
 return '<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+html.escape(title)+' · Cloud OS</title><style>body{margin:0;background:#070910;color:#eef;font:15px system-ui}.wrap{width:min(1050px,92vw);margin:35px auto}.c{padding:24px;border:1px solid #ffffff18;border-radius:22px;background:#121624}.top{display:flex;align-items:center;gap:14px;margin-bottom:20px}.m{color:#9aa4bb}.btn,button,input{padding:11px 13px;border-radius:10px;border:1px solid #ffffff22;background:#0b0e17;color:white}.btn{display:inline-block;text-decoration:none}.files{display:grid;gap:8px}.file{display:flex;justify-content:space-between;gap:12px;padding:12px;border:1px solid #ffffff12;border-radius:12px;text-decoration:none;color:white}.viewer{width:100%;max-height:72vh;border:0;border-radius:14px;background:#05070c}video.viewer{height:auto}img.viewer{object-fit:contain}pre{white-space:pre-wrap;overflow:auto;max-height:72vh;padding:18px;background:#05070c;border-radius:14px;font:13px ui-monospace,monospace}.actions{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}</style></head><body><main class="wrap"><div class="c"><div class="top"><img src="/cloud-os-logo.svg" width="48"><div><b>Cloud OS protected share</b><div class="m">Storage location is private</div></div></div>'+body+'</div></main></body></html>'
@app.get('/share/{token}',response_class=HTMLResponse)
def shared_page(token:str):
 s=share_info(token)
 if not s:raise HTTPException(404,'Share link unavailable or expired')
 n=html.escape(s['name']);gate='<form method="post" action="/share/'+token+'/unlock"><input name="password" type="password" placeholder="Share password" required><button>Unlock preview</button></form>' if s['protected'] else '<a class="btn" href="/share/'+token+'/view">Open preview</a>'
 return _share_shell(s['name'],'<h1>'+n+'</h1><p class="m">'+html.escape(s['kind'].title())+' · '+html.escape(s['preview'])+' preview · expires automatically.</p>'+gate)
@app.post('/share/{token}/unlock')
def shared_unlock(token:str,password:str=Form(...)):
 r,status=share_resolve(token,password)
 if not r:raise HTTPException(401,'Invalid password or expired link')
 from fastapi.responses import RedirectResponse
 response=RedirectResponse('/share/'+token+'/view',303);response.set_cookie('cloudos_share_'+token,password,httponly=True,samesite='strict',secure=bool(load().get('secure_cookies')),max_age=3600,path='/share/'+token);return response
def _render_shared(token,p:Path,s,child=''):
 kind=preview_type(p);name=html.escape(p.name)
 if p.is_dir():
  rows=[]
  for x in sorted(p.iterdir(),key=lambda v:(not v.is_dir(),v.name.lower())):
   rel=(child.rstrip('/')+'/' if child else '')+x.name;rows.append('<a class="file" href="/share/'+token+'/view?path='+quote(rel)+'"><span>'+('Folder · ' if x.is_dir() else '')+html.escape(x.name)+'</span><span class="m">Open</span></a>')
  return HTMLResponse(_share_shell(p.name,'<h1>'+name+'</h1><p class="m">Read-only shared folder. Internal server/storage path is not exposed.</p><div class="files">'+''.join(rows)+'</div>'))
 raw='/share/'+token+'/raw'+(('?path='+quote(child)) if child else '');dl='/share/'+token+'/download'+(('?path='+quote(child)) if child else '');actions='<div class="actions"><a class="btn" href="'+raw+'">Open raw</a>'+(('<a class="btn" href="'+dl+'">Download</a>') if s.get('allow_download',True) else '')+'</div>'
 if kind=='video':body='<video class="viewer" controls preload="metadata" src="'+raw+'"></video>'
 elif kind=='audio':body='<audio controls src="'+raw+'"></audio>'
 elif kind=='image':body='<img class="viewer" src="'+raw+'">'
 elif kind=='pdf':body='<iframe class="viewer" style="height:75vh" src="'+raw+'"></iframe>'
 elif kind=='document':body='<pre>'+html.escape(_doc_text(p) or 'Preview text is unavailable for this document. Download the file to open it in its native application.')+'</pre>'
 elif kind in {'text','code'}:
  try:text=p.read_text(encoding='utf-8')[:2_000_000]
  except (UnicodeDecodeError,OSError):text='Preview unavailable.'
  copy='<button id="copy">Copy code</button><script>document.getElementById("copy").onclick=()=>navigator.clipboard.writeText(document.getElementById("code").innerText)</script>' if kind=='code' else '';body=copy+'<pre id="code">'+html.escape(text)+'</pre>'
 else:body='<p class="m">No browser preview is available for this file type.</p>'
 return HTMLResponse(_share_shell(p.name,'<h1>'+name+'</h1>'+actions+body))
@app.get('/share/{token}/view')
def shared_view(token:str,request:Request,path:str=''):
 s=share_info(token)
 if not s:raise HTTPException(404,'Share unavailable')
 r,status=(resolve_child(token,path,_share_password(request,token)) if path else share_resolve(token,_share_password(request,token)))
 if not r:raise HTTPException(401 if status=='password' else 404,'Share password required' if status=='password' else 'Shared item unavailable')
 _,p=r;return _render_shared(token,p,s,path)
@app.get('/share/{token}/raw')
def shared_raw(token:str,request:Request,path:str=''):
 s=share_info(token)
 if not s:raise HTTPException(404,'Share unavailable')
 r,status=(resolve_child(token,path,_share_password(request,token)) if path else share_resolve(token,_share_password(request,token)))
 if not r:raise HTTPException(401 if status=='password' else 404,'Share access denied')
 _,p=r
 if not p.is_file():raise HTTPException(400,'Not a file')
 return FileResponse(p,content_disposition_type='inline')
@app.get('/share/{token}/download')
def shared_download(token:str,request:Request,path:str=''):
 s=share_info(token)
 if not s or not s['allow_download']:raise HTTPException(403,'Download disabled')
 r,status=(resolve_child(token,path,_share_password(request,token)) if path else share_resolve(token,_share_password(request,token)))
 if not r:raise HTTPException(401 if status=='password' else 404,'Share access denied')
 _,p=r
 if not p.is_file():raise HTTPException(400,'Folders are preview-only')
 return FileResponse(p,filename=p.name)
@app.get('/',response_class=HTMLResponse)
def dashboard():
 page=Path(__file__).with_name('dashboard.html').read_text(encoding='utf-8')
 return page.replace('</body>','<script src="/share-ui.js"></script></body>')
