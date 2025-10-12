import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN, HOST, USERNAME, PASSWORD
from .api import BirdnetGoApiClient


_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.info("Setting up Birdnet Go integration")

    host = entry.data["Host"]
    # username = entry.data["Username"]
    # password = entry.data["Password"]
    hass.data.setdefault(DOMAIN, {})[HOST] = host
    # hass.data.setdefault(DOMAIN, {})[USERNAME] = username
    # hass.data.setdefault(DOMAIN, {})[PASSWORD] = password

    api_client = BirdnetGoApiClient(host)

    try:
        await api_client.async_get_streams_status()
    except ConnectionError as err:
        _LOGGER.error("Could not connect to API: %s", err)
        return False

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = api_client

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

    return True