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
                    _LOGGER.error("Invalid API token - authentication failed")
                    raise UpdateFailed("Invalid API token")
                elif response.status == 403:
                    _LOGGER.error("API token lacks required permissions")
                    raise UpdateFailed("API token lacks required permissions")
                elif response.status == 404:
                    _LOGGER.warning("No data available for date: %s", today)
                    # Return empty dict instead of failing for missing data
                    return {}
                elif response.status >= 500:
                    _LOGGER.error("Ultrahuman API server error: %s", response.status)
                    raise UpdateFailed(f"Ultrahuman API server error: {response.status}")
                
                response.raise_for_status()
                data = await response.json()
                
                # Log data structure for debugging (without sensitive data)
                if isinstance(data, dict):
                    _LOGGER.debug(
                        "Received data from Ultrahuman API with keys: %s",
                        list(data.keys())
                    )
                else:
                    _LOGGER.debug("Received data from Ultrahuman API: %s", type(data))
                
                return data if isinstance(data, dict) else {}
        except aiohttp.ClientTimeout:
            _LOGGER.error("Timeout while connecting to Ultrahuman API")
            raise UpdateFailed("Timeout while connecting to Ultrahuman API")
        except aiohttp.ClientError as err:
            _LOGGER.error("Error communicating with Ultrahuman API: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        except Exception as err:
            _LOGGER.exception("Unexpected error while fetching Ultrahuman data: %s", err)
            raise UpdateFailed(f"Unexpected error: {err}") from err

    async def async_shutdown(self) -> None:
        """Close the session."""
        if self._session:
            await self._session.close()
            self._session = None
