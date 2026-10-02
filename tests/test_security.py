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


def test_dashboard_has_functional_management_controls():
    from pathlib import Path
    import cloud_os
    html=Path(cloud_os.__file__).with_name("dashboard.html").read_text(encoding="utf-8")
    for marker in ("Upload file","New folder","Create full backup","Add user","Create team","Server terminal"):
        assert marker in html

def test_server_csp_allows_embedded_logo():
    import inspect
    import cloud_os.server as server
    source=inspect.getsource(server.security_headers)
    assert "img-src 'self' data:" in source


def test_user_login_metadata_and_account_controls(isolated):
    import cloud_os.teams as teams
    teams.create_user("managed1","correct-horse-battery","Managed","member")
    teams.note_login("managed1")
    u=next(x for x in teams.users() if x["username"]=="managed1")
    assert u["first_login_at"] and u["last_login_at"]
    teams.set_password("managed1","another-correct-password")
    assert teams.authenticate("managed1","another-correct-password")
    teams.set_disabled("managed1",True)
    assert teams.authenticate("managed1","another-correct-password") is None

def test_dashboard_realtime_and_account_admin_controls():
    from pathlib import Path
    import cloud_os
    html=Path(cloud_os.__file__).with_name("dashboard.html").read_text(encoding="utf-8")
    for marker in ("live update every 2s","Reset password","Unblock","Change password","First login:","Last login:"):
        assert marker in html


def test_dashboard_about_ai_and_copy_features():
    from pathlib import Path
    import cloud_os
    html=Path(cloud_os.__file__).with_name("dashboard.html").read_text(encoding="utf-8")
    for marker in ("About Cloud OS","AI Configuration","Copy all","Cloud OS built by <b>Nadeem</b>","chatFab","/api/system/details"):
        assert marker in html

def test_system_details_endpoint_requires_auth():
    import inspect
    import cloud_os.server as server
    source=inspect.getsource(server.system_details)
    assert "require(req)" in source


def test_file_editor_and_dashboard_ux_contract():
    from pathlib import Path
    import cloud_os
    html=Path(cloud_os.__file__).with_name("dashboard.html").read_text(encoding="utf-8")
    for marker in ("New file","data-ren","/api/file/content","brandToggle","modalShade","data-st=\"about\""):
        assert marker in html
    assert "</section>\\n" not in html

def test_booster_status_is_not_hardcoded():
    import inspect
    import cloud_os.booster as booster
    assert '"mode":"normal"' not in inspect.getsource(booster.status)


def test_dashboard_popup_free_and_packaged_logo():
    from pathlib import Path
    import cloud_os
    html=Path(cloud_os.__file__).with_name("dashboard.html").read_text(encoding="utf-8")
    assert "prompt(" not in html
    assert "alert(" not in html
    assert "confirm(" not in html
    assert 'src="/cloud-os-logo.svg"' in html
    assert "</div>\\n<script>" not in html

def test_dashboard_logo_route_exists():
    import inspect
    import cloud_os.server as server
    assert "cloud-os-logo.svg" in inspect.getsource(server.cloud_os_logo)


def test_cloud_ssh_gateway_uses_native_shell_without_shell_true():
    import inspect
    import cloud_os.ssh_gateway as ssh
    source=inspect.getsource(ssh)
    assert "create_server" in source
    assert "create_subprocess_exec" in source
    assert "shell=True" not in source
    assert "process_factory=_process" in source
    assert "_can_terminal" in source

def test_cloud_ssh_defaults_to_separate_port():
    import cloud_os.config as config
    assert config.DEFAULTS["ssh_port"]==2222
    assert config.DEFAULTS["ssh_enabled"] is True
    assert config.DEFAULTS["ssh_host"]=="127.0.0.1"


def test_terminal_session_persists_working_directory(isolated):
    import cloud_os.terminal as terminal
    import cloud_os.files as files
    files.load=lambda:{"storage_root":str(isolated/"storage")}
    root=files.storage_root()
    child=root/"child"; child.mkdir()
    if os.name=="nt":
        if not terminal.available_shells(): pytest.skip("PowerShell unavailable")
        s=terminal.create_session("powershell")
        r=terminal.execute("Set-Location child",shell="powershell",session_id=s["session_id"])
    else:
        s=terminal.create_session("bash")
        r=terminal.execute("cd child",shell="bash",session_id=s["session_id"])
    assert Path(r["cwd"]).name=="child"
    terminal.close_session(s["session_id"])


