"""Family Safety switch platform."""

import logging
from typing import Any

from pyfamilysafety import Account

from homeassistant.components.switch import SwitchEntity, SwitchDeviceClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import FamilySafetyCoordinator

from .const import DOMAIN, DEFAULT_OVERRIDE_ENTITIES
from .config_entry import FamilySafetyConfigEntry
from .entity_base import PlatformOverrideEntity, ApplicationEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: FamilySafetyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Family Safety switches."""
    accounts: list[Account] = config_entry.runtime_data.api.accounts
    entities = []
    for account in accounts:
        if (
            (config_entry.options.get("accounts", None) is None)
            or (account.user_id in config_entry.options.get("accounts", []))
            or (len(config_entry.options.get("accounts", [])) == 0)
        ):
            for platform in DEFAULT_OVERRIDE_ENTITIES:
                entities.append(
                    PlatformOverrideSwitch(
                        coordinator=config_entry.runtime_data,
                        idx=None,
                        account_id=account.user_id,
                        platform=platform,
                    )
                )
            for app in config_entry.options.get("tracked_applications", []):
                entities.append(
                    ApplicationBlockSwitch(
                        coordinator=config_entry.runtime_data,
                        idx=None,
                        account_id=account.user_id,
                        app_id=app,
                    )
                )

    async_add_entities(entities, True)


class ApplicationBlockSwitch(ApplicationEntity, SwitchEntity):
    """Define application switch."""

    @property
    def name(self) -> str:
        """Return entity name."""
        return f"{self._account.first_name} Block {self._application.name}"

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
        self.schedule_update_ha_state()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on entity."""
        await self._application.block_app()
        self.schedule_update_ha_state()


class PlatformOverrideSwitch(PlatformOverrideEntity, SwitchEntity):
    """Platform override switch."""

    def __init__(
        self, coordinator: FamilySafetyCoordinator, idx, account_id, platform
    ) -> None:
        """Create PlatformOverrideSwitch."""
        super().__init__(coordinator, idx, account_id, platform)

    @property
    def name(self) -> str:
        """Return entity name."""
        return f"{self._account.first_name} Block {str(self._platform)}"

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
        await self._enable_override()
        self.schedule_update_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off entity."""
        await self._disable_override()
        self.schedule_update_ha_state()
