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
    assert command[5:] == ["structurizr/cli:2025.11.09", "validate", "-workspace", "shop.dsl"]


def test_skips_when_docker_is_not_running(monkeypatch):
    monkeypatch.setattr(validate.shutil, "which", fake_which({"docker"}))
    monkeypatch.setattr(validate, "_docker_running", lambda docker: False)
    ok, message = validate.validate("shop.dsl")
    assert ok is None
    assert "skipping validation" in message


def test_skips_when_nothing_is_installed(monkeypatch):
    monkeypatch.setattr(validate.shutil, "which", fake_which(set()))
    assert validate.validate("shop.dsl")[0] is None


def test_export_command_local(monkeypatch):
    monkeypatch.setattr(validate.shutil, "which", fake_which({"structurizr-cli"}))
    assert validate._command("w.dsl", "export", ["-format", "mermaid"], "out") == [
        "/bin/structurizr-cli", "export", "-workspace", "w.dsl", "-format", "mermaid", "-output", "out"]


def test_export_command_docker_mounts_output(monkeypatch, tmp_path):
    monkeypatch.setattr(validate.shutil, "which", fake_which({"docker"}))
    monkeypatch.setattr(validate, "_docker_running", lambda docker: True)
    command = validate._command(str(tmp_path / "w.dsl"), "export", ["-format", "json"], str(tmp_path / "out"))
    assert f"{tmp_path / 'out'}:/output" in command
    assert command[-6:] == ["-workspace", "w.dsl", "-format", "json", "-output", "/output"]


def test_export_without_cli_fails_clearly(monkeypatch, tmp_path):
    monkeypatch.setattr(validate.shutil, "which", fake_which(set()))
    ok, message = validate.export("w.dsl", "mermaid", str(tmp_path / "out"))
    assert ok is None
    assert "cannot export mermaid" in message
