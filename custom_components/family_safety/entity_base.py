"""Contains the base definition of an entity."""

import logging

from datetime import datetime, time, timedelta

from pyfamilysafety import Account
from pyfamilysafety.application import Application
from pyfamilysafety.enum import OverrideTarget, OverrideType

import homeassistant.helpers.device_registry as dr
from homeassistant.helpers.entity import DeviceInfo, Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import FamilySafetyCoordinator

_LOGGER = logging.getLogger(__name__)

class ManagedAccountEntity(CoordinatorEntity, Entity):
    """Base class for all managed account entities."""

    def __init__(self,
                 coordinator: FamilySafetyCoordinator,
                 idx,
                 account_id,
                 entity_id) -> None:
        super().__init__(coordinator, idx)
        self._account_id = account_id
        self._entity_id = entity_id
        self.coordinator: FamilySafetyCoordinator = coordinator

    @property
    def _account(self) -> Account:
        """Returns the managed account"""
        return self.coordinator.api.get_account(self._account_id)

    @property
    def unique_id(self) -> str:
        """Returns a unique ID for the entity."""
        return f"familysafety_{self._account_id}_{self._entity_id}"

    @property
    def device_info(self):
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, f"familysafety_{self._account_id}")},
            manufacturer="Microsoft",
            name=str(self._account.first_name),
            entry_type=dr.DeviceEntryType.SERVICE
        )

    async def async_block_application(self, name: str):
        """Blocks a application with a given app name."""
        await [a for a in self._account.applications if a.name == name][0].block_app()

    async def async_unblock_application(self, name: str):
        """Blocks a application with a given app name."""
        await [a for a in self._account.applications if a.name == name][0].unblock_app()

class ApplicationEntity(ManagedAccountEntity):
    """Defines a application entity."""
    def __init__(self,
                 coordinator: FamilySafetyCoordinator,
                 idx,
                 account_id,
                 app_id: str) -> None:
        """init entity."""
        super().__init__(coordinator, idx, account_id, f"override_{str(app_id).lower()}")
        self._app_id = app_id

    @property
    def _application(self) -> Application:
        """Gets the application."""
        return self._account.get_application(self._app_id)

    @property
    def icon(self) -> str | None:
        return self._application.icon


class PlatformOverrideEntity(ManagedAccountEntity):
    """Defines a managed device."""

    def __init__(self,
                 coordinator: FamilySafetyCoordinator,
                 idx,
                 account_id,
                 platform: OverrideTarget) -> None:
        """init entity."""
        super().__init__(coordinator, idx, account_id, f"override_{str(platform).lower()}")
        self._platform = platform

    @property
    def _get_override_state(self) -> bool:
        """Gets a state if the override is active or not."""
        for override in self._account.blocked_platforms:
            if override == self._platform or override == OverrideTarget.ALL_DEVICES:
                return True
        return False

    async def _enable_override(self, until: datetime = None):
        """Enables the override."""
        if until is None:
            until = datetime.combine(datetime.today(),
                                     time(hour=0, minute=0, second=0)) + timedelta(days=1)
        await self._account.override_device(self._platform, OverrideType.UNTIL, valid_until=until)
        await self.coordinator.async_request_refresh()

    async def _disable_override(self):
        """Disables the override."""
        await self._account.override_device(self._platform, OverrideType.CANCEL)
        await self.coordinator.async_request_refresh()
