# Dataprobe DxP (iBoot) — Home Assistant Integration

A simple Home Assistant custom integration to control Dataprobe **iBoot**,
**iBoot-G2** and **iBoot Bar** devices as switches, using the local **DxP**
binary protocol (TCP, default port `9100`). No cloud, no external dependencies.

Each outlet/relay on the device is exposed as a Home Assistant `switch` entity.

## Features

- Local control over the DxP protocol (default port `9100`)
- Turn outlets on/off and read their current state
- Supports single-outlet (iBoot, iBoot-G2) and multi-outlet (iBoot Bar) devices
- UI config flow — no YAML required
- Zero external Python dependencies (client is vendored in `dxp.py`)

## Installation

### HACS (custom repository)

1. In HACS → Integrations → ⋮ → **Custom repositories**, add this repo as an
   *Integration*.
2. Install **Dataprobe DxP (iBoot)** and restart Home Assistant.

### Manual

Copy `custom_components/dataprobe_dxp` into your Home Assistant
`config/custom_components/` directory and restart. During development you can
use `testScripts/deploy_to_ha.py` (see `testScripts/README.md`).

## Configuration

1. Settings → Devices & Services → **Add Integration** → *Dataprobe DxP (iBoot)*.
2. Enter:
   - **Host** — the device IP or hostname
   - **Port** — DxP port (default `9100`)
   - **Username / Password** — device credentials (factory default `admin` / `admin`)
   - **Number of outlets/relays** — `1` for iBoot / iBoot-G2, or the outlet count
     for an iBoot Bar

The integration validates the connection during setup and creates one switch
per outlet.

## Testing without Home Assistant

Use the CLI to verify connectivity and relay numbering:

```bash
python testScripts/dxp_cli.py --host 192.168.1.50 status
python testScripts/dxp_cli.py --host 192.168.1.50 on
```

See `testScripts/README.md` for details.

## Protocol notes

The DxP protocol is a small binary protocol: connect over TCP, send the
`hello-000` greeting, receive a 2-byte sequence number, then send fixed-layout
command packets. This integration implements just the relay read/change
commands. The client lives in `custom_components/dataprobe_dxp/dxp.py`.

## Disclaimer

Not affiliated with or endorsed by Dataprobe. "iBoot" is a trademark of its
respective owner.
