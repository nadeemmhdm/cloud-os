import os
from pathlib import Path
from .config import load

def storage_root():
    root=Path(load().get("storage_root", Path.home()/"CloudOsStorage")).expanduser().resolve()
    root.mkdir(parents=True,exist_ok=True)
    return root

def safe_path(relative=""):
    if not isinstance(relative,str) or "\x00" in relative:
        raise ValueError("Invalid path")
    root=storage_root()
    target=(root/relative).resolve()
    if target != root and root not in target.parents:
        raise ValueError("Path escapes storage root")
    return target

def safe_upload_path(relative_dir, filename):
    name=Path(filename or "upload.bin").name
    if name in ("",".",".."):
        raise ValueError("Invalid filename")
    parent=safe_path(relative_dir)
    if not parent.exists() or not parent.is_dir():
        raise FileNotFoundError("Upload directory does not exist")
    return safe_path(str(Path(relative_dir)/name))

def list_items(relative=""):
    p=safe_path(relative)
    if not p.is_dir():
        raise FileNotFoundError(relative)

    # os.scandir caches directory-entry metadata on the common platforms and
    # avoids repeatedly calling Path.is_dir()/stat() while sorting/rendering.
    # This matters a lot for folders with hundreds or thousands of entries.
    items=[]
    with os.scandir(p) as entries:
        for entry in entries:
            try:
                is_dir=entry.is_dir(follow_symlinks=False)
                size=0 if is_dir else entry.stat(follow_symlinks=False).st_size
            except OSError:
                # A file can disappear or become inaccessible while a directory
                # is being listed. Skip it instead of stalling/failing the page.
                continue
            items.append({"name":entry.name,"directory":is_dir,"size":size})
    items.sort(key=lambda x:(not x["directory"],x["name"].lower()))
    return items
