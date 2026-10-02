from __future__ import annotations
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json,shutil,secrets
from .files import storage_root
from .config import APP_DIR

STATE_FILES=("config.json","access.json","audit.log","ai-secrets.json")
MANIFEST="manifest.json"

def _base():
    p=APP_DIR/"backups"; p.mkdir(parents=True,exist_ok=True); return p

def _target(name):
    if not isinstance(name,str) or not name or Path(name).name!=name or name in (".",".."): raise ValueError("Invalid backup name")
    base=_base().resolve(); target=(base/name).resolve()
    if target.parent!=base or not target.is_dir(): raise FileNotFoundError("Backup not found")
    return target

def _hash(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def _inventory(root):
    return {p.relative_to(root).as_posix():{"sha256":_hash(p),"size":p.stat().st_size} for p in sorted(root.rglob("*")) if p.is_file() and p.name!=MANIFEST}

def create_backup(reason="manual"):
    base=_base(); stamp=datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    dest=base/f"{stamp}-{secrets.token_hex(3)}"; data=dest/"data"; state=data/"state"; files=data/"storage"
    state.mkdir(parents=True); src=storage_root()
    if src.exists(): shutil.copytree(src,files)
    else: files.mkdir()
    for name in STATE_FILES:
        p=APP_DIR/name
        if p.is_file(): shutil.copy2(p,state/name)
    inv=_inventory(data)
    manifest={"format":2,"created_at":datetime.now(timezone.utc).isoformat(),"reason":reason,"files":inv,"file_count":len(inv),"total_bytes":sum(x["size"] for x in inv.values())}
    (dest/MANIFEST).write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    return str(dest)

def list_backups():
    p=APP_DIR/"backups"
    return [] if not p.exists() else [x.name for x in sorted(p.iterdir(),reverse=True) if x.is_dir()]

def backup_info(name):
    target=_target(name); mf=target/MANIFEST
    if not mf.is_file(): return {"name":name,"format":1,"legacy":True,"file_count":None,"total_bytes":None,"created_at":None,"verified":False}
    try: d=json.loads(mf.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as e: raise ValueError(f"Backup manifest is unreadable: {e}") from e
    return {"name":name,"format":d.get("format"),"legacy":False,"file_count":d.get("file_count",0),"total_bytes":d.get("total_bytes",0),"created_at":d.get("created_at"),"verified":verify_backup(name)}

def verify_backup(name):
    target=_target(name); mf=target/MANIFEST
    if not mf.is_file(): return False
    try:d=json.loads(mf.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError): return False
    data=target/"data"
    for rel,meta in d.get("files",{}).items():
        p=(data/rel).resolve()
        try:p.relative_to(data.resolve())
        except ValueError:return False
        if not p.is_file() or _hash(p)!=meta.get("sha256"): return False
    return True

def restore_backup(name):
    target=_target(name)
    if not (target/MANIFEST).is_file(): raise ValueError("Legacy storage-only backups cannot perform full restore")
    if not verify_backup(name): raise ValueError("Backup integrity verification failed")
    safety=Path(create_backup("pre-restore"))
    data=target/"data"; saved_storage=data/"storage"; saved_state=data/"state"
    current_storage=storage_root()
    try:
        if current_storage.exists(): shutil.rmtree(current_storage)
        shutil.copytree(saved_storage,current_storage)
        for fname in STATE_FILES:
            src=saved_state/fname; dst=APP_DIR/fname
            if src.is_file(): shutil.copy2(src,dst)
            elif dst.exists(): dst.unlink()
        # Preserve the current host storage location. Never redirect a restore
        # into an arbitrary path embedded in an older backup configuration.
        cfg_path=APP_DIR/"config.json"
        if cfg_path.is_file():
            cfg=json.loads(cfg_path.read_text(encoding="utf-8")); cfg["storage_root"]=str(current_storage)
            tmp=cfg_path.with_suffix(".restore.tmp"); tmp.write_text(json.dumps(cfg,indent=2),encoding="utf-8"); tmp.replace(cfg_path)
    except Exception:
        # Best-effort rollback from the safety snapshot.
        sdata=safety/"data"; sstorage=sdata/"storage"; sstate=sdata/"state"
        if current_storage.exists(): shutil.rmtree(current_storage)
        shutil.copytree(sstorage,current_storage)
        for fname in STATE_FILES:
            src=sstate/fname; dst=APP_DIR/fname
            if src.is_file(): shutil.copy2(src,dst)
        raise
    return {"restored":name,"safety_backup":safety.name,"restart_recommended":True}

def delete_backup(name):
    target=_target(name); items=[x for x in sorted(_base().iterdir(),reverse=True) if x.is_dir()]
    if len(items)==1: raise ValueError("The last remaining backup cannot be deleted")
    if target==items[0]: raise ValueError("The latest backup cannot be deleted")
    shutil.rmtree(target); return name