def test_ssh_admin_policy_is_role_based():
    import cloud_os.ssh_gateway as ssh
    assert ssh._is_admin({"role":"admin","permissions":["terminal"]})
    assert ssh._is_admin({"role":"owner","permissions":["*"]})
    assert not ssh._is_admin({"role":"operator","permissions":["terminal"]})


def test_ai_chat_auto_selects_provider(isolated,monkeypatch):
    import cloud_os.ai as ai
    monkeypatch.setattr(ai,"_credential",lambda p: ("key","model") if p=="openai" else ("","model"))
    monkeypatch.setattr(ai,"repo_context",lambda q: "")
    monkeypatch.setattr(ai,"ask",lambda provider,prompt,system: f"{provider}:{prompt}")
    r=ai.chat_answer("write python code")
    assert r["provider"]=="openai"
    assert r["answer"]=="openai:write python code"

def test_ai_widget_has_no_provider_selector():
    import cloud_os
    html=Path(cloud_os.__file__).with_name("dashboard.html").read_text(encoding="utf-8")
    assert 'id="chatProvider"' not in html
    assert "loadChatProviders" not in html
    assert "/api/ai/chat" in html


def test_integration_status_exposes_safe_cloudflare_origins(isolated,monkeypatch):
    import cloud_os.integrations as integrations
    monkeypatch.setattr(integrations,"load",lambda:{"ssh_enabled":True,"ssh_host":"127.0.0.1","ssh_port":2222,"port":8765,"cloudflare_enabled":False,"cloudflare_tunnel":""})
    s=integrations.status()
    assert s["ssh"]["loopback_only"] is True
    assert s["ssh"]["cloudflare_origin"]=="ssh://127.0.0.1:2222"
    assert s["cloudflare"]["web_origin"]=="http://127.0.0.1:8765"
    assert s["cloudflare"]["ssh_client_proxy"]=="cloudflared access ssh --hostname %h"


def test_dashboard_sidebar_icons_compact_profile_and_local_ip():
    from pathlib import Path
    import inspect
    import cloud_os, cloud_os.server as server
    html=Path(cloud_os.__file__).with_name("dashboard.html").read_text(encoding="utf-8")
    for marker in ('class="navico"','accountProfile','roleBadge','logoutIcon','Local IP','contentIn'):
        assert marker in html
    assert '"ip_addresses":ips' in inspect.getsource(server.system_details)


def test_terminal_session_routes_exist_and_require_terminal_permission():
    import inspect
    import cloud_os.api as api
    opened=inspect.getsource(api.terminal_session)
    closed=inspect.getsource(api.terminal_session_close)
    assert 'require(req,"terminal")' in opened
    assert "create_session" in opened
    assert 'require(req,"terminal")' in closed
    assert "close_session" in closed


def test_dashboard_ai_has_animated_icon_and_http_errors_are_visible():
    from pathlib import Path
    import cloud_os
    html=Path(cloud_os.__file__).with_name("dashboard.html").read_text(encoding="utf-8")
    for marker in ("aiCore","aiSpark","@keyframes aiPulse","HTTP-"):
        assert marker in html
    assert '>AI</button>' not in html


def test_backup_delete_protects_latest_and_last(isolated,monkeypatch):
    import cloud_os.backup as backup
    root=isolated/"backups"; root.mkdir()
    monkeypatch.setattr(backup,"APP_DIR",isolated)
    (root/"20260102-new").mkdir(); (root/"20260101-old").mkdir()
    with pytest.raises(ValueError,match="latest"):
        backup.delete_backup("20260102-new")
    assert backup.delete_backup("20260101-old")=="20260101-old"
    with pytest.raises(ValueError,match="last remaining"):
        backup.delete_backup("20260102-new")


def test_collapsed_sidebar_is_icon_navigation_rail():
    import cloud_os
    html=Path(cloud_os.__file__).with_name("dashboard.html").read_text(encoding="utf-8")
    assert ".app.sideHidden{grid-template-columns:72px 1fr}" in html
    assert ".app.sideHidden .nav button span" in html
    assert 'data-delbackup' in html
    assert "Latest protected" in html


