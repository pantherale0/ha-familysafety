"""Sensors for family safety."""

from collections.abc import Mapping
import logging
from typing import Any

from pyfamilysafety import Account

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import FamilySafetyCoordinator

from .const import (
    DOMAIN
)

from .entity_base import ManagedAccountEntity

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Family Safety sensors."""
    accounts: list[Account] = hass.data[DOMAIN][config_entry.entry_id].api.accounts
    entities = []
    for account in accounts:
        if (account.user_id in config_entry.options.get("accounts", [])) or (
            len(config_entry.options.get("accounts", []))==0
        ):
            entities.append(
                AccountScreentimeSensor(
                    coordinator=hass.data[DOMAIN][config_entry.entry_id],
                    idx=None,
                    account_id=account.user_id
                )
            )
            for app in config_entry.options.get("tracked_applications", []):
                entities.append(
                    ApplicationScreentimeSensor(
                        coordinator=hass.data[DOMAIN][config_entry.entry_id],
                        idx=None,
                        account_id=account.user_id,
                        app_id=app
                    )
                )

    async_add_entities(entities, True)

class AccountScreentimeSensor(ManagedAccountEntity, SensorEntity):
    """Aggregate screentime sensor."""

    def __init__(self, coordinator: FamilySafetyCoordinator, idx, account_id) -> None:
        super().__init__(coordinator, idx, account_id, "screentime")

    @property
    def name(self) -> str:
        return "Used Screen Time"

    @property
    def native_value(self) -> float:
        """Return duration (minutes)"""
        return (self._account.today_screentime_usage/1000)/60

    @property
    def native_unit_of_measurement(self) -> str | None:
        return "min"

    @property
    def device_class(self) -> SensorDeviceClass | None:
        return SensorDeviceClass.DURATION

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        devices = {}
        for device in self._account.devices:
            if device.today_time_used:
                devices[device.device_name] = (device.today_time_used/1000)/60
            else:
                devices[device.device_name] = 0
        applications = {}
        for app in self._account.applications:
            applications[app.name] = app.usage
        return {
            "application_usage": applications,
            "device_usage": devices
        }

class ApplicationScreentimeSensor(ManagedAccountEntity, SensorEntity):
    """Application specific screentime sensor"""

    def __init__(self,
                 coordinator: FamilySafetyCoordinator,
                 idx,
                 account_id,
                 app_id) -> None:
        super().__init__(coordinator, idx, account_id, f"{app_id}_screentime")
        self._app_id = app_id

    @property
    def name(self) -> str:
        return f"{self._application.name} Used Screen Time"

    @property
    def _application(self):
        """Return the application."""
        return self._account.get_application(self._app_id)

    @property
    def native_value(self) -> float:
        """Return duration (minutes)"""
        return self._application.usage

    @property
    def native_unit_of_measurement(self) -> str | None:
        return "min"

    @property
    def device_class(self) -> SensorDeviceClass | None:
        return SensorDeviceClass.DURATION

    @property
    def icon(self) -> str | None:
        return self._application.icon

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        return {
            "blocked": self._application.blocked
        }
