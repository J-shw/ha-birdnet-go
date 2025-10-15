from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity, DataUpdateCoordinator
)
from datetime import timedelta
import logging

from .const import DOMAIN
from .api import BirdnetGoApiClient

SCAN_INTERVAL = timedelta(seconds=30) 

_LOGGER = logging.getLogger(__name__)

# --- Coordinator Setup ---
async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Stream Tool sensor platform."""
    api_client: BirdnetGoApiClient = hass.data[DOMAIN][config_entry.entry_id]

    async def async_update_data():
        """Fetch data from API."""
        return await api_client.async_get_streams_health()

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="Birdnet Go Health",
        update_method=async_update_data,
        update_interval=SCAN_INTERVAL,
    )

    await coordinator.async_config_entry_first_refresh()

    entities = []

    entities.append(StreamOverallHealthSensor(coordinator, config_entry))

    if (details := coordinator.data.get("stream_details")):
        for stream_detail in details:
            entities.append(StreamDetailSensor(coordinator, config_entry, stream_detail))

    async_add_entities(entities)

class StreamBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for Birdnet Go sensors."""

    def __init__(self, coordinator, config_entry: ConfigEntry):
        """Initialise the sensor."""
        super().__init__(coordinator)
        self._config_entry = config_entry

    @property
    def unique_id(self) -> str:
        """Return a unique ID for the entity."""
        return f"{self._config_entry.entry_id}_{self._id_suffix}"

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
            "name": self._config_entry.title,
            "manufacturer": "Custom",
            "model": "Stream Tool",
        }

class StreamOverallHealthSensor(StreamBaseSensor):
    """Represents the overall health status of the streaming tool."""

    def __init__(self, coordinator, config_entry):
        """Initialise the Overall Health sensor."""
        super().__init__(coordinator, config_entry)
        self._id_suffix = "overall_health"

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self._config_entry.title} Overall Health"

    @property
    def native_value(self):
        """Return the state of the sensor (e.g., 'healthy', 'unhealthy')."""
        return self.coordinator.data.get("status")

    @property
    def extra_state_attributes(self):
        """Return entity specific state attributes."""
        return {
            "last_check_utc": self.coordinator.data.get("last_check")
        }

class StreamDetailSensor(StreamBaseSensor):
    """Represents a specific metric for an individual stream."""

    def __init__(self, coordinator, config_entry, stream_data: dict):
        """Initialize the Stream Detail sensor."""
        super().__init__(coordinator, config_entry)
        self._stream_url = stream_data["url"]
        url_slug = self._stream_url.split('/')[-1]
        self._id_suffix = f"stream_{url_slug}_uptime"

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"Stream {self._stream_url.split('/')[-1]} Uptime"

    @property
    def native_value(self):
        """Return the state of the sensor (uptime in seconds)."""
        stream_details = self.coordinator.data.get("stream_details", [])
        
        current_stream = next(
            (s for s in stream_details if s.get("url") == self._stream_url),
            None
        )
        
        return current_stream.get("uptime_seconds") if current_stream else None

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return "s"
    
    @property
    def extra_state_attributes(self):
        """Add the stream's health status as an attribute."""
        stream_details = self.coordinator.data.get("stream_details", [])
        current_stream = next(
            (s for s in stream_details if s.get("url") == self._stream_url),
            {}
        )
        
        return {
            "health_status": current_stream.get("health_status"),
            "url": self._stream_url,
            "bitrate_mbps": current_stream.get("bitrate_mbps")
        }