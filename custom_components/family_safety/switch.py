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

from .entity_base import PlatformOverrideEntity

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

    async_add_entities(entities, True)

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
        return f"Block {str(self._platform)}"

    @property
    def is_on(self) -> bool:
        return self._get_override_state

    @property
    def device_class(self) -> SwitchDeviceClass | None:
        return SwitchDeviceClass.SWITCH

    async def async_turn_on(self, **kwargs: Any) -> None:
        return await self._enable_override()

    async def async_turn_off(self, **kwargs: Any) -> None:
        return await self._disable_override()
