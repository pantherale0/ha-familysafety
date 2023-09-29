"""Microsoft Family Safety integration."""

import logging

from pyfamilysafety import FamilySafety
from pyfamilysafety.exceptions import HttpException, Unauthorized, AggregatorException

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import (
    ConfigEntryAuthFailed,
    HomeAssistantError
)

from .const import DOMAIN, AGG_ERROR
from .coordinator import FamilySafetyCoordinator

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.SENSOR, Platform.SWITCH]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Create ConfigEntry."""
    hass.data.setdefault(DOMAIN, {})
    _LOGGER.debug("Got request to setup entry.")
    try:
        familysafety = await FamilySafety.create(
            token=entry.options.get("refresh_token", entry.data["refresh_token"]),
            use_refresh_token=True
        )
        _LOGGER.debug("Login successful, setting up coordinator.")
        hass.data[DOMAIN][entry.entry_id] = FamilySafetyCoordinator(
            hass,
            familysafety,
            entry.options.get("update_interval", entry.data["update_interval"]))
        # no need to fetch initial data as this is already handled on creation
    except AggregatorException as err:
        _LOGGER.error(AGG_ERROR)
        raise CannotConnect from err
    except Unauthorized as err:
        raise ConfigEntryAuthFailed from err
    except HttpException as err:
        _LOGGER.error(err)
        raise CannotConnect from err
    except Exception as err:
        _LOGGER.error(err)
        raise CannotConnect from err

    async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
        """Update listener."""
        await hass.config_entries.async_reload(entry.entry_id)

    entry.async_on_unload(entry.add_update_listener(update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading config entry %s", entry.entry_id)
    await hass.data[DOMAIN][entry.entry_id].api.api.end_session()
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
