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

    if isinstance(coordinator.data, list) and coordinator.data:
        for stream_detail in coordinator.data:
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

class StreamDetailSensor(StreamBaseSensor):
    """Represents the health status of an individual stream."""

    def __init__(self, coordinator, config_entry, stream_data: dict):
        """Initialize the Stream Detail sensor."""
        super().__init__(coordinator, config_entry)
        
        self._stream_url = stream_data.get("url") 
        url_slug = self._stream_url.split('/')[-1] if self._stream_url else "unknown"
        self._id_suffix = f"stream_{url_slug}_health"

    @property
    def name(self):
        """Return the name of the sensor."""
        url_slug = self._stream_url.split('/')[-1] if self._stream_url else "Unknown Stream"
        return f"Stream {url_slug} Health"

    def _get_current_stream_data(self) -> dict:
        """Helper to find this sensor's data in the coordinator's list."""
        for stream in self.coordinator.data:
            if stream.get("url") == self._stream_url:
                return stream
        return {}

    @property
    def native_value(self):
        """Return the state of the sensor (e.g., 'running', 'circuit_open')."""
        current_stream = self._get_current_stream_data()
        return current_stream.get("process_state")

    @property
    def extra_state_attributes(self):
        """Add other stream details as attributes."""
        current_stream = self._get_current_stream_data()
        
        last_error = current_stream.get("last_error_context")
        
        return {
            "url": self._stream_url,
            "is_healthy": current_stream.get("is_healthy"),
            "is_receiving_data": current_stream.get("is_receiving_data"),
            "time_since_data_seconds": current_stream.get("time_since_data_seconds"),
            "bytes_per_second": current_stream.get("bytes_per_second"),
            "restart_count": current_stream.get("restart_count"),
            "last_data_received": current_stream.get("last_data_received"),
            "last_error_message": last_error.get("user_facing_msg") if last_error else None,
            "last_error_timestamp": last_error.get("timestamp") if last_error else None,
        }