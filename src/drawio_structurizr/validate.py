"""Run structurizr-cli on a generated workspace: validate it, or export it.

Uses a local ``structurizr-cli`` (or ``structurizr.sh``) on PATH when one is
installed, otherwise the ``structurizr/cli`` Docker image when Docker is
running. https://docs.structurizr.com/cli
"""

import os
import shutil
import subprocess

CLI_NAMES = ("structurizr-cli", "structurizr.sh", "structurizr")
# same structurizr-cli version as the Dockerfile; keep the two in step
DOCKER_IMAGE = "structurizr/cli:2025.11.09"
DOCKER_WORKDIR = "/usr/local/structurizr"
DOCKER_OUTPUT = "/output"

# formats accepted by `structurizr-cli export -format`
EXPORT_FORMATS = ("json", "plantuml", "plantuml/c4plantuml", "mermaid", "dot", "ilograph", "websequencediagrams")

NOT_FOUND = "structurizr-cli not found and Docker not running"


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


def availability():
    """Describe what was checked to find a validator, as (what, result) pairs."""
    cli = find_cli()
    checks = [("structurizr-cli on PATH", f"found at {cli}" if cli else "not found")]
    docker = shutil.which("docker")
    if docker is None:
        checks.append(("docker", "not found"))
    else:
        checks.append(("docker", "running" if _docker_running(docker) else f"found at {docker}, but not running"))
    return checks


def is_available():
    return find_cli() is not None or any(result == "running" for what, result in availability() if what == "docker")


def _command(workspace_path, action="validate", extra=(), output_dir=None):
    """Build the structurizr-cli command line, or return None if none is available."""
    cli = find_cli()
    if cli is not None:
        command = [cli, action, "-workspace", str(workspace_path), *extra]
        if output_dir is not None:
            command += ["-output", str(output_dir)]
        return command

    docker = shutil.which("docker")
    if docker is not None and _docker_running(docker):
        folder, name = os.path.split(os.path.abspath(workspace_path))
        command = [docker, "run", "--rm", "-v", f"{folder}:{DOCKER_WORKDIR}"]
        if output_dir is not None:
            command += ["-v", f"{os.path.abspath(output_dir)}:{DOCKER_OUTPUT}"]
        command += [DOCKER_IMAGE, action, "-workspace", name, *extra]
        if output_dir is not None:
            command += ["-output", DOCKER_OUTPUT]
        return command
    return None


def _run(command):
    try:
        result = subprocess.run(command, capture_output=True, text=True)
    except OSError as error:
        return None, f"could not run {command[0]}: {error}"
    return result.returncode == 0, (result.stdout + result.stderr).strip()


def validate(workspace_path):
    """Run ``structurizr-cli validate``. Returns (ok, output).

    Returns ``(None, message)`` when neither the CLI nor a running Docker is available.
    """
    command = _command(workspace_path)
    if command is None:
        return None, f"{NOT_FOUND}; skipping validation"
    ok, output = _run(command)
    return ok, output if ok is not None else f"{output}; skipping validation"


def export(workspace_path, fmt, output_dir):
    """Run ``structurizr-cli export`` into ``output_dir``. Returns (ok, output).

    Returns ``(None, message)`` when neither the CLI nor a running Docker is available.
    """
    os.makedirs(output_dir, exist_ok=True)
    command = _command(workspace_path, "export", ["-format", fmt], output_dir)
    if command is None:
        return None, f"{NOT_FOUND}; cannot export {fmt}"
    return _run(command)
