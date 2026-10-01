from __future__ import annotations
import gc,os
import psutil

def _mode(p):
 try:
  n=p.nice()
  if os.name=="nt": return "boosted" if n==psutil.ABOVE_NORMAL_PRIORITY_CLASS else "normal"
  return "boosted" if int(n)<0 else "normal"
 except (psutil.Error,ValueError,TypeError): return "unknown"

def status():
 p=psutil.Process(); f=psutil.cpu_freq()
 return {"pid":p.pid,"priority":str(p.nice()),"cpu_count":psutil.cpu_count(),"cpu_percent":psutil.cpu_percent(interval=.15),"frequency_mhz":round(f.current,1) if f else None,"mode":_mode(p)}

def boost():
 gc.collect(); p=psutil.Process(); note=""
 try:
  if os.name=="nt": p.nice(psutil.ABOVE_NORMAL_PRIORITY_CLASS)
  else: p.nice(max(-5,int(p.nice())-2))
 except (psutil.Error,PermissionError,OSError,ValueError) as e: note=str(e)
 d=status(); d["applied"]=d["mode"]=="boosted"; d["note"]=note
 return d

def normal():
 p=psutil.Process(); note=""
 try:p.nice(psutil.NORMAL_PRIORITY_CLASS if os.name=="nt" else 0)
 except (psutil.Error,PermissionError,OSError,ValueError) as e: note=str(e)
 d=status(); d["applied"]=d["mode"]=="normal"; d["note"]=note
 return d
