from __future__ import annotations
import json,os,re,shutil,threading,time,uuid
from datetime import datetime,timezone
from pathlib import Path
from .config import APP_DIR
from .lab_defs_common import MODULES
from .lab_defs_m1 import LABS as M1
from .lab_defs_m2 import LABS as M2
from .lab_defs_m3 import LABS as M3
from .lab_defs_m4 import LABS as M4
from .lab_defs_m5 import LABS as M5
from .lab_defs_challenges import LABS as CHALLENGES
LABS=[*M1,*M2,*M3,*M4,*M5,*CHALLENGES];LAB_BY_ID={x["id"]:x for x in LABS}
LABS_HOME=APP_DIR/"labs";RUNTIME_HOME=LABS_HOME/"runtime";PROGRESS_FILE=LABS_HOME/"progress.json";SETTINGS_FILE=LABS_HOME/"settings.json";_LOCK=threading.RLock();_MAX_COMMAND=512;_RATE_LIMIT=30;_RATE_WINDOW=10.0

def _now():return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
def _json(path,default):
 try:
  v=json.loads(path.read_text(encoding='utf-8'));return v if isinstance(v,type(default)) else default
 except (OSError,json.JSONDecodeError):return default
def _save(path,data):
 path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(data,indent=2,sort_keys=True),encoding='utf-8');tmp.replace(path)
 if os.name!='nt':
  try:path.chmod(0o600)
  except OSError:pass
def _ensure():LABS_HOME.mkdir(parents=True,exist_ok=True);RUNTIME_HOME.mkdir(parents=True,exist_ok=True)
def _settings():
 d=_json(SETTINGS_FILE,{});return {"disabled":[x for x in d.get('disabled',[]) if x in LAB_BY_ID]}
def set_enabled(lab_id,enabled):
 if lab_id not in LAB_BY_ID:raise KeyError(lab_id)
 with _LOCK:
  d=set(_settings()['disabled']);d.discard(lab_id) if enabled else d.add(lab_id);_save(SETTINGS_FILE,{"disabled":sorted(d)})
 return {"lab_id":lab_id,"enabled":enabled}
def _all_progress():return _json(PROGRESS_FILE,{})
def user_progress(username):
 d=_all_progress().get(username.lower(),{});return d if isinstance(d,dict) else {}
def _touch(username,lab_id,**updates):
 with _LOCK:
  a=_all_progress();u=a.setdefault(username.lower(),{});p=u.setdefault(lab_id,{"status":"Not Started","attempts":0,"best_score":0,"completion_time":None,"last_opened":None});p.update(updates);_save(PROGRESS_FILE,a);return dict(p)
def reset_user_progress(username):
 with _LOCK:
  a=_all_progress();a.pop(username.lower(),None);_save(PROGRESS_FILE,a)
def _root(sid):
 if not re.fullmatch(r'[a-f0-9]{32}',sid or ''):raise ValueError('invalid session id')
 r=RUNTIME_HOME.resolve();p=(r/sid).resolve()
 if p.parent!=r:raise ValueError('sandbox path violation')
 return p
def _state_path(sid):return _root(sid)/'state'/'session.json'
def _read_state(sid):
 p=_state_path(sid)
 if not p.exists():raise FileNotFoundError(sid)
 d=_json(p,{})
 if not d:raise RuntimeError('lab session state is corrupt')
 return d
def _write_state(s):_save(_state_path(s['session_id']),s)
def _owned(s,u):
 if s.get('username','').lower()!=u.lower():raise PermissionError('session belongs to another user')
def active_sessions(username):
 _ensure();out={}
 for p in RUNTIME_HOME.iterdir():
  if not p.is_dir() or p.is_symlink():continue
  try:
   s=_read_state(p.name)
   if s.get('username','').lower()==username.lower() and s.get('status') in {'running','paused'}:out[s['lab_id']]={"session_id":s['session_id'],"status":s['status']}
  except Exception:pass
 return out
