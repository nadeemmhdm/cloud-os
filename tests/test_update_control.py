from __future__ import annotations
import pytest
import cloud_os.update_control as updates


def _memory_status(monkeypatch,initial):
    state=dict(initial)
    def load():return dict(state)
    def save(value):state.clear();state.update(value)
    monkeypatch.setattr(updates,"_load",load)
    monkeypatch.setattr(updates,"_save",save)
    return state


def test_stale_update_lock_is_cleared_before_force_retry(monkeypatch):
    state=_memory_status(monkeypatch,{"state":"queued","queued_at":"2020-01-01T00:00:00+00:00","worker_pid":999999})
    monkeypatch.setattr(updates,"_worker_alive",lambda status:False)
    monkeypatch.setattr(updates,"current_commit",lambda:"abc123")
    monkeypatch.setattr(updates,"control_status",lambda:dict(state))
    class Worker:pid=43210
    monkeypatch.setattr(updates.subprocess,"Popen",lambda *a,**k:Worker())
    result=updates.start_install(force=True,server_pid=123)
    assert result["state"]=="queued"
    assert state["worker_pid"]==43210
    assert state["target"]=="origin/main"
    assert state["force"] is True


def test_live_update_worker_still_blocks_parallel_update(monkeypatch):
    _memory_status(monkeypatch,{"state":"installing","worker_pid":12345})
    monkeypatch.setattr(updates,"_worker_alive",lambda status:True)
    with pytest.raises(RuntimeError,match="already running"):
        updates.start_install(force=True,server_pid=123)


def test_update_worker_launch_failure_does_not_leave_queued_lock(monkeypatch):
    state=_memory_status(monkeypatch,{"state":"idle"})
    monkeypatch.setattr(updates,"current_commit",lambda:"abc123")
    def fail_launch(*args,**kwargs):raise OSError("launcher unavailable")
    monkeypatch.setattr(updates.subprocess,"Popen",fail_launch)
    with pytest.raises(RuntimeError,match="Could not start update worker"):
        updates.start_install(force=True,server_pid=123)
    assert state["state"]=="failed"
    assert state["worker_pid"] is None
    assert "launcher unavailable" in state["error"]
