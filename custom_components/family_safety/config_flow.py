"""Config flow for MSFT Family Safety."""

import logging
from typing import Any

from pyfamilysafety import FamilySafetyAPI
from pyfamilysafety.exceptions import HttpException
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        vol.Optional("refresh_token"): str,
        vol.Optional("response_url"): str,
        vol.Required("update_interval", default=60): int
    }
)

async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the input."""
    familysafety: FamilySafetyAPI = None
    try:
        _LOGGER.debug("Config flow received -> test credentials")
        if len(data["refresh_token"])>0:
            familysafety = await FamilySafetyAPI.create(
                token=data["refresh_token"],
                use_refresh_token=True
            )
        else:
            familysafety = await FamilySafetyAPI.create(
                token=data["response_url"],
                use_refresh_token=False
            )
    except HttpException as err:
        _LOGGER.error(err)
        raise InvalidAuth from err
    except Exception as err:
        _LOGGER.error(err)
        raise CannotConnect from err

    _LOGGER.debug("Authentication success, returning refresh_token.")
    return {
        "title": "Microsoft Family Safety",
        "refresh_token": familysafety.authenticator.refresh_token
    }

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1

    async def async_step_user(
            self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the intial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except InvalidAuth as err:
                errors["base"] = "invalid_auth"
            except CannotConnect as err:
                errors["base"] = "cannot_connect"
            except Exception as err:
                _LOGGER.error(err)
                errors["base"] = "unknown"
            else:
                user_input["response_url"] = ""
                user_input["refresh_token"] = info["refresh_token"]
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=CONFIG_SCHEMA,
            errors=errors
        )

class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
