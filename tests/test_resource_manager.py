from pathlib import Path
import pytest
import cloud_os.resource_manager as rm

def test_default_resource_profile(monkeypatch,tmp_path:Path):
 monkeypatch.setattr(rm,'STATE_FILE',tmp_path/'resource-manager.json')
 s=rm.settings();assert s['profile']=='balanced';assert s['adaptive'] is True

def test_invalid_resource_profile_is_rejected(monkeypatch,tmp_path:Path):
 monkeypatch.setattr(rm,'STATE_FILE',tmp_path/'resource-manager.json')
 with pytest.raises(ValueError):rm.configure('turbo',True)

def test_critical_process_names_cannot_be_blocked(monkeypatch,tmp_path:Path):
 monkeypatch.setattr(rm,'STATE_FILE',tmp_path/'resource-manager.json')
 name='explorer.exe' if rm.os.name=='nt' else 'systemd'
 with pytest.raises(ValueError):rm.add_block(name)

def test_blocklist_roundtrip(monkeypatch,tmp_path:Path):
 monkeypatch.setattr(rm,'STATE_FILE',tmp_path/'resource-manager.json')
 s=rm.add_block('example-user-app.exe');assert 'example-user-app.exe' in s['auto_block']
 s=rm.remove_block('example-user-app.exe');assert 'example-user-app.exe' not in s['auto_block']

def test_cloud_os_pid_is_protected():
 with pytest.raises(PermissionError):rm.process_action(rm.os.getpid(),'terminate')
