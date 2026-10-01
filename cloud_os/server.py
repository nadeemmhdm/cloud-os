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
 response.headers["Content-Security-Policy"]="default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"
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
 return """<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Cloud Os</title><style>
*{box-sizing:border-box}body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:#0b0d12;color:#f7f7fa;min-height:100vh}.bg{position:fixed;inset:-30%;background:radial-gradient(circle at 30% 30%,#24304a 0,transparent 32%),radial-gradient(circle at 70% 60%,#27213f 0,transparent 28%);filter:blur(30px);z-index:-1}.shell{display:grid;grid-template-columns:230px 1fr;min-height:100vh}.side{margin:18px;padding:22px;border:1px solid #ffffff14;background:#ffffff09;border-radius:24px}.brand{font-size:21px;font-weight:700;margin-bottom:32px}.dot{display:inline-block;width:10px;height:10px;border-radius:50%;background:#6ee7a8;margin-right:9px}.nav{padding:12px 14px;margin:6px 0;border-radius:14px;color:#c9cbd2}.nav.active{background:#ffffff12;color:white}.main{padding:34px 34px 34px 8px}.muted{color:#969aa6}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:28px}.card{padding:22px;border-radius:22px;border:1px solid #ffffff13;background:#ffffff0b}.value{font-size:34px;font-weight:700;margin:8px 0}.bar{height:7px;background:#ffffff12;border-radius:20px;overflow:hidden}.fill{height:100%;width:0;background:#aab7ff}.wide{grid-column:1/-1}@media(max-width:760px){.shell{display:block}.main{padding:18px}.grid{grid-template-columns:1fr}.wide{grid-column:auto}}</style></head><body><div class="bg"></div><div class="shell"><aside class="side"><div class="brand"><span class="dot"></span>Cloud Os</div><div class="nav active">Overview</div></aside><main class="main"><div><div class="muted">Personal cloud server</div><h1>System overview</h1></div><section class="grid"><div class="card"><span class="muted">CPU</span><div id="cpu" class="value">--%</div><div class="bar"><div id="cpub" class="fill"></div></div></div><div class="card"><span class="muted">Memory</span><div id="ram" class="value">--%</div><div class="bar"><div id="ramb" class="fill"></div></div></div><div class="card"><span class="muted">Storage</span><div id="disk" class="value">--%</div><div class="bar"><div id="diskb" class="fill"></div></div></div><div class="card wide"><span class="muted">Server</span><p id="info" class="muted">Login is required for system metrics.</p></div></section></main></div><script>async function refresh(){try{let r=await fetch('/api/system');if(!r.ok){document.getElementById('info').textContent='Login required to view system metrics.';return}let d=await r.json();for(let k of ['cpu','ram','disk']){document.getElementById(k).textContent=Math.round(d[k])+'%';document.getElementById(k+'b').style.width=d[k]+'%'}document.getElementById('info').textContent=d.platform+' · uptime '+Math.floor(d.uptime/60)+' min · v'+d.version}catch(e){}}refresh();setInterval(refresh,5000)</script></body></html>"""
