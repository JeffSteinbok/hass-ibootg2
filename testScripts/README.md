# Test Scripts

Helper scripts for developing and deploying the Dataprobe DxP integration.

## dxp_cli.py

Talk directly to an iBoot / iBoot-G2 / iBoot Bar device using the vendored
`dxp.py` client — no Home Assistant required. Useful to confirm the IP,
credentials and relay numbering before configuring the integration.

```bash
# Show the state of every relay
python testScripts/dxp_cli.py --host 192.168.1.50 status

# Turn relay 1 on / off
python testScripts/dxp_cli.py --host 192.168.1.50 on
python testScripts/dxp_cli.py --host 192.168.1.50 off

# Target a specific relay on a multi-outlet iBoot Bar
python testScripts/dxp_cli.py --host 192.168.1.50 --relay 2 --num-relays 8 on

# Provide credentials (default admin/admin, or set DXP_USER / DXP_PASSWORD)
python testScripts/dxp_cli.py --host 192.168.1.50 -u admin -p secret status
```

Exit codes: `0` success, `1` command not acknowledged, `2` connection/protocol error.

## deploy_to_ha.py

Copy the integration into a Home Assistant instance's `custom_components`
folder. Uses `robocopy` on Windows and `rsync` on macOS/Linux.

```bash
# Windows (mapped drive or UNC path to your HA config share)
python testScripts/deploy_to_ha.py --ha-path Z:\config\custom_components

# macOS/Linux
python testScripts/deploy_to_ha.py --ha-path /Volumes/config/custom_components
```

The integration is copied to `<ha-path>/dataprobe_dxp`. Restart Home Assistant
or reload the integration afterwards. To avoid passing `--ha-path` every time,
set `DEFAULT_HA_CUSTOM_COMPONENTS` near the top of the script.