def session_view(s,commands=False):
 d={k:s.get(k) for k in ('session_id','lab_id','status','started_at','updated_at','score')};d['marks']=list(s.get('marks',[]));d['lab']=LAB_BY_ID[s['lab_id']]
 if commands:d['available_commands']=[c['cmd'] for c in d['lab']['commands']]
 return d
def start_lab(lab_id,username):
 _ensure()
 if lab_id not in LAB_BY_ID:raise KeyError(lab_id)
 if lab_id in set(_settings()['disabled']):raise RuntimeError('lab is disabled')
 old=active_sessions(username).get(lab_id)
 if old:
  try:exit_lab(old['session_id'],username)
  except Exception:pass
 sid=uuid.uuid4().hex;r=_root(sid)
 for x in ('filesystem','logs','config','state','output'):(r/x).mkdir(parents=True,exist_ok=True)
 (r/'filesystem'/'README.txt').write_text('Cloud OS LAB SANDBOX\nSynthetic training data only.\n',encoding='utf-8');(r/'logs'/'security.log').write_text('2026-10-07T19:30:12Z AUTH_FAILURE user=developer source=10.10.1.45\n2026-10-07T19:31:02Z PORT_SCAN source=10.10.9.77 target=web-01\n',encoding='utf-8')
 s={"session_id":sid,"lab_id":lab_id,"username":username,"status":"running","started_at":_now(),"updated_at":_now(),"marks":[],"history":[],"times":[],"score":0};_write_state(s);p=user_progress(username).get(lab_id,{});_touch(username,lab_id,status='In Progress',attempts=int(p.get('attempts',0))+1,last_opened=_now());return session_view(s,True)
def get_session(sid,username):s=_read_state(sid);_owned(s,username);return session_view(s,True)
def _norm(c):return ' '.join(c.strip().split()).lower()
def _unsafe(c):
 if not isinstance(c,str) or not c.strip() or len(c)>_MAX_COMMAND:return True
 low=c.lower();blocked=['..','&&','||',';','`','$(', '>', '<','file://','http://','https://']
 return any(x in low for x in blocked) or c.strip().startswith(('/','\\')) or bool(re.match(r'^[A-Za-z]:[\\/]',c.strip()))
def run_command(sid,username,command):
 if _unsafe(command):raise PermissionError('unsafe command blocked')
 with _LOCK:
  s=_read_state(sid);_owned(s,username)
  if s.get('status')!='running':raise RuntimeError('lab is not running')
  now=time.time();times=[x for x in s.get('times',[]) if now-float(x)<=_RATE_WINDOW]
  if len(times)>=_RATE_LIMIT:raise RuntimeError('lab command rate limit exceeded')
  times.append(now);s['times']=times[-_RATE_LIMIT:];lab=LAB_BY_ID[s['lab_id']];n=_norm(command)
  if n in {'help','?'}:out='LAB SANDBOX\nAllowed commands:\n'+'\n'.join('  '+c['cmd'] for c in lab['commands'])+'\n  pwd\n  ls\n  cat README.txt\n  cat security.log\n  verify\n  clear\n  exit'
  elif n=='pwd':out='/lab-sandbox'
  elif n=='ls':out='README.txt  security.log  state/'
  elif n=='cat readme.txt':out='Cloud OS LAB SANDBOX\nSynthetic training data only.'
  elif n=='cat security.log':out='2026-10-07T19:30:12Z AUTH_FAILURE user=developer source=10.10.1.45\n2026-10-07T19:31:02Z PORT_SCAN source=10.10.9.77 target=web-01'
  else:
   m=next((x for x in lab['commands'] if _norm(x['cmd'])==n),None)
   if not m:out="LAB-1005 Unsafe or unsupported command blocked. Run 'help'."
   else:
    out=m['output']
    if m.get('mark') and m['mark'] not in s['marks']:s['marks'].append(m['mark'])
  out=out[:12000];s['history']=(s.get('history',[])+[{"at":_now(),"command":command[:_MAX_COMMAND],"output":out}])[-100:];s['updated_at']=_now();_write_state(s);return {"output":out,"status":s['status'],"marks":s['marks']}
