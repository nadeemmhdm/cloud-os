from datetime import datetime,timezone
from pathlib import Path
import shutil,secrets
from .files import storage_root
from .config import APP_DIR

def create_backup():
    base=APP_DIR/"backups"; base.mkdir(parents=True,exist_ok=True)
    stamp=datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    dest=base/f"{stamp}-{secrets.token_hex(3)}"
    shutil.copytree(storage_root(),dest)
    return str(dest)

def list_backups():
    p=APP_DIR/"backups"
    return [] if not p.exists() else [x.name for x in sorted(p.iterdir(),reverse=True) if x.is_dir()]
