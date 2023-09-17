"""Config flow for MSFT Family Safety."""

import logging
from typing import Any

from pyfamilysafety.authenticator import Authenticator
from pyfamilysafety.exceptions import HttpException
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required("response_url"): str,
        vol.Required("update_interval", default=60): int
    }
)

async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the input."""
    auth: Authenticator = None
    try:
        _LOGGER.debug("Config flow received -> test credentials")
        auth = await Authenticator.create(
            token=data["response_url"],
            use_refresh_token=False
        )
    except HttpException as err:
        _LOGGER.error(err)
        raise InvalidAuth from err
    except Exception as err:
        _LOGGER.error(err)
        raise CannotConnect from err

    _LOGGER.debug("Authentication success, expiry time %s, returning refresh_token.", auth.expires)
    return {
        "title": "Microsoft Family Safety",
        "refresh_token": auth.refresh_token
    }

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
            config_entry: config_entries.ConfigEntry
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlow(config_entry)

    async def async_step_user(
            self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the intial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                user_input["refresh_token"] = info["refresh_token"]
                return self.async_create_entry(title=info["title"], data=user_input)
            except InvalidAuth as err:
                _LOGGER.warning("Invalid authentication received: %s", err)
                errors["base"] = "invalid_auth"
            except CannotConnect as err:
                _LOGGER.warning("Cannot connect: %s", err)
                errors["base"] = "cannot_connect"
            except Exception as err:
                _LOGGER.error(err)
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=CONFIG_SCHEMA,
            errors=errors
        )

class OptionsFlow(config_entries.OptionsFlow):
    """An options flow for HASS."""
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Initial step."""
        if user_input is not None:
            return self.async_create_entry(
                title=self.config_entry.title,
                data={
                    "refresh_token": user_input["refresh_token"],
                    "update_interval": user_input["update_interval"]
                }
            )

        update_interval = self.config_entry.data["update_interval"]
        if self.config_entry.options:
            update_interval = self.config_entry.options.get("update_interval")

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required("update_interval", default=update_interval): int,
                    vol.Required("refresh_token",
                                 default=self.config_entry.data["refresh_token"]): str
                }
            )
        )

class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
