"""Sensor platform for Ultrahuman."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import UltrahumanDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass
class UltrahumanSensorEntityDescription(SensorEntityDescription):
    """Describes Ultrahuman sensor entity."""

    value_fn: Callable[[dict[str, Any]], StateType] | None = None
    unit_fn: Callable[[dict[str, Any]], str | None] | None = None


# Define common sensor descriptions
SENSOR_DESCRIPTIONS: tuple[UltrahumanSensorEntityDescription, ...] = (
    # Add specific sensor descriptions here if you know the exact structure
    # Example:
    # UltrahumanSensorEntityDescription(
    #     key="heart_rate",
    #     name="Heart Rate",
    #     native_unit_of_measurement="bpm",
    #     device_class=SensorDeviceClass.FREQUENCY,
    #     state_class=SensorStateClass.MEASUREMENT,
    #     value_fn=lambda data: data.get("heart_rate"),
    # ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Ultrahuman sensor entities."""
    coordinator: UltrahumanDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Create sensors based on available data
    entities: list[UltrahumanSensor] = []
    
    # Wait for initial data to be available
    await coordinator.async_config_entry_first_refresh()
    
    data = coordinator.data
    if isinstance(data, dict):
        # Create dynamic sensors based on the data structure
        for key, value in data.items():
            if isinstance(value, (int, float, str)):
                entities.append(
                    UltrahumanSensor(
                        coordinator=coordinator,
                        description=UltrahumanSensorEntityDescription(
                            key=key,
                            name=key.replace("_", " ").title(),
                            value_fn=lambda d, k=key: d.get(k),
                        ),
                    )
                )
            elif isinstance(value, dict):
                # Handle nested dictionaries
                for nested_key, nested_value in value.items():
                    if isinstance(nested_value, (int, float, str)):
                        full_key = f"{key}_{nested_key}"
                        entities.append(
                            UltrahumanSensor(
                                coordinator=coordinator,
                                description=UltrahumanSensorEntityDescription(
                                    key=full_key,
                                    name=f"{key.replace('_', ' ').title()} {nested_key.replace('_', ' ').title()}",
                                    value_fn=lambda d, k1=key, k2=nested_key: d.get(k1, {}).get(k2) if isinstance(d.get(k1), dict) else None,
                                ),
                            )
                        )

    # Also add predefined sensors if they match the data
    for description in SENSOR_DESCRIPTIONS:
        if description.value_fn and description.value_fn(data) is not None:
            entities.append(
                UltrahumanSensor(coordinator=coordinator, description=description)
            )

    async_add_entities(entities)


class UltrahumanSensor(
    CoordinatorEntity[UltrahumanDataUpdateCoordinator], SensorEntity
):
    """Representation of an Ultrahuman sensor."""

    entity_description: UltrahumanSensorEntityDescription

    def __init__(
        self,
        coordinator: UltrahumanDataUpdateCoordinator,
        description: UltrahumanSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{description.key}"
        self._attr_name = f"Ultrahuman {description.name}"

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if self.entity_description.value_fn:
            return self.entity_description.value_fn(self.coordinator.data)
        return None

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement."""
        if self.entity_description.unit_fn:
            return self.entity_description.unit_fn(self.coordinator.data)
        return self.entity_description.native_unit_of_measurement