def test_overview_has_live_user_clock_date_and_timezone():
    import cloud_os
    html=Path(cloud_os.__file__).with_name("dashboard.html").read_text(encoding="utf-8")
    for marker in ("clockCard","clockTime","clockDate","Intl.DateTimeFormat","Signed in as","clockTimer=setInterval(tick,1000)"):
        assert marker in html


def test_full_backup_restore_integrity_and_safety(isolated,monkeypatch):
    import cloud_os.backup as backup
    store=isolated/"storage"; store.mkdir(); (store/"hello.txt").write_text("before",encoding="utf-8")
    monkeypatch.setattr(backup,"APP_DIR",isolated)
    monkeypatch.setattr(backup,"storage_root",lambda:store)
    (isolated/"config.json").write_text('{"x":1}',encoding="utf-8")
    name=Path(backup.create_backup()).name
    info=backup.backup_info(name)
    assert info["verified"] is True and info["file_count"]>=2
    (store/"hello.txt").write_text("changed",encoding="utf-8")
    r=backup.restore_backup(name)
    assert (store/"hello.txt").read_text(encoding="utf-8")=="before"
    assert r["safety_backup"] and r["restart_recommended"] is True


def test_backup_restore_api_and_animated_ui_contract():
    import inspect,cloud_os,cloud_os.api as api
    html=Path(cloud_os.__file__).with_name("dashboard.html").read_text(encoding="utf-8")
    assert "restore_backup" in inspect.getsource(api.backup_restore)
    assert 'role") not in ("owner","admin")' in inspect.getsource(api.backup_restore)
    for marker in ("Backup & Restore","Create full backup","data-restore","backupFloat","Integrity verified"):
        assert marker in html


def test_login_progressive_cooldown_contract(isolated,monkeypatch):
    import cloud_os.auth as auth
    auth.SECURITY_FILE=isolated/"cooldown.json"
    now=[1000.0]; monkeypatch.setattr(auth.time,"time",lambda:now[0])
    key="account:admin"
    for _ in range(4): auth.note_login_failure(key)
    assert auth.login_allowed(key)
    auth.note_login_failure(key)
    assert not auth.login_allowed(key)
    now[0]+=3
    assert auth.login_allowed(key)
    auth.clear_login_failures(key)
    auth.SECURITY_FILE=None


def test_login_autofill_and_independent_throttle_contract():
    import inspect,cloud_os,cloud_os.api as api
    src=inspect.getsource(api.do_login)
    assert 'account_key=f"account:{username.lower()}"' in src
    assert 'ip_key=f"ip:{ip}"' in src
    html=Path(cloud_os.__file__).with_name("dashboard.html").read_text(encoding="utf-8")
    assert 'id="u" value="admin" autocomplete="username"' in html
    assert 'autocomplete="current-password"' in html


def test_login_security_persists_and_progressively_locks(isolated,monkeypatch):
    import cloud_os.auth as auth
    auth.SECURITY_FILE=isolated/"login-security.json"
    monkeypatch.setattr(auth.time,"time",lambda:1000.0)
    key="account:admin"
    for _ in range(5): wait=auth.note_login_failure(key)
    assert wait>=2 and not auth.login_allowed(key)
    assert auth.SECURITY_FILE.exists()
    monkeypatch.setattr(auth.time,"time",lambda:1003.0)
    assert auth.login_allowed(key)
    auth.clear_login_failures(key)
    assert auth.login_allowed(key)
    auth.SECURITY_FILE=None


def test_login_ui_prefills_owner_and_has_cooldown_state():
    import cloud_os
    html=Path(cloud_os.__file__).with_name("dashboard.html").read_text(encoding="utf-8")
    assert 'id="u" value="admin" autocomplete="username"' in html
    for marker in ('id="loginBtn"',"loginCooldown(","Locked · ","aria-live="): assert marker in html


