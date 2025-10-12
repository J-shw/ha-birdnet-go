import logging
import aiohttp

_LOGGER = logging.getLogger(__name__)

class BirdnetGoApiClient:

    def __init__(self, host: str, username: str, password: str):
        """Initialise the API client."""
        self._base_url = f"http://{host}/api/v2"
        self._auth = aiohttp.BasicAuth(username, password)
        self._session = None

    async def async_get_streams_health(self) -> dict:
        """Detailed health status of all streams."""
        return await self._async_api_request("/streams/health")

    async def async_get_stream_health(self, url: str) -> dict:
        """Stream-specific health status."""
        encoded_url = url.replace('/', '%2F') 
        endpoint = f"/streams/health/{encoded_url}"
        return await self._async_api_request(endpoint)

    async def async_get_streams_status(self) -> dict:
        """High-level summary with healthy/unhealthy counts."""
        return await self._async_api_request("/streams/status")

    async def _async_api_request(self, endpoint: str) -> dict:
        """Make an async GET request to the specified API endpoint."""
        url = self._base_url + endpoint
        _LOGGER.debug("Making API request to: %s", url)

        if self._session is None:
            self._session = aiohttp.ClientSession()

        try:
            async with self._session.get(url, auth=self._auth, timeout=10) as response:
                if response.status // 100 != 2:
                    error_text = await response.text()
                    _LOGGER.error("API error for %s: Status %d, Response: %s", url, response.status, error_text)
                    response.raise_for_status()

                return await response.json()

        except aiohttp.ClientError as err:
            _LOGGER.error("Connection error for %s: %s", url, err)
            raise ConnectionError(f"Failed to connect to the Birdnet Go API: {err}") from err
        except Exception as err:
            _LOGGER.error("Unexpected error during API request to %s: %s", url, err)
            raise