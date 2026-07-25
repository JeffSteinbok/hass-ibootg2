#!/usr/bin/env python3
"""Command-line tester for the Dataprobe DxP client.

Talks directly to an iBoot / iBoot-G2 / iBoot Bar device using the vendored
``dxp.py`` client, without needing Home Assistant. Handy for confirming
credentials, IP, relay numbering and firmware behaviour before wiring the
integration into HA.

Examples
--------
    python testScripts/dxp_cli.py --host 192.168.1.50 status
    python testScripts/dxp_cli.py --host 192.168.1.50 on
    python testScripts/dxp_cli.py --host 192.168.1.50 --relay 2 off
    python testScripts/dxp_cli.py --host 192.168.1.50 -u admin -p secret status

Credentials default to admin/admin (the iBoot factory default). Override with
--user/--password or the DXP_USER / DXP_PASSWORD environment variables.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Allow importing the vendored client from the integration package.
_CLIENT_DIR = Path(__file__).resolve().parent.parent / "custom_components" / "dataprobe_dxp"
sys.path.insert(0, str(_CLIENT_DIR))

# Allow importing the gitignored secrets/credentials.py.
_SECRETS_DIR = Path(__file__).resolve().parent / "secrets"
sys.path.insert(0, str(_SECRETS_DIR))

from dxp import DEFAULT_PORT, DxpClient, DxpError  # noqa: E402  pylint: disable=C0413

try:
    import credentials as _creds  # noqa: E402  pylint: disable=C0413
except ImportError:
    _creds = None


def _default(name: str, fallback):
    """Return the value from secrets/credentials.py if present, else fallback."""
    if _creds is not None and hasattr(_creds, name):
        return getattr(_creds, name)
    return fallback


def _build_client(args: argparse.Namespace) -> DxpClient:
    return DxpClient(
        host=args.host,
        username=args.user,
        password=args.password,
        port=args.port,
        num_relays=args.num_relays,
    )


def _print_status(client: DxpClient) -> int:
    states = client.get_relays()
    if not states:
        print("Device returned no relay states.")
        return 1
    for index, state in enumerate(states, start=1):
        print(f"Relay {index}: {'ON' if state else 'OFF'}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Parse arguments and run the requested command."""
    parser = argparse.ArgumentParser(
        description="Control or query a Dataprobe DxP (iBoot) device."
    )
    parser.add_argument(
        "--host",
        default=_default("HOST", None),
        help="Device IP address or hostname (default from secrets/credentials.py).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=_default("PORT", DEFAULT_PORT),
        help=f"TCP port (default {DEFAULT_PORT} or from secrets).",
    )
    parser.add_argument(
        "-u",
        "--user",
        default=os.environ.get("DXP_USER", _default("USERNAME", "admin")),
        help="Username (default from secrets, 'admin', or $DXP_USER).",
    )
    parser.add_argument(
        "-p",
        "--password",
        default=os.environ.get("DXP_PASSWORD", _default("PASSWORD", "admin")),
        help="Password (default from secrets, 'admin', or $DXP_PASSWORD).",
    )
    parser.add_argument(
        "-r",
        "--relay",
        type=int,
        default=1,
        help="Relay/outlet number for on/off (1-based, default 1).",
    )
    parser.add_argument(
        "-n",
        "--num-relays",
        type=int,
        default=_default("NUM_RELAYS", 1),
        help="Number of relays the device exposes (default 1 or from secrets).",
    )
    parser.add_argument(
        "command",
        choices=["on", "off", "status"],
        help="Action to perform.",
    )

    args = parser.parse_args(argv)

    if not args.host:
        parser.error(
            "no host provided. Set HOST in testScripts/secrets/credentials.py "
            "or pass --host."
        )

    client = _build_client(args)

    try:
        if args.command == "status":
            return _print_status(client)

        want_on = args.command == "on"
        ok = client.set_relay(args.relay, want_on)
        action = "ON" if want_on else "OFF"
        if ok:
            print(f"Relay {args.relay} turned {action}.")
            return 0
        print(f"Device did not acknowledge turning relay {args.relay} {action}.")
        return 1
    except DxpError as err:
        print(f"Error: {err}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
