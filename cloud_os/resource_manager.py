from __future__ import annotations
import json,os,threading,time
from pathlib import Path
import psutil
from .config import APP_DIR

STATE_FILE=APP_DIR/"resource-manager.json"
_LOCK=threading.RLock();_STOP=threading.Event();_THREAD=None
PROFILES={
 "eco":{"cpu_fraction":0.25,"memory_soft_mb":1536,"workers":1,"priority":"low"},
 "balanced":{"cpu_fraction":0.50,"memory_soft_mb":2048,"workers":2,"priority":"below-normal"},
 "performance":{"cpu_fraction":0.75,"memory_soft_mb":3072,"workers":4,"priority":"normal"},
}
CRITICAL_WINDOWS={"system","system idle process","registry","memory compression","smss.exe","csrss.exe","wininit.exe","winlogon.exe","services.exe","lsass.exe","svchost.exe","dwm.exe","fontdrvhost.exe"}
CRITICAL_LINUX={"systemd","init","kthreadd","kworker","dbus-daemon","networkmanager","systemd-journald","systemd-logind","sshd"}

def _read():
 try:
  d=json.loads(STATE_FILE.read_text(encoding="utf-8"));return d if isinstance(d,dict) else {}
 except (OSError,json.JSONDecodeError):return {}
def _write(d):
 STATE_FILE.parent.mkdir(parents=True,exist_ok=True);tmp=STATE_FILE.with_suffix('.tmp');tmp.write_text(json.dumps(d,indent=2,sort_keys=True),encoding='utf-8');tmp.replace(STATE_FILE)
 if os.name!='nt':
  try:STATE_FILE.chmod(0o600)
  except OSError:pass

def settings():
 d=_read();p=str(d.get('profile','balanced')).lower()
 if p not in PROFILES:p='balanced'
 return {"profile":p,"adaptive":bool(d.get('adaptive',True)),"auto_block":[str(x).lower() for x in d.get('auto_block',[]) if str(x).strip()]}
def configure(profile:str|None=None,adaptive:bool|None=None):
 with _LOCK:
  d=settings()
  if profile is not None:
   profile=profile.lower().strip()
   if profile not in PROFILES:raise ValueError('profile must be eco, balanced, or performance')
   d['profile']=profile
  if adaptive is not None:d['adaptive']=bool(adaptive)
  _write(d);apply_profile(d['profile']);return status()

def _cloud_process(p:psutil.Process):
 try:
  if p.pid==os.getpid():return True
  cmd=' '.join(p.cmdline()).lower()
  return 'cloud_os' in cmd or 'cloud-os' in cmd
 except psutil.Error:return False

def _critical_name(name:str):
 n=(name or '').lower()
 if os.name=='nt':return n in CRITICAL_WINDOWS
 return n in CRITICAL_LINUX or n.startswith(('kworker','migration/','watchdog/','rcu_'))

def classify_process(p:psutil.Process):
 try:
  name=p.name();user=p.username() or ''
  if _cloud_process(p):return 'cloud_os'
  if _critical_name(name):return 'critical_system'
  current=(psutil.Process().username() or '').lower()
  if user.lower()!=current:return 'system_or_other_user'
  return 'user_app'
 except (psutil.Error,OSError):return 'protected_unknown'

def process_list(limit:int=200):
 rows=[]
 for p in psutil.process_iter(['pid','name','username','cpu_percent','memory_info']):
  try:
   info=p.info;rows.append({"pid":p.pid,"name":info.get('name') or '',"username":info.get('username') or '',"cpu_percent":float(info.get('cpu_percent') or 0),"memory_mb":round((info.get('memory_info').rss if info.get('memory_info') else 0)/1048576,1),"class":classify_process(p)})
  except (psutil.Error,AttributeError):continue
 rows.sort(key=lambda x:(x['cpu_percent'],x['memory_mb']),reverse=True);return rows[:max(1,min(limit,500))]

def _set_priority(p:psutil.Process,level:str):
 if os.name=='nt':
  value={"low":psutil.IDLE_PRIORITY_CLASS,"below-normal":psutil.BELOW_NORMAL_PRIORITY_CLASS,"normal":psutil.NORMAL_PRIORITY_CLASS}.get(level,psutil.BELOW_NORMAL_PRIORITY_CLASS)
  p.nice(value)
 else:p.nice({"low":15,"below-normal":8,"normal":0}.get(level,8))

def _set_io_priority(p:psutil.Process,level:str):
 try:
  if os.name=='nt' and hasattr(psutil,'IOPRIO_VERYLOW'):p.ionice(psutil.IOPRIO_VERYLOW if level!='normal' else psutil.IOPRIO_NORMAL)
  elif os.name!='nt' and hasattr(psutil,'IOPRIO_CLASS_IDLE'):
   p.ionice(psutil.IOPRIO_CLASS_IDLE if level=='low' else psutil.IOPRIO_CLASS_BE if level=='below-normal' else psutil.IOPRIO_CLASS_NONE,value=0)
 except (psutil.Error,ValueError,AttributeError):pass

