import platform,time
import psutil
from fastapi import FastAPI,Request
from fastapi.responses import HTMLResponse
from . import __version__
from .api import router,require

app=FastAPI(title="Cloud Os",version=__version__,docs_url=None,redoc_url=None)
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
def health(): return {"status":"ok","version":__version__}

@app.get("/api/system")
def system(req:Request):
 require(req)
 d=psutil.disk_usage("/")
 return {"cpu":psutil.cpu_percent(),"ram":psutil.virtual_memory().percent,"disk":d.percent,"uptime":int(time.time()-BOOT),"platform":platform.system(),"version":__version__}

@app.get("/",response_class=HTMLResponse)
def dashboard():
    from pathlib import Path
    return Path(__file__).with_name("dashboard.html").read_text(encoding="utf-8")
