import platform,time,shutil,subprocess,os,socket,html
from contextlib import asynccontextmanager
import psutil
from fastapi import FastAPI,Request,Form,HTTPException
from fastapi.responses import HTMLResponse,FileResponse
from . import __version__
from .api import router,require
from .share_api import router as share_router
from .updater import start_update_checker
from .shares import info as share_info,resolve as share_resolve
@asynccontextmanager
async def lifespan(app): start_update_checker();yield
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
def cloud_os_logo():
 from pathlib import Path
 return FileResponse(Path(__file__).with_name('cloud-os-logo.svg'),media_type='image/svg+xml')
@app.get('/share/{token}',response_class=HTMLResponse)
def shared_page(token:str):
 s=share_info(token)
 if not s:raise HTTPException(404,'Share link unavailable or expired')
 n=html.escape(s['name']);gate='<form method="post" action="/share/'+token+'/unlock"><input name="password" type="password" placeholder="Share password" required><button>Unlock preview</button></form>' if s['protected'] else '<a class="btn" href="/share/'+token+'/view">Open preview</a>'
 return '<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+n+' · Cloud OS</title><style>body{margin:0;background:#070910;color:#eef;font:15px system-ui;display:grid;place-items:center;min-height:100vh}.c{width:min(760px,90vw);padding:28px;border:1px solid #ffffff18;border-radius:22px;background:#121624}input,button,.btn{padding:12px;border-radius:10px;border:1px solid #ffffff22;background:#0b0e17;color:white}.btn{display:inline-block;text-decoration:none}form{display:flex;gap:8px;flex-wrap:wrap}.m{color:#9aa4bb}</style></head><body><main class="c"><img src="/cloud-os-logo.svg" width="54"><h1>'+n+'</h1><p class="m">Protected Cloud OS share · '+html.escape(s['preview'])+' preview · expires automatically. Storage path is never exposed.</p>'+gate+'</main></body></html>'
@app.post('/share/{token}/unlock')
def shared_unlock(token:str,password:str=Form(...)):
 r,status=share_resolve(token,password)
 if not r:raise HTTPException(401,'Invalid password or expired link')
 from fastapi.responses import RedirectResponse
 response=RedirectResponse('/share/'+token+'/view',303);response.set_cookie('cloudos_share_'+token,password,httponly=True,samesite='strict',secure=True,max_age=3600,path='/share/'+token);return response
@app.get('/share/{token}/view')
def shared_view(token:str,request:Request):
 s=share_info(token)
 if not s:raise HTTPException(404,'Share unavailable')
 r,status=share_resolve(token,request.cookies.get('cloudos_share_'+token,''))
 if not r:raise HTTPException(401,'Share password required')
 _,p=r;return FileResponse(p,media_type='text/plain' if s['preview']=='text' else s['mime'],content_disposition_type='inline',filename=p.name)
@app.get('/share/{token}/download')
def shared_download(token:str,request:Request):
 s=share_info(token)
 if not s or not s['allow_download']:raise HTTPException(403,'Download disabled')
 r,status=share_resolve(token,request.cookies.get('cloudos_share_'+token,''))
 if not r:raise HTTPException(401,'Share password required')
 _,p=r;return FileResponse(p,filename=p.name)
@app.get('/',response_class=HTMLResponse)
def dashboard():
 from pathlib import Path
 return Path(__file__).with_name('dashboard.html').read_text(encoding='utf-8')