def _affinity_for_fraction(p:psutil.Process,fraction:float):
 try:
  available=p.cpu_affinity();count=max(1,round(len(available)*max(.1,min(1.0,fraction))));p.cpu_affinity(available[:count]);return count
 except (psutil.Error,AttributeError,ValueError):return None

def apply_profile(profile:str|None=None):
 cfg=settings();name=(profile or cfg['profile']).lower();spec=PROFILES[name];p=psutil.Process();note=[]
 try:_set_priority(p,spec['priority'])
 except (psutil.Error,PermissionError,OSError,ValueError) as e:note.append(str(e))
 _set_io_priority(p,spec['priority']);cores=_affinity_for_fraction(p,spec['cpu_fraction'])
 return {"profile":name,"cpu_fraction":spec['cpu_fraction'],"memory_soft_mb":spec['memory_soft_mb'],"workers":spec['workers'],"affinity_cores":cores,"note":"; ".join(note)}

def host_pressure():
 vm=psutil.virtual_memory();cpu=psutil.cpu_percent(interval=.10);disk=None
 try:disk=psutil.disk_usage(str(APP_DIR.anchor or Path.cwd())).percent
 except OSError:pass
 return {"cpu_percent":round(cpu,1),"memory_percent":round(vm.percent,1),"available_mb":round(vm.available/1048576,1),"disk_percent":disk,"high":cpu>=90 or vm.available<1024*1024*1024 or vm.percent>=92}

def status():
 cfg=settings();p=psutil.Process();rss=0
 try:rss=round(p.memory_info().rss/1048576,1)
 except psutil.Error:pass
 try:aff=p.cpu_affinity()
 except (psutil.Error,AttributeError):aff=[]
 return {**cfg,"policy":PROFILES[cfg['profile']],"cloud_os":{"pid":p.pid,"memory_mb":rss,"affinity":aff,"classification":classify_process(p)},"host":host_pressure(),"guard_running":bool(_THREAD and _THREAD.is_alive())}

def add_block(name:str):
 n=Path(name.strip()).name.lower()
 if not n or _critical_name(n):raise ValueError('critical or empty process name cannot be blocked')
 with _LOCK:
  d=settings();items=set(d['auto_block']);items.add(n);d['auto_block']=sorted(items);_write(d)
 return settings()
def remove_block(name:str):
 n=Path(name.strip()).name.lower()
 with _LOCK:
  d=settings();items=set(d['auto_block']);items.discard(n);d['auto_block']=sorted(items);_write(d)
 return settings()

def process_action(pid:int,action:str):
 if pid in (0,1,4,os.getpid()):raise PermissionError('protected process cannot be changed')
 try:p=psutil.Process(int(pid))
 except (psutil.NoSuchProcess,ValueError):raise FileNotFoundError(pid)
 cls=classify_process(p)
 if cls!='user_app':raise PermissionError(f'process class {cls} is protected')
 action=action.lower().strip()
 if action=='lower_priority':_set_priority(p,'low');_set_io_priority(p,'low')
 elif action=='suspend':p.suspend()
 elif action=='resume':p.resume()
 elif action=='terminate':p.terminate()
 else:raise ValueError('action must be lower_priority, suspend, resume, or terminate')
 return {"pid":pid,"name":p.name() if p.is_running() else '',"action":action,"class":cls,"ok":True}

def _enforce_blocklist():
 blocked=set(settings()['auto_block'])
 if not blocked:return 0
 killed=0
 for p in psutil.process_iter(['name']):
  try:
   if (p.info.get('name') or '').lower() in blocked and classify_process(p)=='user_app':p.terminate();killed+=1
  except psutil.Error:continue
 return killed

def guard_once():
 cfg=settings();pressure=host_pressure();result={"pressure":pressure,"blocked_terminated":_enforce_blocklist()}
 if cfg['adaptive']:
  if pressure['high']:
   p=psutil.Process()
   try:_set_priority(p,'low')
   except psutil.Error:pass
   result['adaptive_action']='throttled'
  else:
   apply_profile(cfg['profile']);result['adaptive_action']='profile-restored'
 return result

def _loop(interval:float):
 while not _STOP.wait(interval):
  try:guard_once()
  except Exception:pass

def start_guard(interval:float=10.0):
 global _THREAD
 with _LOCK:
  if _THREAD and _THREAD.is_alive():return _THREAD
  _STOP.clear();apply_profile();_THREAD=threading.Thread(target=_loop,args=(max(3.0,float(interval)),),name='cloud-os-resource-guard',daemon=True);_THREAD.start();return _THREAD

def stop_guard():_STOP.set()
