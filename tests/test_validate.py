"""Tests for choosing how structurizr-cli is run."""

from drawio_structurizr import validate


def fake_which(available):
    return lambda name: f"/bin/{name}" if name in available else None


def test_prefers_local_cli(monkeypatch):
    monkeypatch.setattr(validate.shutil, "which", fake_which({"structurizr.sh", "docker"}))
    assert validate._command("out/shop.dsl") == ["/bin/structurizr.sh", "validate", "-workspace", "out/shop.dsl"]


def test_falls_back_to_running_docker(monkeypatch, tmp_path):
    monkeypatch.setattr(validate.shutil, "which", fake_which({"docker"}))
    monkeypatch.setattr(validate, "_docker_running", lambda docker: True)
    command = validate._command(str(tmp_path / "shop.dsl"))
    assert command[:5] == ["/bin/docker", "run", "--rm", "-v", f"{tmp_path}:/usr/local/structurizr"]
    assert command[5:] == ["structurizr/cli", "validate", "-workspace", "shop.dsl"]


def test_skips_when_docker_is_not_running(monkeypatch):
    monkeypatch.setattr(validate.shutil, "which", fake_which({"docker"}))
    monkeypatch.setattr(validate, "_docker_running", lambda docker: False)
    ok, message = validate.validate("shop.dsl")
    assert ok is None
    assert "skipping validation" in message


def test_skips_when_nothing_is_installed(monkeypatch):
    monkeypatch.setattr(validate.shutil, "which", fake_which(set()))
    assert validate.validate("shop.dsl")[0] is None
