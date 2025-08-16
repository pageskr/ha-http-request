"""Sensor platform for HTTP Request integration."""
from __future__ import annotations

import json
import logging
from datetime import timedelta
from typing import Any

import aiohttp

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

_LOGGER = logging.getLogger(__name__)

DOMAIN = "http_request"
MANUFACTURER = "Pages in Korea (pages.kr)"
MODEL = "HTTP Request"


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up HTTP Request sensor based on a config entry."""
    coordinator = HttpRequestDataUpdateCoordinator(hass, config_entry)
    await coordinator.async_config_entry_first_refresh()
    
    sensors = [HttpRequestSensor(coordinator, config_entry)]
    async_add_entities(sensors, True)


class HttpRequestDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching HTTP Request data."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize."""
        self.config_entry = config_entry
        self.method = config_entry.data.get("method", "GET")
        self.url = config_entry.data["url"]
        self.timeout = config_entry.data.get("timeout", 30)
        
        # Parse headers
        headers_str = config_entry.data.get("headers", "")
        self.headers = {}
        if headers_str:
            try:
                self.headers = json.loads(headers_str)
            except json.JSONDecodeError:
                _LOGGER.error("Invalid JSON in headers: %s", headers_str)
        
        update_interval = config_entry.data.get("scan_interval", 60)
        
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{config_entry.entry_id}",
            update_interval=timedelta(seconds=update_interval),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from HTTP endpoint."""
        session = async_get_clientsession(self.hass)
        
        try:
            async with session.request(
                method=self.method,
                url=self.url,
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                text = await response.text()
                
                # Try to parse as JSON
                try:
                    data = await response.json(content_type=None)
                    return {
                        "status": response.status,
                        "data": data,
                        "text": text,
                        "is_json": True,
                    }
                except Exception:
                    return {
                        "status": response.status,
                        "data": None,
                        "text": text,
                        "is_json": False,
                    }
                    
        except aiohttp.ClientError as error:
            raise UpdateFailed(f"Error fetching data: {error}")
        except Exception as error:
            _LOGGER.exception("Unexpected error")
            raise UpdateFailed(f"Unexpected error: {error}")


class HttpRequestSensor(CoordinatorEntity, SensorEntity):
    """Representation of a HTTP Request sensor."""

    def __init__(
        self,
        coordinator: HttpRequestDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._name = config_entry.data["name"]
        self._attr_unique_id = f"{DOMAIN}_{config_entry.entry_id}"
        
        # Set device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=MODEL,
            manufacturer=MANUFACTURER,
            model=MODEL,
            configuration_url="https://github.com/pageskr/ha-http-request",
        )

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._name

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
            
        # For now, return the full text response as the state
        return self.coordinator.data.get("text", "")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        if self.coordinator.data is None:
            return {}
            
        attrs = {
            "http_status": self.coordinator.data.get("status"),
            "is_json": self.coordinator.data.get("is_json", False),
        }
        
        # If JSON data, include it in attributes
        if self.coordinator.data.get("is_json") and self.coordinator.data.get("data"):
            attrs["json_data"] = self.coordinator.data["data"]
            
        return attrs