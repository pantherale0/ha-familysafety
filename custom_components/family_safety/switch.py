"""Family Safety switch platform."""

import logging
from typing import Any

from pyfamilysafety import Account

from homeassistant.components.switch import SwitchEntity, SwitchDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import FamilySafetyCoordinator

from .const import (
    DOMAIN,
    DEFAULT_OVERRIDE_ENTITIES
)

from .entity_base import PlatformOverrideEntity, ApplicationEntity

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Family Safety switches."""
    accounts: list[Account] = hass.data[DOMAIN][config_entry.entry_id].api.accounts
    entities = []
    for account in accounts:
        if (config_entry.options.get("accounts", None) is None) or (
            account.user_id in config_entry.options.get("accounts", [])) or (
            len(config_entry.options.get("accounts", []))==0
        ):
            for platform in DEFAULT_OVERRIDE_ENTITIES:
                entities.append(
                    PlatformOverrideSwitch(
                        coordinator=hass.data[DOMAIN][config_entry.entry_id],
                        idx=None,
                        account_id=account.user_id,
                        platform=platform
                    )
                )
            for app in config_entry.options.get("tracked_applications", []):
                entities.append(
                    ApplicationBlockSwitch(
                        coordinator=hass.data[DOMAIN][config_entry.entry_id],
                        idx=None,
                        account_id=account.user_id,
                        app_id=app
                    )
                )

    async_add_entities(entities, True)

class ApplicationBlockSwitch(ApplicationEntity, SwitchEntity):
    """Define application switch."""

    @property
    def name(self) -> str:
        """Return entity name."""
        return f"Block {self._application.name}"

    @property
    def is_on(self) -> bool:
        """Return entity state."""
        return self._application.blocked

    @property
    def device_class(self) -> SwitchDeviceClass | None:
        """Return device class."""
        return SwitchDeviceClass.SWITCH

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off entity."""
        await self._application.unblock_app()
        await self.coordinator.async_request_refresh()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on entity."""
        await self._application.block_app()
        await self.coordinator.async_request_refresh()

class PlatformOverrideSwitch(PlatformOverrideEntity, SwitchEntity):
    """Platform override switch."""

    def __init__(self,
                 coordinator: FamilySafetyCoordinator,
                 idx,
                 account_id,
                 platform) -> None:
        super().__init__(coordinator, idx, account_id, platform)

    @property
    def name(self) -> str:
        """Return entity name."""
        return f"Block {str(self._platform)}"

    @property
    def is_on(self) -> bool:
        """Return entity state."""
        return self._get_override_state

    @property
    def device_class(self) -> SwitchDeviceClass | None:
        """Return device class."""
        return SwitchDeviceClass.SWITCH

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on entity."""
        return await self._enable_override()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off entity."""
        return await self._disable_override()
