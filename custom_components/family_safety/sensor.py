"""Sensors for family safety."""

from collections.abc import Mapping
import logging
from typing import Any

import voluptuous as vol

from pyfamilysafety import Account

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback, async_get_current_platform

from .coordinator import FamilySafetyCoordinator

from .const import (
    DOMAIN
)

from .entity_base import ManagedAccountEntity, ApplicationEntity

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
            entities.append(
                AccountBalanceSensor(
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
    # register services
    platform = async_get_current_platform()
    platform.async_register_entity_service(
        name="block_app",
        schema={
            vol.Required("name"): str
        },
        func="async_block_application"
    )
    platform.async_register_entity_service(
        name="unblock_app",
        schema={
            vol.Required("name"): str
        },
        func="async_unblock_application"
    )

class AccountBalanceSensor(ManagedAccountEntity, SensorEntity):
    """A balance sensor for the account."""

    def __init__(self, coordinator: FamilySafetyCoordinator, idx, account_id) -> None:
        """Account Balance Sensor."""
        super().__init__(coordinator, idx, account_id, "balance")

    @property
    def name(self) -> str:
        """Return name of entity."""
        return "Available Balance"

    @property
    def native_value(self) -> float:
        """Return balance."""
        return self._account.account_balance

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return unit of measurement."""
        return self._account.account_currency

    @property
    def device_class(self) -> SensorDeviceClass | None:
        """Return device class."""
        return SensorDeviceClass.MONETARY

class AccountScreentimeSensor(ManagedAccountEntity, SensorEntity):
    """Aggregate screentime sensor."""

    def __init__(self, coordinator: FamilySafetyCoordinator, idx, account_id) -> None:
        """Screentime Sensor."""
        super().__init__(coordinator, idx, account_id, "screentime")

    @property
    def name(self) -> str:
        """Return entity name."""
        return "Used Screen Time"

    @property
    def native_value(self) -> float:
        """Return duration (minutes)."""
        return (self._account.today_screentime_usage/1000)/60

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return unit of measurement."""
        return "min"

    @property
    def device_class(self) -> SensorDeviceClass | None:
        """Return device class."""
        return SensorDeviceClass.DURATION

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return additional state attributes."""
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

class ApplicationScreentimeSensor(ApplicationEntity, SensorEntity):
    """Application specific screentime sensor."""

    @property
    def name(self) -> str:
        """Return entity name."""
        return f"{self._application.name} Used Screen Time"

    @property
    def native_value(self) -> float:
        """Return duration (minutes)."""
        return self._application.usage

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return native unit of measurement."""
        return "min"

    @property
    def device_class(self) -> SensorDeviceClass | None:
        """Return device class."""
        return SensorDeviceClass.DURATION

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return additional state attributes."""
        return {
            "blocked": self._application.blocked
        }
