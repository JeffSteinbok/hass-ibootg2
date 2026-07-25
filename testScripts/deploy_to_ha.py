#!/usr/bin/env python3
"""Deploy the Dataprobe DxP integration to a Home Assistant instance.

Copies ``custom_components/dataprobe_dxp`` into the target HA
``custom_components`` folder, excluding ``__pycache__`` and hidden files.

- On Windows: uses robocopy (mirror).
- On macOS/Linux: uses rsync.

Examples
--------
    python testScripts/deploy_to_ha.py --ha-path \\\\HAHOST\\config\\custom_components
    python testScripts/deploy_to_ha.py --ha-path Z:\\config\\custom_components
    python testScripts/deploy_to_ha.py --ha-path /Volumes/config/custom_components

The integration is copied into ``<ha-path>/dataprobe_dxp``. Restart Home
Assistant (or reload the integration) after deploying.
"""

from __future__ import annotations

import argparse
import platform
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
COMPONENT_NAME = "dataprobe_dxp"
COMPONENT_SRC = PROJECT_ROOT / "custom_components" / COMPONENT_NAME

# Set a default here to avoid passing --ha-path every time (points at the
# custom_components folder of your HA config, e.g. r"Z:\config\custom_components").
DEFAULT_HA_CUSTOM_COMPONENTS = None


def deploy_windows(dest: Path) -> bool:
    """Mirror the component to dest using robocopy."""
    cmd = [
        "robocopy",
        str(COMPONENT_SRC),
        str(dest),
        "/MIR",
        "/XD", "__pycache__",
        "/XF", ".*",
        "/NFL", "/NDL", "/NJH", "/NJS", "/NP",
    ]
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=False)
    # robocopy exit codes < 8 indicate success (files copied / no change).
    if result.returncode >= 8:
        print(f"Error during robocopy (exit code {result.returncode})")
        return False
    return True


def deploy_rsync(dest: Path) -> bool:
    """Mirror the component to dest using rsync."""
    cmd = [
        "rsync",
        "-rltvz",
        "--delete",
        "--no-perms",
        "--no-owner",
        "--exclude=__pycache__",
        "--exclude=.*",
        f"{COMPONENT_SRC}/",
        f"{dest}/",
    ]
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        print(f"Error during rsync (exit code {result.returncode})")
        return False
    return True


def main(argv: list[str] | None = None) -> int:
    """Parse arguments and run the deployment."""
    parser = argparse.ArgumentParser(
        description="Deploy the Dataprobe DxP integration to Home Assistant."
    )
    parser.add_argument(
        "--ha-path",
        default=DEFAULT_HA_CUSTOM_COMPONENTS,
        help="Path to the HA custom_components directory.",
    )
    args = parser.parse_args(argv)

    if not args.ha_path:
        print("Error: provide --ha-path (or set DEFAULT_HA_CUSTOM_COMPONENTS in the script).")
        return 1

    if not COMPONENT_SRC.is_dir():
        print(f"Error: source component not found: {COMPONENT_SRC}")
        return 1

    dest = Path(args.ha_path) / COMPONENT_NAME
    dest.mkdir(parents=True, exist_ok=True)
    print(f"Deploying {COMPONENT_SRC} -> {dest}")

    system = platform.system()
    if system == "Windows":
        ok = deploy_windows(dest)
    else:
        ok = deploy_rsync(dest)

    if ok:
        print("Deployment successful. Restart Home Assistant or reload the integration.")
        return 0

    print("Deployment failed.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
