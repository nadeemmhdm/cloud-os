from datetime import datetime
from pathlib import Path
import shutil
from .files import storage_root
from .config import APP_DIR
def create_backup():
 dest=APP_DIR/"backups"/datetime.now().strftime("%Y%m%d-%H%M%S"); dest.parent.mkdir(parents=True,exist_ok=True)
 shutil.copytree(storage_root(),dest); return str(dest)
def list_backups():
 p=APP_DIR/"backups"; return [] if not p.exists() else [x.name for x in sorted(p.iterdir(),reverse=True) if x.is_dir()]
