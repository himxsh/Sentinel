import json
import subprocess

import pytest

from sentinel.tools.ccloud import ALLOWED, control_plane, run


def test_rejects_non_allowlisted_args():
    with pytest.raises(ValueError, match="not in allow-list"):
        run(["cluster", "delete", "foo"])
    with pytest.raises(ValueError, match="not in allow-list"):
        run(["sql", "shell"])


def test_allowlisted_run_returns_ok(monkeypatch):
    fake_data = [{"id": "c1", "name": "test-cluster", "cloud_provider": "aws"}]

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=json.dumps(fake_data),
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    # avoid needing actual ccloud binary on PATH
    monkeypatch.setattr("sentinel.tools.ccloud._bin", lambda: "/faux/ccloud")

    result = run(["cluster", "list"])
    assert result["ok"] is True
    assert result["data"] == fake_data


def test_soft_fail_on_file_not_found(monkeypatch):
    def fake_run(*args, **kwargs):
        raise FileNotFoundError()

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr("sentinel.tools.ccloud._bin", lambda: "/nonexistent/ccloud")

    result = control_plane()
    assert result["ok"] is False
    assert "not found" in result["error"]


def test_soft_fail_on_non_zero_exit(monkeypatch):
    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="unauthorized",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr("sentinel.tools.ccloud._bin", lambda: "/faux/ccloud")

    result = run(["cluster", "list"])
    assert result["ok"] is False
    assert "unauthorized" in result["error"]


def test_control_plane_returns_cluster_list(monkeypatch):
    fake_data = [{"id": "c1"}]

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=[], returncode=0, stdout=json.dumps(fake_data), stderr="",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr("sentinel.tools.ccloud._bin", lambda: "/faux/ccloud")

    result = control_plane()
    assert result["ok"] is True
    assert result["data"] == fake_data


def test_control_plane_soft_fail(monkeypatch):
    monkeypatch.setattr("sentinel.tools.ccloud._bin", lambda: "/nonexistent/ccloud")

    result = control_plane()
    assert result["ok"] is False
