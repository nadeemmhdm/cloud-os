from __future__ import annotations
import subprocess
from .files import storage_root
MAX_OUTPUT=20000
def execute(command,timeout=20):
 if not command or len(command)>2000: raise ValueError("Invalid command")
 proc=subprocess.run(command,shell=True,cwd=str(storage_root()),capture_output=True,text=True,timeout=timeout)
 return {"code":proc.returncode,"stdout":proc.stdout[-MAX_OUTPUT:],"stderr":proc.stderr[-MAX_OUTPUT:]}
