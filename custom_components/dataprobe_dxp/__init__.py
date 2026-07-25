"""Dataprobe DxP (iBoot) Home Assistant Integration."""

import logging

from .haimports import *  # pylint: disable=W0401,W0614
from .const import (
    LOGGER,
    DOMAIN,
    DATAPROBE_DXP_MANAGER,
    DATAPROBE_DXP_PLATFORMS,
    CONF_NUM_RELAYS,
    DEFAULT_NUM_RELAYS,
    DEFAULT_PORT,
)
from .manager import DataProbeDxpManager

_LOGGER = logging.getLogger(LOGGER)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up Dataprobe DxP from a config entry."""
    _LOGGER.debug("async_setup_entry")

    host = config_entry.data.get(CONF_HOST)
    port = config_entry.data.get(CONF_PORT, DEFAULT_PORT)
    username = config_entry.data.get(CONF_USERNAME)
    password = config_entry.data.get(CONF_PASSWORD)
    num_relays = config_entry.data.get(CONF_NUM_RELAYS, DEFAULT_NUM_RELAYS)

    manager = DataProbeDxpManager(
        host=host,
        port=port,
        username=username,
        password=password,
        num_relays=num_relays,
    )

    connected = await hass.async_add_executor_job(manager.test_connection)
    if not connected:
        _LOGGER.error("Unable to connect to Dataprobe DxP device at %s:%s", host, port)
        raise ConfigEntryNotReady(f"Unable to connect to {host}:{port}")

    _LOGGER.info("Connected to Dataprobe DxP device at %s with %d relay(s)", host, num_relays)

    platforms = set()
    platforms.add(Platform.SWITCH)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][config_entry.entry_id] = {
        DATAPROBE_DXP_MANAGER: manager,
        DATAPROBE_DXP_PLATFORMS: platforms,
    }

    await hass.config_entries.async_forward_entry_setups(config_entry, platforms)
    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    entry_data = hass.data.get(DOMAIN, {}).get(config_entry.entry_id)
    if entry_data is None:
        return True

    unload_ok = await hass.config_entries.async_unload_platforms(
        config_entry,
        entry_data[DATAPROBE_DXP_PLATFORMS],
    )

    if unload_ok:
        hass.data[DOMAIN].pop(config_entry.entry_id)
        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN)

    return unload_ok
