from __future__ import annotations
import gc,os,platform
import psutil

def status():
 p=psutil.Process()
 f=psutil.cpu_freq()
 return {"pid":p.pid,"priority":str(p.nice()),"cpu_count":psutil.cpu_count(),"cpu_percent":psutil.cpu_percent(interval=.15),"frequency_mhz":round(f.current,1) if f else None,"mode":"normal"}
def boost():
 gc.collect()
 p=psutil.Process(); applied=False; note=""
 try:
  if os.name=="nt":
   p.nice(psutil.ABOVE_NORMAL_PRIORITY_CLASS); applied=True
  else:
   current=p.nice()
   target=max(-5,current-2)
   p.nice(target); applied=True
 except (psutil.Error,PermissionError,OSError) as e: note=str(e)
 d=status(); d["mode"]="boosted" if applied else "normal"; d["applied"]=applied; d["note"]=note
 return d
def normal():
 p=psutil.Process()
 try:p.nice(psutil.NORMAL_PRIORITY_CLASS if os.name=="nt" else 0)
 except (psutil.Error,PermissionError,OSError) as e:return {**status(),"applied":False,"note":str(e)}
 return {**status(),"mode":"normal","applied":True,"note":""}
