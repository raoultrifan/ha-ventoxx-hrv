"""The Ventoxx HRV integration."""
from __future__ import annotations
from datetime import timedelta
import logging
import async_timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, CONF_HOST
from .api import VentoxxApiClient

_LOGGER = logging.getLogger(__name__)
PLATFORMS: list[Platform] = [Platform.FAN]

class VentoxxDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Ventoxx data."""

    def __init__(self, hass, api):
        """Initialize."""
        self.api = api
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=10),
        )

    async def _async_update_data(self):
        """Fetch data from API."""
        async with async_timeout.timeout(10):
            return await self.api.get_state()

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Ventoxx from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    session = async_get_clientsession(hass)
    client = VentoxxApiClient(entry.data[CONF_HOST], session)
    
    coordinator = VentoxxDataUpdateCoordinator(hass, client)
    await coordinator.async_config_entry_first_refresh()
    
    hass.data[DOMAIN][entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