def test_persistent_login_throttle_definitions_are_not_overridden():
    import inspect, cloud_os.auth as auth
    source=inspect.getsource(auth)
    assert source.count("def login_allowed(key):")==1
    assert source.count("def note_login_failure(key):")==1
    assert "_LOCKED_UNTIL" not in source
    assert "_ATTEMPTS" not in source

def test_update_checker_is_hourly_and_never_auto_installs():
    import inspect, cloud_os.updater as updater
    source=inspect.getsource(updater)
    assert updater.INTERVAL==3600
    assert "pip install" not in source
    assert "subprocess" not in source
    assert "releases/latest" in source

def test_update_endpoints_require_auth_and_settings():
    import inspect, cloud_os.api as api
    assert "require(req)" in inspect.getsource(api.get_update_status)
    assert 'require(req,"settings")' in inspect.getsource(api.update_check_now)

def test_dashboard_update_center_and_dismissible_announcement():
    import cloud_os
    html=Path(cloud_os.__file__).with_name("dashboard.html").read_text(encoding="utf-8")
    for marker in ("Update Center","Check now","cloudos-dismissed-update","Hide dashboard announcement","/api/update/status","/api/update/check"):
        assert marker in html

def test_system_details_imports_socket():
    import cloud_os.server as server
    assert hasattr(server,"socket")

def test_backup_restore_preserves_current_storage_location():
    import inspect, cloud_os.backup as backup
    source=inspect.getsource(backup.restore_backup)
    assert 'cfg["storage_root"]=str(current_storage)' in source


def test_health_does_not_disclose_version():
    import cloud_os.server as server
    assert server.health()=={"status":"ok"}

def test_runtime_does_not_claim_ssh_is_isolated():
    import inspect,cloud_os.runtime as runtime
    s=inspect.getsource(runtime.prepare_integrations)
    assert "isolated SSH/SFTP" not in s and "host-native shell" in s

def test_ssh_password_auth_has_throttling():
    import inspect,cloud_os.ssh_gateway as ssh
    s=inspect.getsource(ssh.CloudOSSSHServer.validate_password)
    assert "login_allowed" in s and "note_login_failure" in s

def test_cli_update_and_uninstall_security_contract():
    import inspect,cloud_os.cli as cli
    up=inspect.getsource(cli.update); un=inspect.getsource(cli.uninstall)
    assert "--porcelain" in up and "ROLLBACK" in up and "Cloud OS updated successfully" in up
    assert "purge_data" in un and "typer.confirm" in un


def test_desktop_sidebar_uses_brand_toggle():
    import cloud_os
    html=Path(cloud_os.__file__).with_name("dashboard.html").read_text(encoding="utf-8")
    assert 'id="brandToggle"' in html
    assert 'function toggleSidebar()' in html
    assert 'aria-label="Collapse sidebar"' in html
    assert 'hidden?"Expand sidebar":"Collapse sidebar"' in html
    assert '.app.sideHidden .brandmark:after' in html

def test_cloudflare_dashboard_connector_never_exposes_token(isolated,monkeypatch):
    import cloud_os.cloudflare as cf
    cf.SECRET_FILE=isolated/"cloudflare-secret.json"
    monkeypatch.setattr(cf,"load",lambda:{"cloudflare_enabled":True,"cloudflare_tunnel":"Cloud OS Tunnel"})
    cf._write_token("x"*80)
    s=cf.status()
    assert s["token_stored"] is True
    assert "token" not in str(s).replace("token_stored","")


def test_cloudflare_dashboard_api_requires_settings_permission():
    import inspect, cloud_os.api as api
    assert 'require(req,"settings")' in inspect.getsource(api.connect_cloudflare)
    assert 'require(req,"settings")' in inspect.getsource(api.restart_cloudflare)
    assert 'require(req,"settings")' in inspect.getsource(api.disconnect_cloudflare)


def test_cloudflare_dashboard_setup_wizard_contract():
    import cloud_os
    html=Path(cloud_os.__file__).with_name("dashboard.html").read_text(encoding="utf-8")
    for marker in ("Connect existing tunnel","Connect Cloudflare Tunnel","Restart connector","/api/integrations/cloudflare/connect","The token stays on this server."):
        assert marker in html


