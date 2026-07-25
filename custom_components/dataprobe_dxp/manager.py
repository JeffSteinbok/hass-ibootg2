"""Manager that owns the DxP client and caches relay state for Home Assistant."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.util import Throttle

from .const import LOGGER
from .dxp import DxpClient, DxpError

_LOGGER = logging.getLogger(LOGGER)

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=15)


class DataProbeDxpManager:
    """Owns a single DxP device connection and the last known relay states.

    The manager runs blocking socket I/O; call its methods from an executor
    (``hass.async_add_executor_job``). Relay indexes are 1-based to match the
    DxP protocol.
    """

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        num_relays: int,
        name: str | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.num_relays = num_relays
        self.name = name or host
        self.available = False
        self.relay_states: list[bool] = [False] * num_relays
        self._client = DxpClient(host, username, password, port, num_relays)

    def test_connection(self) -> bool:
        """Attempt an initial read to validate the connection. Blocking."""
        try:
            self._store_states(self._client.get_relays())
            self.available = True
            return True
        except DxpError as err:
            _LOGGER.error("test_connection: Unable to reach %s: %s", self.host, err)
            self.available = False
            return False

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self) -> None:
        """Refresh relay states from the device. Blocking and throttled."""
        try:
            self._store_states(self._client.get_relays())
            self.available = True
        except DxpError as err:
            _LOGGER.warning("update: Unable to read %s: %s", self.host, err)
            self.available = False

    def set_relay(self, relay: int, on: bool) -> bool:
        """Turn a relay on or off and update the cached state. Blocking."""
        try:
            ok = self._client.set_relay(relay, on)
        except DxpError as err:
            _LOGGER.error("set_relay: Failed to set relay %s on %s: %s", relay, self.host, err)
            self.available = False
            return False

        if ok:
            self.relay_states[relay - 1] = on
            self.available = True
        return ok

    def _store_states(self, states: list[bool]) -> None:
        """Cache relay states, padding/truncating to the configured count."""
        padded = list(states[: self.num_relays])
        padded += [False] * (self.num_relays - len(padded))
        self.relay_states = padded
