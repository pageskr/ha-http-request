"""Support for HTTP Request sensors."""
import logging
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

_LOGGER = logging.getLogger(__name__)

DOMAIN = "http_request"
SCAN_INTERVAL = timedelta(seconds=300)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the HTTP Request sensor."""
    name = config_entry.data.get("name")
    url = config_entry.data.get("url")
    
    async_add_entities([HttpRequestSensor(name, url)], True)


class HttpRequestSensor(SensorEntity):
    """Representation of a HTTP Request sensor."""

    def __init__(self, name, url):
        """Initialize the sensor."""
        self._name = name
        self._url = url
        self._state = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._state

    async def async_update(self):
        """Fetch new state data for the sensor."""
        self._state = f"URL: {self._url}"