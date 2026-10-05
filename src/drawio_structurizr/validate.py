"""Optional: validate a generated workspace with structurizr-cli.

Requires ``structurizr-cli`` (or ``structurizr.sh``) on PATH:
https://docs.structurizr.com/cli
"""

import shutil
import subprocess

CLI_NAMES = ("structurizr-cli", "structurizr.sh", "structurizr")


def find_cli():
    for name in CLI_NAMES:
        path = shutil.which(name)
        if path:
            return path
    return None


def validate(workspace_path):
    """Run ``structurizr-cli validate``. Returns (ok, output).

    Returns ``(None, message)`` when the CLI is not installed.
    """
    cli = find_cli()
    if cli is None:
        return None, "structurizr-cli not found on PATH; skipping validation"
    result = subprocess.run(
        [cli, "validate", "-workspace", str(workspace_path)],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0, (result.stdout + result.stderr).strip()
