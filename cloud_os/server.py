import platform,time,shutil,subprocess,os,socket
from contextlib import asynccontextmanager
import psutil
from fastapi import FastAPI,Request
from fastapi.responses import HTMLResponse,FileResponse
from . import __version__
from .api import router,require
from .updater import start_update_checker

@asynccontextmanager
async def lifespan(app):
 start_update_checker()
 yield

app=FastAPI(title="Cloud Os",version=__version__,docs_url=None,redoc_url=None,lifespan=lifespan)
app.include_router(router)
BOOT=time.time()

@app.middleware("http")
async def security_headers(request:Request,call_next):
 response=await call_next(request)
 response.headers["X-Content-Type-Options"]="nosniff"
 response.headers["X-Frame-Options"]="DENY"
 response.headers["Referrer-Policy"]="no-referrer"
 response.headers["Permissions-Policy"]="camera=(), microphone=(), geolocation=()"
 response.headers["Content-Security-Policy"]="default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"
 response.headers["Cache-Control"]="no-store"
 return response

@app.get("/health")
def health(): return {"status":"ok"}

@app.get("/api/system")
def system(req:Request):
 require(req)
 root=os.path.abspath(os.sep) if os.name=="nt" else "/"
 d=psutil.disk_usage(root)
 return {"cpu":psutil.cpu_percent(),"ram":psutil.virtual_memory().percent,"disk":d.percent,"uptime":int(time.time()-BOOT),"platform":platform.system(),"version":__version__}

@app.get("/api/system/details")
def system_details(req:Request):
 require(req)
 vm=psutil.virtual_memory()
 drives=[]
 try:
  for p in psutil.disk_partitions(all=False):
   try:
    u=psutil.disk_usage(p.mountpoint)
    drives.append({"device":p.device,"mount":p.mountpoint,"total":u.total,"used":u.used,"free":u.free})
   except (PermissionError,OSError): pass
 except Exception: pass
 gpu="Unavailable"
 try:
  if os.name=="nt":
   r=subprocess.run(["powershell","-NoLogo","-NoProfile","-NonInteractive","-Command","(Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name) -join ', '"],capture_output=True,text=True,timeout=5,shell=False)
   if r.returncode==0 and r.stdout.strip(): gpu=r.stdout.strip()
  elif shutil.which("lspci"):
   r=subprocess.run(["lspci"],capture_output=True,text=True,timeout=5,shell=False)
   names=[x.split(":",2)[-1].strip() for x in r.stdout.splitlines() if any(k in x.lower() for k in ("vga compatible controller","3d controller","display controller"))]
   if names: gpu=", ".join(names)
 except Exception: pass
 ips=[]
 try:
  for info in socket.getaddrinfo(socket.gethostname(),None,socket.AF_INET):
   ip=info[4][0]
   if ip and not ip.startswith("127.") and ip not in ips: ips.append(ip)
 except OSError: pass
 return {
  "system_name":platform.node() or "Unknown",
  "ip_addresses":ips,
  "os":platform.system(),
  "os_release":platform.release(),
  "os_version":platform.version(),
  "architecture":platform.machine(),
  "processor":platform.processor() or "Unknown",
  "cpu_physical_cores":psutil.cpu_count(logical=False),
  "cpu_logical_cores":psutil.cpu_count(logical=True),
  "ram_total":vm.total,
  "ram_available":vm.available,
  "graphics":gpu,
  "python":platform.python_version(),
  "cloud_os_version":__version__,
  "drives":drives
 }

@app.get("/cloud-os-logo.svg")
def cloud_os_logo():
 from pathlib import Path
 return FileResponse(Path(__file__).with_name("cloud-os-logo.svg"),media_type="image/svg+xml")

def _dashboard_html():
 from pathlib import Path
 html=Path(__file__).with_name("dashboard.html").read_text(encoding="utf-8")
 # Labs is deliberately injected at delivery time so it stays isolated from the
 # core dashboard bundle while the section is only a preview.
 html=html.replace('const pages=["overview","files","terminal","backups","users","audit","integrations","settings"]', 'const pages=["overview","files","terminal","backups","users","audit","integrations","labs","settings"]',1)
 html=html.replace("settings:'<svg", "labs:'<svg class=\"navico\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.7\"><path d=\"M9 3h6M10 3v5l-5 9a3 3 0 0 0 2.6 4h8.8a3 3 0 0 0 2.6-4l-5-9V3M8 15h8\"/></svg>',settings:'<svg",1)
 html=html.replace('({overview,files,terminal,backups,users,audit,integrations,settings}[p])()', '({overview,files,terminal,backups,users,audit,integrations,labs,settings}[p])()',1)
 anchor='async function settings(tab="account")'
 labs='function labs(){q("#content").innerHTML=\'<div class="card glass wide" style="min-height:420px;display:grid;place-items:center;text-align:center"><div style="max-width:560px"><div style="width:64px;height:64px;margin:0 auto 18px;border-radius:20px;display:grid;place-items:center;background:#788deb18;border:1px solid #788deb38;font-size:28px">◈</div><div class="small" style="text-transform:uppercase;letter-spacing:.14em;color:#aeb8ff">Cloud OS Labs</div><h2 style="font-size:clamp(28px,5vw,44px);margin:10px 0">Coming soon</h2><p class="muted" style="line-height:1.7">Experimental Cloud OS features will appear here before they graduate into the main workspace. Labs is currently in preview and has no experimental features enabled.</p><span class="roleBadge" style="margin-top:12px">Preview</span></div></div>\'}async function settings(tab="account")'
 if anchor in html:
  html=html.replace(anchor,labs,1)
 return html

@app.get("/",response_class=HTMLResponse)
def dashboard():
 return _dashboard_html()
