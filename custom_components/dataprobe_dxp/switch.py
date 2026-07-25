"""Switch platform for the Dataprobe DxP integration."""

from __future__ import annotations

import logging
from typing import Any

from .haimports import *  # pylint: disable=W0401,W0614
from .const import (
    LOGGER,
    DOMAIN,
    DATAPROBE_DXP_MANAGER,
    MANUFACTURER,
    MODEL,
)
from .manager import DataProbeDxpManager

_LOGGER = logging.getLogger(LOGGER)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Dataprobe DxP switch platform."""
    manager: DataProbeDxpManager = hass.data[DOMAIN][config_entry.entry_id][
        DATAPROBE_DXP_MANAGER
    ]

    entities = [
        DataProbeDxpSwitch(manager, relay)
        for relay in range(1, manager.num_relays + 1)
    ]
    async_add_entities(entities)


class DataProbeDxpSwitch(SwitchEntity):
    """A single relay/outlet on a Dataprobe DxP device."""

    _attr_has_entity_name = True

    def __init__(self, manager: DataProbeDxpManager, relay: int) -> None:
        self._manager = manager
        self._relay = relay
        self._attr_unique_id = f"{manager.host}:{manager.port}-relay{relay}"

        if manager.num_relays > 1:
            self._attr_name = f"Outlet {relay}"
        else:
            self._attr_name = "Outlet"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info so all relays group under one device."""
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self._manager.host}:{self._manager.port}")},
            name=self._manager.name,
            manufacturer=MANUFACTURER,
            model=MODEL,
        )

    @property
    def available(self) -> bool:
        """Return True if the device is reachable."""
        return self._manager.available

    @property
    def is_on(self) -> bool:
        """Return True if the relay is on."""
        return self._manager.relay_states[self._relay - 1]

    def turn_on(self, **kwargs: Any) -> None:
        """Turn the relay on."""
        _LOGGER.debug("Turning on relay %s on %s", self._relay, self._manager.host)
        self._manager.set_relay(self._relay, True)

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the relay off."""
        _LOGGER.debug("Turning off relay %s on %s", self._relay, self._manager.host)
        self._manager.set_relay(self._relay, False)

    def update(self) -> None:
        """Poll the device for the latest relay states (throttled in manager)."""
        self._manager.update()
