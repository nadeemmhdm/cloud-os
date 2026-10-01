import os
from pathlib import Path
import pytest

@pytest.fixture()
def isolated(tmp_path,monkeypatch):
    monkeypatch.setenv("CLOUD_OS_HOME",str(tmp_path/"home"))
    import cloud_os.config as config
    config.APP_DIR=tmp_path/"home"; config.APP_DIR.mkdir(parents=True,exist_ok=True); config.CONFIG_FILE=config.APP_DIR/"config.json"
    import cloud_os.teams as teams
    teams.DB=config.APP_DIR/"access.json"
    import cloud_os.audit as audit
    audit.LOG=config.APP_DIR/"audit.log"
    yield tmp_path

def test_safe_path_blocks_escape(isolated):
    import cloud_os.files as files
    files.load=lambda:{"storage_root":str(isolated/"storage")}
    with pytest.raises(ValueError): files.safe_path("../escape")

def test_password_minimum(isolated):
    from cloud_os.auth import hash_password
    with pytest.raises(ValueError): hash_password("short")

def test_role_permissions(isolated):
    import cloud_os.teams as teams
    teams.create_user("viewer1","correct-horse-battery","Viewer","viewer")
    assert teams.permissions("viewer1")==["files.read"]

def test_reserved_admin_username(isolated):
    import cloud_os.teams as teams
    with pytest.raises(ValueError): teams.create_user("admin","correct-horse-battery")

def test_upload_filename_is_basename(isolated):
    import cloud_os.files as files
    files.load=lambda:{"storage_root":str(isolated/"storage")}
    files.storage_root()
    p=files.safe_upload_path("","../evil.txt")
    assert p.name=="evil.txt"
    assert p.parent==files.storage_root()


def test_terminal_rejects_unknown_shell(isolated):
    import cloud_os.terminal as terminal
    with pytest.raises(ValueError):
        terminal.execute("echo test",shell="unknown")

def test_terminal_uses_host_native_shell(isolated,monkeypatch):
    import cloud_os.terminal as terminal
    import cloud_os.files as files
    files.load=lambda:{"storage_root":str(isolated/"storage")}
    files.storage_root()
    if os.name=="nt":
        if not terminal.available_shells(): pytest.skip("PowerShell unavailable")
        result=terminal.execute("Write-Output cloudos",shell="powershell")
    else:
        result=terminal.execute("printf cloudos",shell="bash")
    assert result["code"]==0
    assert "cloudos" in result["stdout"]


def test_owner_role_cannot_be_created(isolated):
    import cloud_os.teams as teams
    with pytest.raises(ValueError):
        teams.create_user("secondowner","correct-horse-battery","Second Owner","owner")

def test_owner_role_cannot_be_granted_by_team(isolated):
    import cloud_os.teams as teams
    teams.create_user("member1","correct-horse-battery","Member","member")
    teams.create_team("ops")
    with pytest.raises(ValueError):
        teams.add_member("ops","member1","owner")

def test_windows_privileged_terminal_never_bypasses_uac(isolated,monkeypatch):
    import cloud_os.terminal as terminal
    monkeypatch.setattr(terminal.os,"name","nt")
    with pytest.raises(PermissionError):
        terminal.execute("Write-Output test",shell="powershell",privileged=True)


def test_corrupt_access_database_fails_closed(isolated):
    import cloud_os.teams as teams
    teams.DB.parent.mkdir(parents=True,exist_ok=True)
    teams.DB.write_text("{broken",encoding="utf-8")
    with pytest.raises(RuntimeError):
        teams.users()

def test_backup_names_do_not_collide(isolated):
    import cloud_os.backup as backup
    import cloud_os.files as files
    files.load=lambda:{"storage_root":str(isolated/"storage")}
    root=files.storage_root()
    (root/"data.txt").write_text("ok",encoding="utf-8")
    a=backup.create_backup()
    b=backup.create_backup()
    assert a!=b

def test_audit_detail_is_bounded(isolated):
    import cloud_os.audit as audit
    audit.record("test","x"*10000)
    rows=audit.recent()
    assert len(rows[-1]["detail"])==4096


def test_error_catalog_has_unique_codes():
    import cloud_os.errors as errors
    codes=[x.code for x in errors.ERRORS.values()]
    assert len(codes)==len(set(codes))
    assert all(code==key for key,code in zip(errors.ERRORS.keys(),codes))

def test_error_payload_is_stable():
    from cloud_os.errors import payload
    p=payload("AUTH-001")
    assert p["error"]["code"]=="AUTH-001"
    assert "message" in p["error"]
    assert "suggestion" in p["error"]

def test_error_detail_is_bounded():
    from cloud_os.errors import payload
    p=payload("SYS-001","x"*5000)
    assert len(p["error"]["detail"])==500


def test_corrupt_config_fails_closed(isolated):
    import cloud_os.config as config
    config.CONFIG_FILE.write_text("{broken",encoding="utf-8")
    with pytest.raises(RuntimeError):
        config.load()

def test_ai_provider_http_error_does_not_expose_body(isolated,monkeypatch):
    import io
    import urllib.error
    import cloud_os.ai as ai
    class FakeOpener:
        def __call__(self,*args,**kwargs):
            raise urllib.error.HTTPError("https://provider.invalid",401,"bad",{},io.BytesIO(b"secret-provider-body"))
    monkeypatch.setattr(ai.urllib.request,"urlopen",FakeOpener())
    with pytest.raises(RuntimeError) as exc:
        ai._post("https://provider.invalid",{},{"x":1})
    assert "secret-provider-body" not in str(exc.value)

def test_terminal_audit_redaction_contract():
    import inspect
    import cloud_os.api as api
    source=inspect.getsource(api.terminal)
    assert "body.command[:200]" not in source
    assert "command_length" in source

def test_cross_origin_mutation_is_blocked():
    from starlette.requests import Request
    import cloud_os.api as api
    scope={"type":"http","method":"POST","path":"/api/folder","headers":[(b"host",b"cloud.local"),(b"origin",b"https://evil.example")]}
    req=Request(scope)
    with pytest.raises(Exception) as exc:
        api._same_origin(req)
    assert getattr(exc.value,"status_code",None)==403
