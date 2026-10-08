from pathlib import Path
import re
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
 assert all(x.get('resources') for x in d['labs'])

def test_lab_state_changes_and_verifies(monkeypatch,tmp_path):
 _sandbox(monkeypatch,tmp_path);s=labs.start_lab('M3-L4','alice');sid=s['session_id']
 for cmd in ['ports close web-server 3306','ports close web-server 22','ports close web-server 8080','scan web-server verify']:labs.run_command(sid,'alice',cmd)
 r=labs.verify_lab(sid,'alice');assert r['passed'] is True;assert r['score']==100

def test_new_microsoft_labs_are_registered_and_runnable(monkeypatch,tmp_path):
 _sandbox(monkeypatch,tmp_path)
 for lab_id in ('M6-L1','M7-L1','M8-L1','M9-L1','M69-FINAL'):
  s=labs.start_lab(lab_id,'alice');assert s['lab_id']==lab_id;assert s['resources_ready'] is True;assert s['resource_count']>0;assert s['terminal_ready'] is True;assert s['verification_ready'] is True;labs.exit_lab(s['session_id'],'alice')

def test_every_module_1_to_6_core_lab_has_resources_and_all_commands_run(monkeypatch,tmp_path):
 _sandbox(monkeypatch,tmp_path)
 core=[x for x in labs.LABS if re.fullmatch(r'M[1-6]-L[1-6]',x['id'])]
 assert len(core)==36
 for definition in core:
  s=labs.start_lab(definition['id'],'alice');sid=s['session_id'];root=labs.RUNTIME_HOME/sid
  assert s['resources_ready'] is True
  assert s['resource_count']==len(definition['resources'])
  assert (root/'resources'/'manifest.json').exists()
  assert (root/'resources'/'catalog.json').exists()
  resource_text=labs.run_command(sid,'alice','resources')['output']
  assert definition['resources'][0]['id'] in resource_text
  for command in definition['commands']:
   result=labs.run_command(sid,'alice',command['cmd'])
   assert 'unsupported simulator command' not in result['output'].lower()
  verified=labs.verify_lab(sid,'alice')
  assert verified['passed'] is True, definition['id']
  assert verified['score']==100, definition['id']
  labs.exit_lab(sid,'alice')

def test_every_lab_definition_has_resources_and_runnable_commands(monkeypatch,tmp_path):
 _sandbox(monkeypatch,tmp_path)
 assert not labs._DEFINITION_ERRORS
 for definition in labs.LABS:
  s=labs.start_lab(definition['id'],'qa-user');sid=s['session_id']
  assert s['resources_ready'] is True, definition['id']
  assert s['resource_count']>0, definition['id']
  for command in definition['commands']:
   result=labs.run_command(sid,'qa-user',command['cmd'])
   assert result['output'], (definition['id'],command['cmd'])
   assert 'unsupported simulator command' not in result['output'].lower(), (definition['id'],command['cmd'])
  verified=labs.verify_lab(sid,'qa-user')
  assert verified['passed'] is True, definition['id']
  assert verified['score']==100, definition['id']
  labs.exit_lab(sid,'qa-user')

def test_kql_comparison_operators_are_valid_simulator_syntax(monkeypatch,tmp_path):
 _sandbox(monkeypatch,tmp_path);s=labs.start_lab('M8-L2','alice')
 result=labs.run_command(s['session_id'],'alice','SigninLogs | where TimeGenerated > ago(1h)')
 assert 'previous simulated hour' in result['output']

def test_lab_terminal_builtins_work(monkeypatch,tmp_path):
 _sandbox(monkeypatch,tmp_path);s=labs.start_lab('M6-L1','alice');sid=s['session_id']
 assert 'Built-ins' in labs.run_command(sid,'alice','help')['output']
 assert 'entra-tenant' in labs.run_command(sid,'alice','resources')['output']
 assert 'identity-tenant' in labs.run_command(sid,'alice','resource show entra-tenant')['output']
 assert 'M6-L1' in labs.run_command(sid,'alice','status')['output']
 assert 'entra-tenant' in labs.run_command(sid,'alice','cat resources/catalog.json')['output']

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
