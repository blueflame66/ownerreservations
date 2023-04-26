"""Config flow for OwnerRez Integration integration."""
from __future__ import annotations

import logging
import aiohttp

from typing import Any

from .const import DEFAULT_UN, DEFAULT_PT, DEFAULT_URL, CONF_DAYS, CONF_MAX_EVENTS

import voluptuous as vol


from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
import homeassistant.helpers.config_validation as cv
from homeassistant.const import CONF_API_TOKEN, CONF_USERNAME, CONF_DELAY_TIME

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME, default=DEFAULT_UN): str,
        vol.Required(CONF_API_TOKEN, default=DEFAULT_PT): str,
        # vol.Required(CONF_DELAY_TIME, default=120): cv.positive_int,
        vol.Required(CONF_DAYS, default=365): cv.positive_int,
        vol.Required(CONF_MAX_EVENTS, default=10): cv.positive_int,
    }
)


class PlaceholderHub:
    """Placeholder class to make tests pass.

    TODO Remove this placeholder class and replace with things from your PyPI package.
    """

    def __init__(self, host: str) -> None:
        """Initialize."""
        self.host = host

    async def authenticate(self, username: str, password: str) -> str:
        """Test if we can authenticate with the host."""
        auth = aiohttp.BasicAuth(username, password)
        api_url = self.host + "/properties"
        async with aiohttp.ClientSession(auth=auth) as session:
            async with session.get(api_url) as resp:
                connectresult = resp.status
                return connectresult


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    # TODO validate the data can be used to set up a connection.

    # If your PyPI package is not built with async, pass your methods
    # to the executor:
    # await hass.async_add_executor_job(
    #     your_validate_func, data["username"], data["password"]
    # )

    hub = PlaceholderHub(DEFAULT_URL)

    if not await hub.authenticate(data[CONF_USERNAME], data[CONF_API_TOKEN]):
        raise InvalidAuth

    # If you cannot connect:
    # throw CannotConnect
    # If the authentication is wrong:
    # InvalidAuth

    # Return info that you want to store in the config entry.
    return {"title": "Owner Res Glenn"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for OwnerRez Integration."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
