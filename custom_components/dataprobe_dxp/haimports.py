"""Include all HA imports here.

Single file for all Home Assistant imports so that we can include this in all
other files, and disable linting in one specific place.
"""

# pylint: disable=unused-import, wildcard-import, unused-wildcard-import

import voluptuous as vol

from homeassistant import config_entries, core
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
    Platform,
    STATE_OFF,
    STATE_ON,
)
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity import DeviceInfo, Entity, EntityDescription
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from homeassistant.components.switch import (
    SwitchEntity,
    SwitchEntityDescription,
)
