"""Contains the base definition of an entity."""

import logging

from pyfamilysafety import Account

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
