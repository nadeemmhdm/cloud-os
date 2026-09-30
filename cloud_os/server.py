from fastapi import FastAPI
from . import __version__

app = FastAPI(title="Cloud Os", version=__version__)

@app.get("/health")
def health():
    return {"status":"ok","version":__version__}

@app.get("/")
def root():
    return {"name":"Cloud Os","status":"online","version":__version__}
