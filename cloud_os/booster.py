from __future__ import annotations
import gc
import psutil
from .resource_manager import configure,settings,status as resource_status

def status():
 p=psutil.Process();f=psutil.cpu_freq();r=resource_status();profile=r.get('profile','balanced')
 return {"pid":p.pid,"priority":str(p.nice()),"cpu_count":psutil.cpu_count(),"cpu_percent":psutil.cpu_percent(interval=.10),"frequency_mhz":round(f.current,1) if f else None,"mode":"boosted" if profile=='performance' else "normal","profile":profile,"adaptive":r.get('adaptive',True),"host":r.get('host',{})}

def boost():
 gc.collect();r=configure('performance',True);d=status();d['applied']=r.get('profile')=='performance';d['note']='Performance profile enabled with adaptive host protection.';return d

def normal():
 r=configure('balanced',True);d=status();d['applied']=r.get('profile')=='balanced';d['note']='Balanced profile restored with adaptive host protection.';return d
