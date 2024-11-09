"""Contains the base definition of an entity."""

import logging

from datetime import datetime, time, timedelta

from pyfamilysafety import Account
from pyfamilysafety.application import Application
from pyfamilysafety.enum import OverrideTarget, OverrideType

import homeassistant.helpers.device_registry as dr
from homeassistant.helpers.entity import DeviceInfo, Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.exceptions import ServiceValidationError

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
        """Create a ManagedAccountEntity."""
        super().__init__(coordinator, idx)
        self._account_id = account_id
        self._entity_id = entity_id
        self.coordinator: FamilySafetyCoordinator = coordinator

    @property
    def _account(self) -> Account:
        """Return the managed account."""
        return self.coordinator.api.get_account(self._account_id)

    @property
    def unique_id(self) -> str:
        """Return a unique ID for the entity."""
        return f"{self._account_id}_{self._entity_id}"

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

    async def async_approve_request(self, request_id: str, extension_time: int):
        """Approve a pending request."""
        try:
            await self.coordinator.api.approve_pending_request(
                request_id=request_id,
                extension_time=extension_time
            )
        except ValueError:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_request_id"
            )

    async def async_deny_request(self, request_id: str):
        """Deny a pending request."""
        try:
            await self.coordinator.api.deny_pending_request(request_id=request_id)
        except ValueError:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_request_id"
            )


class ApplicationEntity(ManagedAccountEntity):
    """Define a application entity."""

    def __init__(self,
                 coordinator: FamilySafetyCoordinator,
                 idx,
                 account_id,
                 app_id: str) -> None:
        """Create a application entity."""
        super().__init__(coordinator, idx, account_id,
                         f"override_{str(app_id).lower()}")
        self._app_id = app_id

    @property
    def _application(self) -> Application:
        """Get the application."""
        return self._account.get_application(self._app_id)

    @property
    def icon(self) -> str | None:
        """Get the application icon."""
        return self._application.icon


class PlatformOverrideEntity(ManagedAccountEntity):
    """Defines a managed device."""

    def __init__(self,
                 coordinator: FamilySafetyCoordinator,
                 idx,
                 account_id,
                 platform: OverrideTarget) -> None:
        """Create a PlatformOverride entity."""
        super().__init__(coordinator, idx, account_id,
                         f"override_{str(platform).lower()}")
        self._platform = platform

    @property
    def _get_override_state(self) -> bool:
        """Get the current state if the override is active or not."""
        for override in self._account.blocked_platforms:
            if override == self._platform:
                return True
        return False

    async def _enable_override(self, until: datetime = None):
        """Enable the override."""
        if until is None:
            until = datetime.combine(datetime.today(),
                                     time(hour=0, minute=0, second=0)) + timedelta(days=1)
        await self._account.override_device(self._platform, OverrideType.UNTIL, valid_until=until)

    async def _disable_override(self):
        """Disable the override."""
        await self._account.override_device(self._platform, OverrideType.CANCEL)
