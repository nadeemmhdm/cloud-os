from pathlib import Path
from .config import load

def storage_root():
    root=Path(load().get("storage_root", Path.home()/"CloudOsStorage")).expanduser().resolve()
    root.mkdir(parents=True,exist_ok=True)
    return root

def safe_path(relative=""):
    root=storage_root()
    target=(root/relative).resolve()
    if target != root and root not in target.parents:
        raise ValueError("Path escapes storage root")
    return target

def list_items(relative=""):
    p=safe_path(relative)
    if not p.is_dir(): raise FileNotFoundError(relative)
    return [{"name":x.name,"directory":x.is_dir(),"size":0 if x.is_dir() else x.stat().st_size} for x in sorted(p.iterdir(),key=lambda x:(not x.is_dir(),x.name.lower()))]
