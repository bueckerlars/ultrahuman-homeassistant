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
                raw_data = await response.json()
                
                # Extract and flatten metrics from the API response
                # Structure: {'data': {'metrics': {'2026-01-07': [...]}}, 'error': None, 'status': 200}
                if isinstance(raw_data, dict) and "data" in raw_data:
                    metrics_data = raw_data.get("data", {}).get("metrics", {})
                    
                    # Get today's date to find the right metrics
                    today = datetime.now().strftime("%Y-%m-%d")
                    today_metrics = metrics_data.get(today, [])
                    
                    # Flatten metrics into a dictionary
                    flattened = {}
                    for metric in today_metrics:
                        if isinstance(metric, dict) and "type" in metric and "object" in metric:
                            metric_type = metric["type"]
                            metric_obj = metric["object"]
                            
                            # Extract values based on metric type
                            if metric_type == "hr":
                                # Heart rate - extract avg from values
                                if "values" in metric_obj and isinstance(metric_obj["values"], list):
                                    values = [v.get("value") for v in metric_obj["values"] if "value" in v]
                                    if values:
                                        flattened["heart_rate_avg"] = sum(values) / len(values)
                                        flattened["heart_rate_min"] = min(values)
                                        flattened["heart_rate_max"] = max(values)
                            
                            elif metric_type == "night_rhr":
                                # Resting heart rate
                                if "avg" in metric_obj:
                                    flattened["heart_rate_resting"] = metric_obj["avg"]
                                elif "values" in metric_obj and isinstance(metric_obj["values"], list):
                                    # Get the latest value
                                    latest = metric_obj["values"][-1] if metric_obj["values"] else {}
                                    if "value" in latest:
                                        flattened["heart_rate_resting"] = latest["value"]
                            
                            elif metric_type == "avg_sleep_hrv":
                                # HRV
                                if "value" in metric_obj:
                                    flattened["hrv"] = metric_obj["value"]
                            
                            elif metric_type == "sleep":
                                # Sleep data
                                sleep_obj = metric_obj
                                if "quick_metrics" in sleep_obj:
                                    for qm in sleep_obj["quick_metrics"]:
                                        if isinstance(qm, dict) and "type" in qm:
                                            qm_type = qm["type"]
                                            if qm_type == "total_sleep" and "value" in qm:
                                                # Convert seconds to minutes
                                                flattened["sleep_duration"] = qm["value"] / 60
                                            elif qm_type == "sleep_index" and "value" in qm:
                                                flattened["sleep_quality"] = qm["value"]
                                            elif qm_type == "time_in_bed" and "value" in qm:
                                                flattened["time_in_bed"] = qm["value"] / 60
                            
                            elif metric_type == "steps":
                                # Steps
                                if "value" in metric_obj:
                                    flattened["steps"] = metric_obj["value"]
                            
                            elif metric_type == "active_minutes":
                                # Active minutes - Total minutes of moderate to vigorous physical activity
                                if "value" in metric_obj:
                                    flattened["activity_minutes"] = metric_obj["value"]
                                    # Also calculate hours
                                    flattened["activity_hours"] = metric_obj["value"] / 60
                            
                            elif metric_type == "motion":
                                # Motion/Movement intensity - may contain calories and other metrics
                                if "value" in metric_obj:
                                    flattened["movement_index"] = metric_obj["value"]
                                
                                # Extract additional metrics from quick_metrics
                                if "quick_metrics" in metric_obj:
                                    for qm in metric_obj["quick_metrics"]:
                                        if isinstance(qm, dict) and "type" in qm:
                                            qm_type = qm["type"]
                                            if qm_type == "calories" and "value" in qm:
                                                flattened["total_calories"] = qm["value"]
                                            elif qm_type == "total_calories" and "value" in qm:
                                                flattened["total_calories"] = qm["value"]
                            
                            elif metric_type == "activity_index":
                                # Activity index - may contain quick_metrics with additional data
                                if "value" in metric_obj:
                                    flattened["activity_index"] = metric_obj["value"]
                                
                                # Extract additional activity metrics from quick_metrics
                                if "quick_metrics" in metric_obj:
                                    for qm in metric_obj["quick_metrics"]:
                                        if isinstance(qm, dict) and "type" in qm:
                                            qm_type = qm["type"]
                                            if qm_type == "calories" and "value" in qm:
                                                flattened["total_calories"] = qm["value"]
                                            elif qm_type == "total_calories" and "value" in qm:
                                                flattened["total_calories"] = qm["value"]
                                            elif qm_type == "active_minutes" and "value" in qm:
                                                flattened["activity_minutes"] = qm["value"]
                                                # Calculate hours from minutes
                                                flattened["activity_hours"] = qm["value"] / 60
                            
                            elif metric_type == "recovery_index":
                                # Recovery index
                                if "value" in metric_obj:
                                    flattened["recovery_index"] = metric_obj["value"]
                            
                            elif metric_type == "metabolic_score":
                                # Metabolic score
                                if "value" in metric_obj:
                                    flattened["metabolic_score"] = metric_obj["value"]
                            
                            elif metric_type == "body_temperature":
                                # Body temperature
                                if "value" in metric_obj:
                                    flattened["body_temperature"] = metric_obj["value"]
                            
                            elif metric_type == "vo2_max":
                                # VO2 Max
                                if "value" in metric_obj:
                                    flattened["vo2_max"] = metric_obj["value"]
                    
                    _LOGGER.info(
                        "Extracted %d metrics from API response. Keys: %s",
                        len(flattened),
                        list(flattened.keys())
                    )
                    return flattened
                
                # Fallback: return raw data if structure is unexpected
                _LOGGER.warning("Unexpected API response structure: %s", list(raw_data.keys()) if isinstance(raw_data, dict) else type(raw_data))
                return raw_data if isinstance(raw_data, dict) else {}
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
