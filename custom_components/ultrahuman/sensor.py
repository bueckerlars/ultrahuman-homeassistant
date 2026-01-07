"""Sensor platform for Ultrahuman."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
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


def _extract_nested_value(data: dict[str, Any], *keys: str) -> StateType:
    """Extract value from nested dictionary structure."""
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
        else:
            return None
    return current if isinstance(current, (int, float, str)) else None


def _infer_device_class_and_unit(key: str) -> tuple[SensorDeviceClass | None, str | None, SensorStateClass | None]:
    """Infer device class, unit, and state class from sensor key name."""
    key_lower = key.lower()
    
    # Temperature sensors
    if "temperature" in key_lower or "temp" in key_lower:
        return SensorDeviceClass.TEMPERATURE, "°C", SensorStateClass.MEASUREMENT
    
    # Duration/Time sensors
    if "duration" in key_lower or "time" in key_lower or "sleep" in key_lower:
        if "sleep" in key_lower:
            return SensorDeviceClass.DURATION, "min", SensorStateClass.MEASUREMENT
        return SensorDeviceClass.DURATION, "s", SensorStateClass.MEASUREMENT
    
    # Heart rate sensors
    if "heart_rate" in key_lower or "hrv" in key_lower or "pulse" in key_lower:
        if "hrv" in key_lower:
            return None, "ms", SensorStateClass.MEASUREMENT
        return SensorDeviceClass.FREQUENCY, "bpm", SensorStateClass.MEASUREMENT
    
    # Steps
    if "step" in key_lower:
        return None, "steps", SensorStateClass.TOTAL_INCREASING
    
    # Energy/Power
    if "energy" in key_lower or "calorie" in key_lower:
        return SensorDeviceClass.ENERGY, "kcal", SensorStateClass.TOTAL_INCREASING
    
    # Distance
    if "distance" in key_lower:
        return SensorDeviceClass.DISTANCE, "m", SensorStateClass.TOTAL_INCREASING
    
    # Weight
    if "weight" in key_lower:
        return SensorDeviceClass.WEIGHT, "kg", SensorStateClass.MEASUREMENT
    
    # Default for numeric values
    return None, None, SensorStateClass.MEASUREMENT


# Define common sensor descriptions for known Ring metrics
SENSOR_DESCRIPTIONS: tuple[UltrahumanSensorEntityDescription, ...] = (
    # Heart Rate metrics
    UltrahumanSensorEntityDescription(
        key="heart_rate_resting",
        name="Heart Rate Resting",
        native_unit_of_measurement="bpm",
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:heart-pulse",
        value_fn=lambda d: _extract_nested_value(d, "heart_rate", "resting")
            or _extract_nested_value(d, "resting_heart_rate")
            or _extract_nested_value(d, "heart_rate_resting"),
    ),
    UltrahumanSensorEntityDescription(
        key="heart_rate_avg",
        name="Heart Rate Average",
        native_unit_of_measurement="bpm",
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:heart-pulse",
        value_fn=lambda d: _extract_nested_value(d, "heart_rate", "average")
            or _extract_nested_value(d, "avg_heart_rate")
            or _extract_nested_value(d, "heart_rate_avg"),
    ),
    # HRV (Heart Rate Variability)
    UltrahumanSensorEntityDescription(
        key="hrv",
        name="Heart Rate Variability",
        native_unit_of_measurement="ms",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:heart-flash",
        value_fn=lambda d: _extract_nested_value(d, "hrv")
            or _extract_nested_value(d, "heart_rate_variability"),
    ),
    # Sleep metrics
    UltrahumanSensorEntityDescription(
        key="sleep_duration",
        name="Sleep Duration",
        native_unit_of_measurement="min",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:sleep",
        value_fn=lambda d: _extract_nested_value(d, "sleep", "duration")
            or _extract_nested_value(d, "sleep_duration"),
    ),
    UltrahumanSensorEntityDescription(
        key="sleep_quality",
        name="Sleep Quality",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:sleep",
        value_fn=lambda d: _extract_nested_value(d, "sleep", "quality")
            or _extract_nested_value(d, "sleep_quality"),
    ),
    # Activity metrics
    UltrahumanSensorEntityDescription(
        key="steps",
        name="Steps",
        native_unit_of_measurement="steps",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:walk",
        value_fn=lambda d: _extract_nested_value(d, "steps")
            or _extract_nested_value(d, "activity", "steps"),
    ),
    UltrahumanSensorEntityDescription(
        key="activity_index",
        name="Activity Index",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:run",
        value_fn=lambda d: _extract_nested_value(d, "activity_index")
            or _extract_nested_value(d, "activity", "index"),
    ),
    # Recovery metrics
    UltrahumanSensorEntityDescription(
        key="recovery_index",
        name="Recovery Index",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:heart-plus",
        value_fn=lambda d: _extract_nested_value(d, "recovery_index")
            or _extract_nested_value(d, "recovery", "index"),
    ),
    UltrahumanSensorEntityDescription(
        key="metabolic_score",
        name="Metabolic Score",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:chart-line",
        value_fn=lambda d: _extract_nested_value(d, "metabolic_score")
            or _extract_nested_value(d, "metabolic", "score"),
    ),
    # Body Temperature
    UltrahumanSensorEntityDescription(
        key="body_temperature",
        name="Body Temperature",
        native_unit_of_measurement="°C",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer",
        value_fn=lambda d: _extract_nested_value(d, "body_temperature")
            or _extract_nested_value(d, "temperature", "body"),
    ),
    # VO2 Max
    UltrahumanSensorEntityDescription(
        key="vo2_max",
        name="VO2 Max",
        native_unit_of_measurement="ml/kg/min",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:run-fast",
        value_fn=lambda d: _extract_nested_value(d, "vo2_max")
            or _extract_nested_value(d, "fitness", "vo2_max"),
    ),
)


def _create_sensors_from_data(
    data: dict[str, Any],
    coordinator: UltrahumanDataUpdateCoordinator,
    prefix: str = "",
    entities: list[UltrahumanSensor] | None = None,
) -> list[UltrahumanSensor]:
    """Recursively create sensors from nested data structure."""
    if entities is None:
        entities = []
    
    for key, value in data.items():
        full_key = f"{prefix}_{key}" if prefix else key
        
        if isinstance(value, (int, float)):
            # Create sensor for numeric values
            device_class, unit, state_class = _infer_device_class_and_unit(full_key)
            # Capture variables for closure
            sensor_key = full_key
            sensor_prefix = prefix
            sensor_orig_key = key
            entities.append(
                UltrahumanSensor(
                    coordinator=coordinator,
                    description=UltrahumanSensorEntityDescription(
                        key=sensor_key,
                        name=sensor_key.replace("_", " ").title(),
                        device_class=device_class,
                        native_unit_of_measurement=unit,
                        state_class=state_class or SensorStateClass.MEASUREMENT,
                        value_fn=lambda d, k=sensor_key, p=sensor_prefix, orig_k=sensor_orig_key: (
                            d.get(k) if not p
                            else d.get(p, {}).get(orig_k) if isinstance(d.get(p), dict)
                            else None
                        ),
                    ),
                )
            )
        elif isinstance(value, str) and value.replace(".", "", 1).replace("-", "", 1).isdigit():
            # Try to convert string numbers to float
            sensor_key = full_key
            try:
                float_value = float(value)
                device_class, unit, state_class = _infer_device_class_and_unit(sensor_key)
                entities.append(
                    UltrahumanSensor(
                        coordinator=coordinator,
                        description=UltrahumanSensorEntityDescription(
                            key=sensor_key,
                            name=sensor_key.replace("_", " ").title(),
                            device_class=device_class,
                            native_unit_of_measurement=unit,
                            state_class=state_class or SensorStateClass.MEASUREMENT,
                            value_fn=lambda d, k=sensor_key: (
                                float(d.get(k)) if isinstance(d.get(k), str) and d.get(k).replace(".", "", 1).replace("-", "", 1).isdigit()
                                else d.get(k)
                            ),
                        ),
                    )
                )
            except (ValueError, AttributeError):
                # Not a number, create as string sensor
                entities.append(
                    UltrahumanSensor(
                        coordinator=coordinator,
                        description=UltrahumanSensorEntityDescription(
                            key=sensor_key,
                            name=sensor_key.replace("_", " ").title(),
                            value_fn=lambda d, k=sensor_key: d.get(k),
                        ),
                    )
                )
        elif isinstance(value, str):
            # Create sensor for string values
            sensor_key = full_key
            entities.append(
                UltrahumanSensor(
                    coordinator=coordinator,
                    description=UltrahumanSensorEntityDescription(
                        key=sensor_key,
                        name=sensor_key.replace("_", " ").title(),
                        value_fn=lambda d, k=sensor_key: d.get(k),
                    ),
                )
            )
        elif isinstance(value, dict):
            # Recursively process nested dictionaries
            _create_sensors_from_data(value, coordinator, full_key, entities)
        elif isinstance(value, list):
            # Handle arrays - create sensors for numeric arrays or aggregate
            if value and isinstance(value[0], (int, float)):
                # Create aggregated sensors for numeric arrays
                sensor_key = full_key
                sensor_prefix = prefix
                sensor_orig_key = key
                entities.append(
                    UltrahumanSensor(
                        coordinator=coordinator,
                        description=UltrahumanSensorEntityDescription(
                            key=f"{sensor_key}_count",
                            name=f"{sensor_key.replace('_', ' ').title()} Count",
                            state_class=SensorStateClass.MEASUREMENT,
                            value_fn=lambda d, k=sensor_orig_key, p=sensor_prefix: (
                                len(d.get(k, [])) if not p
                                else len(d.get(p, {}).get(k, [])) if isinstance(d.get(p), dict)
                                else 0
                            ),
                        ),
                    )
                )
                entities.append(
                    UltrahumanSensor(
                        coordinator=coordinator,
                        description=UltrahumanSensorEntityDescription(
                            key=f"{sensor_key}_sum",
                            name=f"{sensor_key.replace('_', ' ').title()} Sum",
                            state_class=SensorStateClass.MEASUREMENT,
                            value_fn=lambda d, k=sensor_orig_key, p=sensor_prefix: (
                                sum(d.get(k, [])) if not p and isinstance(d.get(k), list)
                                else sum(d.get(p, {}).get(k, [])) if isinstance(d.get(p), dict) and isinstance(d.get(p).get(k), list)
                                else None
                            ),
                        ),
                    )
                )
    
    return entities


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
    if not isinstance(data, dict):
        _LOGGER.warning("Received invalid data format from coordinator: %s", type(data))
        return
    
    # First, add predefined sensors if they match the data
    for description in SENSOR_DESCRIPTIONS:
        if description.value_fn:
            value = description.value_fn(data)
            if value is not None:
                # Check if sensor already exists (avoid duplicates)
                existing_keys = {e.entity_description.key for e in entities}
                if description.key not in existing_keys:
                    entities.append(
                        UltrahumanSensor(coordinator=coordinator, description=description)
                    )
    
    # Then create dynamic sensors for remaining data
    existing_keys = {e.entity_description.key for e in entities}
    dynamic_entities = _create_sensors_from_data(data, coordinator)
    
    # Add dynamic sensors that don't conflict with predefined ones
    for entity in dynamic_entities:
        if entity.entity_description.key not in existing_keys:
            entities.append(entity)
            existing_keys.add(entity.entity_description.key)

    _LOGGER.info("Created %d Ultrahuman sensors", len(entities))
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
