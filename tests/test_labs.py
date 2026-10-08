from pathlib import Path
import pytest
import cloud_os.labs as labs

def _sandbox(monkeypatch,tmp_path:Path):
 home=tmp_path/'labs';monkeypatch.setattr(labs,'LABS_HOME',home);monkeypatch.setattr(labs,'RUNTIME_HOME',home/'runtime');monkeypatch.setattr(labs,'PROGRESS_FILE',home/'progress.json');monkeypatch.setattr(labs,'SETTINGS_FILE',home/'settings.json');return home

def test_catalog_has_modules_1_to_9_practical_exercises(monkeypatch,tmp_path):
 _sandbox(monkeypatch,tmp_path);d=labs.catalog('alice')
 assert len(d['labs'])==66
 assert d['overall']['total']==55
 assert [m['id'] for m in d['modules']]==[f'M{i}' for i in range(1,10)]
 assert all(m['labs']==6 for m in d['modules'][:8])
 assert d['modules'][8]['labs']==7
 assert any(x['id']=='M69-FINAL' for x in d['labs'])

def test_lab_state_changes_and_verifies(monkeypatch,tmp_path):
 _sandbox(monkeypatch,tmp_path);s=labs.start_lab('M3-L4','alice');sid=s['session_id']
 for cmd in ['ports close web-server 3306','ports close web-server 22','ports close web-server 8080','scan web-server verify']:labs.run_command(sid,'alice',cmd)
 r=labs.verify_lab(sid,'alice');assert r['passed'] is True;assert r['score']==100

def test_new_microsoft_labs_are_registered_and_runnable(monkeypatch,tmp_path):
 _sandbox(monkeypatch,tmp_path)
 for lab_id in ('M6-L1','M7-L1','M8-L1','M9-L1','M69-FINAL'):
  s=labs.start_lab(lab_id,'alice');assert s['lab_id']==lab_id;assert s['resources_ready'] is True;assert s['terminal_ready'] is True;assert s['verification_ready'] is True;labs.exit_lab(s['session_id'],'alice')

def test_unsafe_commands_are_blocked_without_host_execution(monkeypatch,tmp_path):
 _sandbox(monkeypatch,tmp_path);s=labs.start_lab('M1-L1','alice')
 with pytest.raises(PermissionError):labs.run_command(s['session_id'],'alice','cat ../../Windows/System32/config/SAM')
 with pytest.raises(PermissionError):labs.run_command(s['session_id'],'alice','security scan && whoami')

def test_reset_replaces_workspace(monkeypatch,tmp_path):
 _sandbox(monkeypatch,tmp_path);s=labs.start_lab('M5-L6','alice');old=s['session_id'];new=labs.reset_lab(old,'alice');assert new['session_id']!=old;assert not (labs.RUNTIME_HOME/old).exists();assert (labs.RUNTIME_HOME/new['session_id']).exists()

def test_complete_cleans_runtime_and_saves_progress(monkeypatch,tmp_path):
 _sandbox(monkeypatch,tmp_path);s=labs.start_lab('M1-L1','alice');sid=s['session_id']
 for cmd in ['answer compute vm-web','answer storage bucket-assets','answer network vnet-main','answer identity user-analyst']:labs.run_command(sid,'alice',cmd)
 assert labs.complete_lab(sid,'alice')['ok'] is True;assert not (labs.RUNTIME_HOME/sid).exists();assert labs.user_progress('alice')['M1-L1']['status']=='Completed'

def test_session_owner_isolation(monkeypatch,tmp_path):
 _sandbox(monkeypatch,tmp_path);s=labs.start_lab('M2-L3','alice')
 with pytest.raises(PermissionError):labs.get_session(s['session_id'],'bob')
