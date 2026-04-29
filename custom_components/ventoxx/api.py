import logging
import aiohttp
import async_timeout

_LOGGER = logging.getLogger(__name__)

class VentoxxApiError(Exception):
    """Exception to indicate a general API error."""

class VentoxxApiClient:
    """Async client for the Ventoxx local HTTP API."""

    def __init__(self, host: str, session: aiohttp.ClientSession) -> None:
        """Initialize the API client."""
        self._host = host
        self._session = session
        self._base_url = f"http://{host}"

    async def get_state(self) -> dict:
        """Fetch the current state from the Ventoxx unit."""
        url = f"{self._base_url}/getstate"
        
        # Force the exact headers your old YAML used
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        try:
            async with async_timeout.timeout(10):
                # Add data="" and the headers to the POST request
                async with self._session.post(url, data="", headers=headers) as response:
                    if response.status != 200:
                        raise VentoxxApiError(f"Failed to fetch state: HTTP {response.status}")
                    return await response.json()
        except Exception as err:
            raise VentoxxApiError(f"Error communicating with Ventoxx at {self._host}: {err}") from err

    async def set_full_state(self, fstate: int, buzzst: int, dispst: int) -> None:
        """Push the fstate along with buzzer and display parameters."""
        url = f"{self._base_url}/set" 
        
        # NOTE: If your password ever changes, update it here!
        payload = {
            "pass": "ventoxxpass", 
            "fstate": str(fstate),
            "buzzst": str(buzzst),
            "dispst": str(dispst)
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        
        try:
            async with async_timeout.timeout(10):
                async with self._session.post(url, data=payload, headers=headers) as response:
                    if response.status not in (200, 204):
                        raise VentoxxApiError(f"Failed to set full state: HTTP {response.status}")
        except Exception as err:
            raise VentoxxApiError(f"Error sending state to Ventoxx at {self._host}: {err}") from err