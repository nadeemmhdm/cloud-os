from __future__ import annotations
import json, os
from pathlib import Path

APP_DIR=Path(os.getenv("CLOUD_OS_HOME",Path.home()/".cloud-os"))
CONFIG_FILE=APP_DIR/"config.json"
DEFAULTS={
 "host":"127.0.0.1","port":8765,"ssh_enabled":True,"cloudflare_enabled":False,
 "cloudflare_tunnel":"","storage_root":str(Path.home()/"CloudOsStorage"),
 "admin_password_hash":"","secure_cookies":False
}

def _protect(path: Path):
 try:
  if os.name != "nt": path.chmod(0o600)
 except OSError:
  pass

def load():
 APP_DIR.mkdir(parents=True,exist_ok=True)
 if not CONFIG_FILE.exists(): save(DEFAULTS.copy())
 data=DEFAULTS.copy()
 try:
  raw=json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
  if not isinstance(raw,dict): raise ValueError("configuration root must be an object")
  data.update(raw)
 except (OSError,json.JSONDecodeError,ValueError) as exc:
  raise RuntimeError(f"Cloud OS configuration is unreadable or corrupt: {exc}") from exc
 return data

def save(data):
 APP_DIR.mkdir(parents=True,exist_ok=True)
 tmp=CONFIG_FILE.with_suffix(".tmp")
 tmp.write_text(json.dumps(data,indent=2),encoding="utf-8")
 _protect(tmp)
 tmp.replace(CONFIG_FILE)
 _protect(CONFIG_FILE)
