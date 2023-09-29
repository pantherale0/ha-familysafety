"""Config flow for MSFT Family Safety."""

import contextlib
import logging
from typing import Any

from pyfamilysafety import FamilySafety
from pyfamilysafety.authenticator import Authenticator
from pyfamilysafety.exceptions import HttpException
from pyfamilysafety.application import Application
from pyfamilysafety.account import Account
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import selector

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required("response_url"): str,
        vol.Required("update_interval", default=60): int
    }
)

def _get_application_id(name: str, applications: list[Application]):
    """Return the single application ID."""
    return [a for a in applications if a.name == name][0].app_id

def _convert_applications(applications: list[Application]):
    """Converts a list of applications to an array for options."""
    return [a.name for a in applications]

def _convert_accounts(accounts: list[Account]):
    """Convert a list of accounts to an array for options."""
    return [f"{a.first_name} {a.surname}" for a in accounts]

def _get_account_id(name: str, accounts: list[Account]):
    """Return the account ID."""
    return [a for a in accounts if (f"{a.first_name} {a.surname}" == name)][0].user_id

async def validate_input(data: dict[str, Any]) -> dict[str, Any]:
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
        return OptionsFlow(config_entry=config_entry)

    async def async_step_user(
            self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the intial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(user_input)
                user_input["refresh_token"] = info["refresh_token"]
                return self.async_create_entry(title=info["title"], data=user_input)
            except InvalidAuth as err:
                _LOGGER.warning("Invalid authentication received: %s", err)
                errors["base"] = "invalid_auth"
            except CannotConnect as err:
                _LOGGER.warning("Cannot connect: %s", err)
                errors["base"] = "cannot_connect"

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
        self.family_safety: FamilySafety = None

    def _get_config_entry(self, key):
        """Returns the specific config entry"""
        config = self.config_entry.data.get(key, None)
        if (self.config_entry.options) and (
            self.config_entry.options.get(key, None) is not None
        ):
            config = self.config_entry.options.get(key)
        return config

    async def _async_create_entry(self, **kwargs) -> config_entries.FlowResult:
        """Create an entry using optional overrides."""
        update_interval = self._get_config_entry("update_interval")
        if kwargs.get("update_interval", None) is not None:
            update_interval = kwargs.get("update_interval")
        if update_interval is None:
            update_interval = 60

        refresh_token = self._get_config_entry("refresh_token")
        if kwargs.get("refresh_token", None) is not None:
            refresh_token = kwargs.get("refresh_token")

        tracked_applications = self._get_config_entry("tracked_applications")
        if kwargs.get("tracked_applications", None) is not None:
            tracked_applications = kwargs.get("tracked_applications")
        if tracked_applications is None:
            tracked_applications = []

        accounts = self._get_config_entry("accounts")
        if kwargs.get("accounts", None) is not None:
            accounts = kwargs.get("accounts")
        if accounts is None:
            accounts = []

        await self.family_safety.api.end_session()
        return self.async_create_entry(
            title=self.config_entry.title,
            data={
                "refresh_token": refresh_token,
                "update_interval": update_interval,
                "tracked_applications": tracked_applications,
                "accounts": accounts
            }
        )

    async def async_step_auth(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Auth step."""
        if user_input is not None:
            return await self._async_create_entry(
                refresh_token=user_input["refresh_token"],
                update_interval=user_input["update_interval"]
            )

        refresh_token = self.config_entry.data["refresh_token"]
        if self.config_entry.options:
            refresh_token = self.config_entry.options.get("refresh_token", refresh_token)

        update_interval = self.config_entry.data["update_interval"]
        if self.config_entry.options:
            update_interval = self.config_entry.options.get("update_interval", update_interval)

        return self.async_show_form(
            step_id="auth",
            data_schema=vol.Schema(
                {
                    vol.Required("update_interval", default=update_interval): int,
                    vol.Required("refresh_token",
                                 default=refresh_token): str
                }
            )
        )

    async def async_step_applications(
            self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Application configuration step."""
        if user_input is not None:
            tracked_applications = []
            applications = self.family_safety.accounts[0].applications
            for app in user_input.get("tracked_applications", []):
                tracked_applications.append(_get_application_id(app, applications))
            return await self._async_create_entry(
                tracked_applications=tracked_applications
            )

        default_tracked_applications = []
        tracked_applications = self._get_config_entry("tracked_applications")
        if tracked_applications is None:
            tracked_applications = []
        for app in tracked_applications:
            with contextlib.suppress(IndexError):
                default_tracked_applications.append(
                    self.family_safety.accounts[0].get_application(app).name
                )

        return self.async_show_form(
            step_id="applications",
            data_schema=vol.Schema({
                vol.Optional("tracked_applications",
                             default=default_tracked_applications): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=_convert_applications(self.family_safety.accounts[0].applications),
                        custom_value=False,
                        multiple=True)
                )
            })
        )

    async def async_step_accounts(
            self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Accounts step."""

        if user_input is not None:
            tracked_user_ids = []
            try:
                for user in user_input.get("accounts", []):
                    tracked_user_ids.append(
                        _get_account_id(user, self.family_safety.accounts)
                    )
            except IndexError:
                pass
            return await self._async_create_entry(
                accounts=tracked_user_ids
            )

        default_tracked_accounts = []
        tracked_accounts = self._get_config_entry("accounts")
        if tracked_accounts is None:
            tracked_accounts = []
        for account in tracked_accounts:
            try:
                acc = self.family_safety.get_account(account)
                default_tracked_accounts.append(f"{acc.first_name} {acc.surname}")
            except IndexError:
                pass

        return self.async_show_form(
            step_id="accounts",
            data_schema=vol.Schema(
                {
                    vol.Optional("accounts",
                                 default=default_tracked_accounts): selector.SelectSelector(
                                     selector.SelectSelectorConfig(
                                         options=_convert_accounts(self.family_safety.accounts),
                                         custom_value=False,
                                         multiple=True
                                     )
                                 )
                }
            )
        )

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """First step."""
        self.family_safety = await FamilySafety.create(
            token=self.config_entry.data["refresh_token"],
            use_refresh_token=True
        )
        return self.async_show_menu(
            step_id="init",
            menu_options=["auth", "applications", "accounts"]
        )

class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
