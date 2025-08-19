"""Support for HTTP Request info binary sensor."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL
from .sensor import HttpRequestDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the HTTP Request info binary sensor."""
    # Reuse the coordinator from sensor platform
    coordinator = HttpRequestDataUpdateCoordinator(hass, config_entry)
    
    await coordinator.async_config_entry_first_refresh()
    
    # Store coordinator for sensor platform to reuse
    hass.data[DOMAIN][config_entry.entry_id]["coordinator"] = coordinator
    
    # Add the info entity
    async_add_entities([HttpRequestInfoEntity(coordinator, config_entry)], True)


class HttpRequestInfoEntity(CoordinatorEntity, BinarySensorEntity):
    """Representation of HTTP Request info entity."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(
        self,
        coordinator: HttpRequestDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the info entity."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        service_name = config_entry.data.get("service_name", "HTTP Request")
        self._attr_unique_id = f"{config_entry.entry_id}_info"
        self._attr_name = "Info"
        
        # Set device info for service
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=service_name,
            manufacturer=MANUFACTURER,
            model=MODEL,
            entry_type=dr.DeviceEntryType.SERVICE,  # 서비스 타입
        )

    @property
    def is_on(self) -> bool | None:
        """Return true if the HTTP request was successful (2xx status code)."""
        if self.coordinator.data is None:
            return None
        
        status = self.coordinator.data.get("status")
        if status is None:
            return None
            
        # HTTP status codes 200-299 are successful
        return 200 <= status < 300

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the state attributes."""
        if self.coordinator.data is None:
            return None
            
        response_data = self.coordinator.data
        
        attributes = {
            "http_status": response_data.get("status"),
            "response_type": self.coordinator.response_type,
            "url": self.coordinator.url,
            "method": self.coordinator.method,
            "timeout": self.coordinator.timeout,
            "verify_ssl": self.coordinator.verify_ssl,
            "scan_interval": self.coordinator.update_interval.total_seconds() if self.coordinator.update_interval else None,
        }
        
        # Add response headers if available
        if "headers" in response_data:
            attributes["response_headers"] = dict(response_data["headers"])
        
        # Add content type if available
        if "content_type" in response_data:
            attributes["content_type"] = response_data["content_type"]
        
        # Add response size if available
        if "content_length" in response_data:
            attributes["content_length"] = response_data["content_length"]
        
        return attributes

    @property
    def icon(self) -> str:
        """Return the icon based on HTTP status."""
        if self.coordinator.data is None:
            return "mdi:cloud-question"
            
        status = self.coordinator.data.get("status")
        if status is None:
            return "mdi:cloud-question"
        
        if 200 <= status < 300:
            return "mdi:cloud-check"
        elif 300 <= status < 400:
            return "mdi:cloud-sync"
        elif 400 <= status < 500:
            return "mdi:cloud-alert"
        elif 500 <= status < 600:
            return "mdi:cloud-off-outline"
        else:
            return "mdi:cloud-question"
