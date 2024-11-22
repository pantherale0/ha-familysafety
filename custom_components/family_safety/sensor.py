"""Sensors for family safety."""

from collections.abc import Mapping, Callable
from dataclasses import dataclass
from datetime import datetime
import logging
from typing import Any

import voluptuous as vol

from pyfamilysafety import Account
from pyfamilysafety.application import Application

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription, SensorDeviceClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import (
    AddEntitiesCallback,
    async_get_current_platform,
)

from .coordinator import FamilySafetyCoordinator

from .const import DOMAIN, CONF_KEY_EXPR, CONF_EXPR_DEFAULT
from .config_entry import FamilySafetyConfigEntry

from .entity_base import ManagedAccountEntity

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class FamilySafetySensorEntityDescription(SensorEntityDescription):
    """Describes family_safety sensor entity."""

    value_fn: Callable[[ManagedAccountEntity], str | int | datetime]
    name_fn: Callable[[ManagedAccountEntity], str]
    native_unit_of_measurement_fn: Callable[[ManagedAccountEntity], str]


GEN_SENSORS: dict[str, FamilySafetySensorEntityDescription] = {
    "account_balance": FamilySafetySensorEntityDescription(
        key="account_balance",
        value_fn=lambda data: data._account.account_balance,
        device_class=SensorDeviceClass.MONETARY,
        name_fn=lambda data: f"{data._account.first_name} Available Balance",
        native_unit_of_measurement_fn=lambda data: data._account.account_currency,
    )
}

EXPR_SENSORS: dict = {
    "pending_requests": FamilySafetySensorEntityDescription(
        key="pending_requests",
        value_fn=lambda data: len(
            [d for d in data.coordinator.api.pending_requests if d["puid"] == data._account_id]),
        name_fn=lambda data: f"{data._account.first_name} Pending Requests",
        native_unit_of_measurement_fn=lambda data: None
    )
}

TIME_SENSORS: dict[str, FamilySafetySensorEntityDescription] = {
    "screentime": FamilySafetySensorEntityDescription(
        key="screentime",
        value_fn=lambda data: (
            data._account.today_screentime_usage / 1000) / 60,
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement_fn=lambda data: "min",
        name_fn=lambda data: f"{data._account.first_name} Used Screen Time"
    )
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: FamilySafetyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Family Safety sensors."""
    accounts: list[Account] = config_entry.runtime_data.api.accounts
    entities = []
    for account in accounts:
        if (account.user_id in config_entry.options.get("accounts", [])) or (
            len(config_entry.options.get("accounts", [])) == 0
        ):
            for app in config_entry.options.get("tracked_applications", []):
                entities.append(ScreentimeSensor(
                    coordinator=config_entry.runtime_data,
                    description=FamilySafetySensorEntityDescription(
                        key=app,
                        device_class=SensorDeviceClass.DURATION,
                        native_unit_of_measurement_fn=lambda data: "min",
                        value_fn=lambda data: data._account.get_application(
                                app).usage,
                        name_fn=lambda data: f"{data._account.first_name} {data._account.get_application(app).name} Used Screen Time"),
                    idx=None,
                    account_id=account.user_id
                ))
            entities.extend(
                [ScreentimeSensor(
                    coordinator=config_entry.runtime_data,
                    idx=None,
                    account_id=account.user_id,
                    description=desc
                ) for desc in TIME_SENSORS.values()]
            )
            entities.extend(
                [GenericSensor(
                    coordinator=config_entry.runtime_data,
                    idx=None,
                    account_id=account.user_id,
                    description=desc
                ) for desc in GEN_SENSORS.values()]
            )
            if config_entry.options.get(CONF_KEY_EXPR, CONF_EXPR_DEFAULT):
                entities.extend(
                    [GenericSensor(
                        coordinator=config_entry.runtime_data,
                        idx=None,
                        account_id=account.user_id,
                        description=desc
                    ) for desc in EXPR_SENSORS.values()]
                )

    async_add_entities(entities, True)
    # register services
    platform = async_get_current_platform()
    platform.async_register_entity_service(
        name="block_app",
        schema={vol.Required("name"): str},
        func="async_block_application",
    )
    platform.async_register_entity_service(
        name="unblock_app",
        schema={vol.Required("name"): str},
        func="async_unblock_application",
    )
    if config_entry.options.get(CONF_KEY_EXPR, CONF_EXPR_DEFAULT):
        platform.async_register_entity_service(
            name="approve_request",
            schema={
                vol.Required("request_id"): str,
                vol.Required("extension_time"): int
            },
            func="async_approve_request"
        )
        platform.async_register_entity_service(
            name="deny_request",
            schema={
                vol.Required("request_id"): str
            },
            func="async_deny_request"
        )


class GenericSensor(ManagedAccountEntity, SensorEntity):
    """Use a Basic Sensor."""

    def __init__(self, coordinator: FamilySafetyCoordinator, description: FamilySafetySensorEntityDescription, idx, account_id) -> None:
        """Use a Basic Sensor."""
        super().__init__(coordinator, idx, account_id, description.key)
        self.entity_description = description

    @property
    def name(self) -> str:
        """Return name of entity."""
        return self.entity_description.name_fn(self)

    @property
    def native_value(self):
        """Return the native value of the entity."""
        return self.entity_description.value_fn(self)

    @property
    def native_unit_of_measurement(self):
        """Return UOM."""
        return self.entity_description.native_unit_of_measurement_fn(self)

    @property
    def device_class(self):
        """Return device class."""
        return self.entity_description.device_class

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return additional state attributes."""
        if self.entity_description.key == "pending_requests":
            return {
                "requests": [d for d in self.coordinator.api.pending_requests if d["puid"] == self._account_id]
            }


class ScreentimeSensor(GenericSensor, SensorEntity):
    """Aggregate screentime sensor."""

    def __init__(self, coordinator: FamilySafetyCoordinator, description: FamilySafetySensorEntityDescription, idx, account_id) -> None:
        """Screentime Sensor."""
        super().__init__(coordinator, description, idx, account_id)
        if description.key == "screentime":
            self.app_id = None
        else:
            self.app_id = description.key

    @property
    def _application(self) -> Application:
        """Get the application."""
        return self._account.get_application(self.app_id)

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return additional state attributes."""
        if self.entity_description.key == "screentime":
            devices = {}
            for device in self._account.devices:
                if device.today_time_used:
                    devices[device.device_name] = (
                        device.today_time_used / 1000) / 60
                else:
                    devices[device.device_name] = 0
            applications = {}
            for app in self._account.applications:
                applications[app.name] = app.usage
            return {"application_usage": applications, "device_usage": devices}
        elif self.app_id is not None:
            return {"blocked": self._application.blocked}
