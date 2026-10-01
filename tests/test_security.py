import os
from pathlib import Path
import pytest

@pytest.fixture()
def isolated(tmp_path,monkeypatch):
    monkeypatch.setenv("CLOUD_OS_HOME",str(tmp_path/"home"))
    import cloud_os.config as config
    config.APP_DIR=tmp_path/"home"; config.CONFIG_FILE=config.APP_DIR/"config.json"
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
