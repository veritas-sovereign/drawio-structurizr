"""Phase D: --validate-required fails when no validator is available."""

import os
import stat
from pathlib import Path

import pytest

from drawio_structurizr.main import main

SHOP = str(Path(__file__).resolve().parent.parent / "examples" / "shop.drawio")


def stub_cli(folder, exit_code):
    path = folder / "structurizr-cli"
    path.write_text(f'#!/bin/sh\necho "stub validate $3"\nexit {exit_code}\n')
    path.chmod(path.stat().st_mode | stat.S_IEXEC)


@pytest.fixture
def bin_dir(tmp_path, monkeypatch):
    folder = tmp_path / "bin"
    folder.mkdir()
    monkeypatch.setenv("PATH", f"{folder}{os.pathsep}/bin{os.pathsep}/usr/bin")
    return folder


def test_valid_workspace_passes(bin_dir, tmp_path, capsys):
    stub_cli(bin_dir, 0)
    output = tmp_path / "shop.dsl"
    assert main([SHOP, "-o", str(output), "--validate-required"]) == 0
    assert output.exists()
    out = capsys.readouterr().out
    assert f"Validated {output}" in out
    assert "stub validate" not in out  # validator output is only shown on failure


def test_invalid_workspace_fails(bin_dir, tmp_path, capsys):
    stub_cli(bin_dir, 1)
    assert main([SHOP, "-o", str(tmp_path / "shop.dsl"), "--validate-required"]) == 1
    assert "stub validate" in capsys.readouterr().err


def test_missing_validator_fails_before_writing(tmp_path, monkeypatch, capsys):
    empty = tmp_path / "empty"
    empty.mkdir()
    monkeypatch.setenv("PATH", str(empty))
    output = tmp_path / "shop.dsl"
    assert main([SHOP, "-o", str(output), "--validate", "--validate-required"]) == 1
    assert not output.exists()
    err = capsys.readouterr().err
    assert "--validate-required was set, but no Structurizr validator is available" in err
    assert "Checked structurizr-cli on PATH" in err and "not found" in err
    assert "Checked docker" in err


def test_plain_validate_still_skips(tmp_path, monkeypatch):
    empty = tmp_path / "empty"
    empty.mkdir()
    monkeypatch.setenv("PATH", str(empty))
    output = tmp_path / "shop.dsl"
    assert main([SHOP, "-o", str(output), "--validate"]) == 0
    assert output.exists()


@pytest.mark.parametrize("flag", ["--check", "--dry-run", "--diff"])
def test_rejected_without_an_output_file(flag):
    with pytest.raises(SystemExit) as exit_info:
        main([SHOP, "--validate-required", flag])
    assert exit_info.value.code == 2
