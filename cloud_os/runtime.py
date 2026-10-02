from __future__ import annotations
from .ssh_gateway import start_background
from .cloudflare import start_connector

def start_cloudflare():
    return start_connector()

def prepare_integrations():
    # Cloud OS owns this host-native shell SSH gateway. Host sshd is never started.
    ssh_thread=start_background()
    return {"cloudflare":start_cloudflare(),"ssh":ssh_thread}
