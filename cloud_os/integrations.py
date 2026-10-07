import shutil,socket,ipaddress
from .config import load
from .cloudflare import status as cloudflare_status

def _port_open(host,port):
    try:
        with socket.create_connection((host,port),timeout=.25):return True
    except OSError:return False

def _local_ip():
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);s.connect(('8.8.8.8',80));ip=s.getsockname()[0];s.close();return ip
    except OSError:
        try:return socket.gethostbyname(socket.gethostname())
        except OSError:return '127.0.0.1'

def _is_public_hostname(host):
    h=(host or '').split(':')[0].strip('[]').lower()
    if not h or h in {'localhost','127.0.0.1','::1'}:return False
    try:return not (ipaddress.ip_address(h).is_private or ipaddress.ip_address(h).is_loopback)
    except ValueError:return '.' in h

def status(request_host=''):
    cfg=load();sh=str(cfg.get('ssh_host','127.0.0.1'));sp=int(cfg.get('ssh_port',2222));probe='127.0.0.1' if sh in ('0.0.0.0','::') else sh
    cf=bool(shutil.which('cloudflared'));managed=cloudflare_status();local_ip=_local_ip();hostname=(request_host or '').split(':')[0].strip('[]')
    remote=_is_public_hostname(hostname) and bool(managed['configured'])
    ssh_client=(f'ssh USER@{hostname}' if remote else f'ssh -p {sp} USER@{local_ip}')
    if remote:ssh_client=f'ssh -o ProxyCommand="cloudflared access ssh --hostname %h" USER@{hostname}'
    return {
      'access_mode':'domain' if remote else 'local',
      'access_host':hostname if remote else local_ip,
      'ssh':{
        'enabled':bool(cfg.get('ssh_enabled')),'type':'Cloud OS native server SSH gateway','host':sh,'port':sp,'running':_port_open(probe,sp),'native_server_shell':True,
        'local_ip':local_ip,'local_command':f'ssh -p {sp} USER@{local_ip}','display_command':ssh_client,
        'domain_host':hostname if remote else '','domain_command':ssh_client if remote else '',
        'cloudflare_origin':f'ssh://127.0.0.1:{sp}','loopback_only':sh in ('127.0.0.1','::1','localhost'),
      },
      'cloudflare':{
        'enabled':bool(cfg.get('cloudflare_enabled')),'configured':bool(cfg.get('cloudflare_tunnel')),'installed':cf,'tunnel':str(cfg.get('cloudflare_tunnel','')),
        'web_origin':f"http://127.0.0.1:{int(cfg.get('port',8765))}",'ssh_origin':f'ssh://127.0.0.1:{sp}','ssh_client_proxy':'cloudflared access ssh --hostname %h',
        'connector_running':managed['connector_running'],'token_stored':managed['token_stored'],'cloudflared_version':managed['cloudflared_version'],'diagnostic':managed['diagnostic'],
      }
    }
