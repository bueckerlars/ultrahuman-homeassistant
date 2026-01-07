"""Data update coordinator for Ultrahuman."""
from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, DAILY_METRICS_ENDPOINT, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class UltrahumanDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching Ultrahuman data."""

    def __init__(self, hass: HomeAssistant, api_token: str) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=UPDATE_INTERVAL),
        )
        self.api_token = api_token
        self._session: aiohttp.ClientSession | None = None

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Ultrahuman API."""
        if self._session is None:
            self._session = aiohttp.ClientSession()

        headers = {"Authorization": self.api_token}
        
        # Get today's date
        today = datetime.now().strftime("%Y-%m-%d")
        
        try:
            async with self._session.get(
                DAILY_METRICS_ENDPOINT,
                headers=headers,
                params={"date": today},
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                if response.status == 401:
                    raise UpdateFailed("Invalid API token")
                response.raise_for_status()
                data = await response.json()
                _LOGGER.debug("Received data from Ultrahuman API: %s", data)
                return data
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}") from err

    async def async_shutdown(self) -> None:
        """Close the session."""
        if self._session:
            await self._session.close()
            self._session = None
