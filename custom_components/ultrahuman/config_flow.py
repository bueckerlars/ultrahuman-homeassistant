"""Config flow for Ultrahuman integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, DAILY_METRICS_ENDPOINT

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("api_token"): str,
    }
)


async def validate_api_token(hass: HomeAssistant, api_token: str) -> dict[str, Any]:
    """Validate the API token by making a test request."""
    headers = {"Authorization": api_token}
    
    # Test with today's date
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                DAILY_METRICS_ENDPOINT,
                headers=headers,
                params={"date": today},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return {"title": "Ultrahuman", "data": data}
                elif response.status == 401:
                    raise InvalidAuth
                else:
                    raise CannotConnect
        except aiohttp.ClientError as err:
            _LOGGER.error("Error connecting to Ultrahuman API: %s", err)
            raise CannotConnect from err
        except Exception as err:
            _LOGGER.error("Unexpected error: %s", err)
            raise CannotConnect from err


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Ultrahuman."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        try:
            info = await validate_api_token(self.hass, user_input["api_token"])
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
