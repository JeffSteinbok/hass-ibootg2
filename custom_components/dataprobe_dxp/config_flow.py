"""Config flow for the Dataprobe DxP integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from .haimports import *  # pylint: disable=W0401,W0614
from .const import (
    DOMAIN,
    CONF_NUM_RELAYS,
    DEFAULT_NUM_RELAYS,
    DEFAULT_PORT,
    LOGGER,
)
from .manager import DataProbeDxpManager

_LOGGER = logging.getLogger(LOGGER)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Required(CONF_USERNAME, default="admin"): str,
        vol.Required(CONF_PASSWORD, default="admin"): str,
        vol.Required(CONF_NUM_RELAYS, default=DEFAULT_NUM_RELAYS): int,
    }
)


class DataProbeDxpFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Dataprobe DxP config flow."""

    VERSION = 1

    @callback
    def _show_form(self, errors=None):
        """Show the setup form to the user."""
        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors if errors else {},
        )

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle a flow start."""
        if user_input is None:
            return self._show_form()

        host = user_input[CONF_HOST]
        port = user_input[CONF_PORT]

        await self.async_set_unique_id(f"{host}:{port}")
        self._abort_if_unique_id_configured()

        manager = DataProbeDxpManager(
            host=host,
            port=port,
            username=user_input[CONF_USERNAME],
            password=user_input[CONF_PASSWORD],
            num_relays=user_input[CONF_NUM_RELAYS],
        )

        connected = await self.hass.async_add_executor_job(manager.test_connection)
        if not connected:
            return self._show_form(errors={"base": "cannot_connect"})

        return self.async_create_entry(title=host, data=user_input)
