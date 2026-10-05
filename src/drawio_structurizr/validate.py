"""Optional: validate a generated workspace with structurizr-cli.

Uses a local ``structurizr-cli`` (or ``structurizr.sh``) on PATH when one is
installed, otherwise the ``structurizr/cli`` Docker image when Docker is
running. https://docs.structurizr.com/cli
"""

import os
import shutil
import subprocess

CLI_NAMES = ("structurizr-cli", "structurizr.sh", "structurizr")
DOCKER_IMAGE = "structurizr/cli"
DOCKER_WORKDIR = "/usr/local/structurizr"


def find_cli():
    for name in CLI_NAMES:
        path = shutil.which(name)
        if path:
            return path
    return None


def _docker_running(docker):
    try:
        return subprocess.run([docker, "info"], capture_output=True, timeout=20).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def _command(workspace_path):
    cli = find_cli()
    if cli is not None:
        return [cli, "validate", "-workspace", str(workspace_path)]

    docker = shutil.which("docker")
    if docker is not None and _docker_running(docker):
        folder, name = os.path.split(os.path.abspath(workspace_path))
        return [docker, "run", "--rm", "-v", f"{folder}:{DOCKER_WORKDIR}",
                DOCKER_IMAGE, "validate", "-workspace", name]
    return None


def validate(workspace_path):
    """Run ``structurizr-cli validate``. Returns (ok, output).

    Returns ``(None, message)`` when neither the CLI nor a running Docker is available.
    """
    command = _command(workspace_path)
    if command is None:
        return None, "structurizr-cli not found and Docker not running; skipping validation"
    try:
        result = subprocess.run(command, capture_output=True, text=True)
    except OSError as error:
        return None, f"could not run {command[0]}: {error}; skipping validation"
    return result.returncode == 0, (result.stdout + result.stderr).strip()
