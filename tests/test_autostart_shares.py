import inspect
from pathlib import Path

def test_windows_autostart_contract():
 import cloud_os.cli as cli
 src=inspect.getsource(cli._windows_autostart)
 assert "New-ScheduledTaskTrigger -AtStartup" in src
 assert "-LogonType S4U" in src
 assert "-RunLevel Limited" in src
 assert "RestartCount 20" in src
 assert "cloud_os.cli start" in src
 assert "CLOUD_OS_HOME" in src

def test_runtime_starts_configured_cloudflare():
 import cloud_os.runtime as runtime
 assert "start_connector" in inspect.getsource(runtime.prepare_integrations) or "start_cloudflare" in inspect.getsource(runtime.prepare_integrations)

def test_share_tokens_hide_storage_path(tmp_path,monkeypatch):
 import cloud_os.config as config
 import cloud_os.files as files
 import cloud_os.shares as shares
 config.APP_DIR=tmp_path/'home';config.CONFIG_FILE=config.APP_DIR/'config.json';shares.APP_DIR=config.APP_DIR;shares.SHARES=config.APP_DIR/'shares.json'
 root=tmp_path/'storage';root.mkdir();(root/'secret.txt').write_text('hello',encoding='utf-8')
 monkeypatch.setattr(files,'load',lambda:{'storage_root':str(root)})
 monkeypatch.setattr(shares,'safe_path',files.safe_path)
 r=shares.create('secret.txt','strong-share-password',24,False)
 assert 'secret.txt' not in r['token']
 assert shares.resolve(r['token'],'wrong')[0] is None
 resolved,status=shares.resolve(r['token'],'strong-share-password')
 assert status=='ok' and resolved[1].name=='secret.txt'

def test_folder_share_child_cannot_escape(tmp_path,monkeypatch):
 import cloud_os.config as config
 import cloud_os.files as files
 import cloud_os.shares as shares
 config.APP_DIR=tmp_path/'home';config.CONFIG_FILE=config.APP_DIR/'config.json';shares.APP_DIR=config.APP_DIR;shares.SHARES=config.APP_DIR/'shares.json'
 root=tmp_path/'storage';folder=root/'folder';folder.mkdir(parents=True);(folder/'a.txt').write_text('a')
 monkeypatch.setattr(files,'load',lambda:{'storage_root':str(root)});monkeypatch.setattr(shares,'safe_path',files.safe_path)
 r=shares.create('folder','',24,False)
 assert shares.resolve_child(r['token'],'../outside.txt')[0] is None
 assert shares.resolve_child(r['token'],'a.txt')[0][1].name=='a.txt'

def test_share_preview_features_are_packaged():
 import cloud_os,cloud_os.server as server
 root=Path(cloud_os.__file__).parent
 assert (root/'share-ui.js').exists()
 src=inspect.getsource(server)
 for marker in ("<video class=\"viewer\" controls","kind=='pdf'","aria-label=\"Copy code\"","_doc_text","Storage location is private"):
  assert marker in src