def verify_lab(sid,username):
 with _LOCK:
  s=_read_state(sid);_owned(s,username);lab=LAB_BY_ID[s['lab_id']];marks=set(s.get('marks',[]));res=[];earned=total=0
  for t in lab['tasks']:
   total+=t['points'];ok=t['required'] in marks;earned+=t['points'] if ok else 0;res.append({"id":t['id'],"title":t['title'],"status":"PASS" if ok else "FAIL","points":t['points'] if ok else 0,"hint":None if ok else t['hint'],"explanation":"Requirement satisfied in current sandbox state." if ok else t['failure']})
  score=round(100*earned/max(1,total));s['score']=score;s['updated_at']=_now();_write_state(s);p=user_progress(username).get(s['lab_id'],{});_touch(username,s['lab_id'],best_score=max(int(p.get('best_score',0)),score),last_opened=_now());return {"passed":all(x['status']=='PASS' for x in res),"score":score,"completed":sum(x['status']=='PASS' for x in res),"total":len(res),"results":res}
def pause_lab(sid,u):s=_read_state(sid);_owned(s,u);s['status']='paused';s['updated_at']=_now();_write_state(s);return session_view(s)
def resume_lab(sid,u):s=_read_state(sid);_owned(s,u);s['status']='running';s['updated_at']=_now();_write_state(s);return session_view(s)
def exit_lab(sid,u):s=_read_state(sid);_owned(s,u);shutil.rmtree(_root(sid),ignore_errors=True);return {"ok":True}
def reset_lab(sid,u):s=_read_state(sid);_owned(s,u);lab_id=s['lab_id'];exit_lab(sid,u);return start_lab(lab_id,u)
def complete_lab(sid,u):
 r=verify_lab(sid,u)
 if not r['passed']:raise RuntimeError('verification must pass before completion')
 s=_read_state(sid);_owned(s,u);_touch(u,s['lab_id'],status='Completed',best_score=100,completion_time=_now(),last_opened=_now());shutil.rmtree(_root(sid),ignore_errors=True);return {"ok":True,"score":r['score']}
def catalog(username):
 progress=user_progress(username);active=active_sessions(username);disabled=set(_settings()['disabled']);mods=[]
 for m in MODULES:
  core=[x for x in LABS if x['module']==m['id'] and re.fullmatch(r'M[1-5]-L[1-6]',x['id'])];done=sum(progress.get(x['id'],{}).get('status')=='Completed' for x in core);mods.append({**m,"labs":len(core),"completed":done,"progress":round(100*done/max(1,len(core)))})
 rows=[]
 for l in LABS:
  p=progress.get(l['id'],{});rows.append({**l,"enabled":l['id'] not in disabled,"progress":p or {"status":"Not Started","attempts":0,"best_score":0},"active_session":active.get(l['id'])})
 core=[x for x in LABS if re.fullmatch(r'M[1-5]-L[1-6]',x['id'])];done=sum(progress.get(x['id'],{}).get('status')=='Completed' for x in core);return {"modules":mods,"labs":rows,"overall":{"completed":done,"total":len(core),"progress":round(100*done/max(1,len(core)))},"safety":"All exercises run in an isolated simulated Lab Runtime. Host OS security, users, firewall, services, packages, network, Cloud OS production data and real credentials are not modified."}
def admin_stats():
 a=_all_progress();done=sum(1 for u in a.values() if isinstance(u,dict) for p in u.values() if isinstance(p,dict) and p.get('status')=='Completed');return {"users":len(a),"completed_labs":done,"disabled":_settings()['disabled'],"definitions":len(LABS),"active_sessions":sum(len(active_sessions(u)) for u in a)}
