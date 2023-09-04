"""Microsoft Family Safety integration."""

import logging

from pyfamilysafety import FamilySafety
from pyfamilysafety.exceptions import HttpException

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import (
    ConfigEntryAuthFailed,
    HomeAssistantError
)

from .const import DOMAIN
from .coordinator import FamilySafetyCoordinator

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Setup Family Safety from a ConfigEntry."""
    hass.data.setdefault(DOMAIN, {})
    _LOGGER.debug("Got request to setup entry.")
    try:
        familysafety = None
        if len(entry.data["refresh_token"]) > 0:
            familysafety = await FamilySafety.create(
               token=entry.data["refresh_token"],
               use_refresh_token=True
            )
        else:
            familysafety = await FamilySafety.create(
               token=entry.data["response_url"],
               use_refresh_token=False
            )
        _LOGGER.debug("Login successful, setting up coordinator.")
        hass.data[DOMAIN][entry.entry_id] = FamilySafetyCoordinator(
            hass,
            familysafety,
            entry.data["update_interval"])
        # no need to fetch initial data as this is already handled on creation
    except HttpException as err:
        _LOGGER.error(err)
        raise ConfigEntryAuthFailed from err
    except Exception as err:
        _LOGGER.error(err)
        raise CannotConnect from err

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading config entry %s", entry.entry_id)
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