def test_owner_recovery_key_is_hashed_and_one_time(isolated,monkeypatch):
    import cloud_os.auth as auth
    from cloud_os import config
    monkeypatch.setattr(config,"APP_DIR",isolated)
    monkeypatch.setattr(auth,"SECURITY_FILE",isolated/"login-security.json")
    config.save({})
    key=auth.create_recovery_key(force=True)
    stored=config.load()
    assert key and key not in str(stored)
    assert stored.get("owner_recovery_hash")
    assert auth.recover_owner(key,"A-strong-new-password-123") is True

def test_owner_lock_revokes_owner_sessions(isolated,monkeypatch):
    import cloud_os.auth as auth
    from cloud_os import config
    monkeypatch.setattr(config,"APP_DIR",isolated)
    config.save({})
    auth.ensure_admin("A-strong-owner-password-123")
    token=auth.login("A-strong-owner-password-123","admin")
    assert token and auth.identity(token)
    auth.set_owner_locked(True,"suspected compromise")
    assert auth.identity(token) is None
    assert auth.login("A-strong-owner-password-123","admin") is None

def test_security_center_contract():
    import inspect, cloud_os.api as ap, cloud_os
    from pathlib import Path
    html=Path(cloud_os.__file__).with_name("dashboard.html").read_text(encoding="utf-8")
    src=inspect.getsource(ap)
    for marker in ("/security/owner/recovery-key","/security/owner/lock","/recovery/owner"):
        assert marker in src
    assert "Forgot password / unlock owner" in html
    assert "Emergency account lock" in html


def test_mobile_dashboard_uses_persistent_icon_sidebar():
    import cloud_os
    from pathlib import Path
    html=Path(cloud_os.__file__).with_name("dashboard.html").read_text(encoding="utf-8")
    assert "grid-template-columns:64px minmax(0,1fr)" in html
    assert ".hamb,.mobile{display:none!important}" in html
    assert "audit-row" in html
    assert "audit-detail" in html
    assert "audit-time" in html


def test_terminal_real_newline_and_small_screen_contract():
    import inspect
    import cloud_os.terminal as terminal
    import cloud_os
    from pathlib import Path
    src=inspect.getsource(terminal.execute)
    assert 'rstrip("\\\\r\\\\n")+"\\\\n"' not in src
    assert 'rstrip("\\r\\n")+"\\n"' in src
    html=Path(cloud_os.__file__).with_name("dashboard.html").read_text(encoding="utf-8")
    assert "@media(max-width:430px)" in html
    assert "@media(max-width:360px)" in html
    assert "white-space:pre;overflow:auto" in html


def test_dashboard_fast_navigation_and_audit_tail_contract():
    import cloud_os
    from pathlib import Path
    html=Path(cloud_os.__file__).with_name("dashboard.html").read_text(encoding="utf-8")
    assert "navGeneration" in html
    assert "pageLoading" in html
    assert "gen!==navGeneration" in html
    audit=Path(cloud_os.__file__).with_name("audit.py").read_text(encoding="utf-8")
    assert "deque(f,maxlen=limit)" in audit
    assert "threading.RLock()" in audit

def test_same_origin_rejects_cross_site_fetch():
    import inspect, cloud_os.api as api
    src=inspect.getsource(api._same_origin)
    assert 'fetch_site=="cross-site"' in src
    assert "Cross-site state-changing request blocked" in src


def test_windows_safe_updater_does_not_upgrade_loaded_dependencies():
    import inspect, cloud_os.cli as cli
    install_src=inspect.getsource(cli._install_application_source)
    assert '"--no-deps"' in install_src
    assert '"--disable-pip-version-check"' in install_src
    update_src=inspect.getsource(cli.update)
    assert '"--no-deps"' in update_src
    verify_src=inspect.getsource(cli._verify_runtime_dependencies)
    assert '"check"' in verify_src


def test_windows_update_is_deferred_until_managed_server_stops():
    import inspect, cloud_os.cli as cli
    helper=inspect.getsource(cli._windows_deferred_update)
    assert "Wait-Process" in helper
    assert "Stop-ScheduledTask" in helper
    assert "Start-ScheduledTask" in helper
    assert "--no-deps" in helper
    assert "pip check" in helper
    update=inspect.getsource(cli.update)
    assert "_windows_deferred_update(target,old,old_ref)" in update
