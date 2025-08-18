"""Support for HTTP Request sensors."""
from __future__ import annotations

import json
import logging
from datetime import timedelta
from typing import Any

import aiohttp
import async_timeout

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    CONF_BODY,
    CONF_HEADERS,
    CONF_HTML_ATTR,
    CONF_HTML_SELECTOR,
    CONF_JSON_PATH,
    CONF_METHOD,
    CONF_PARAMS,
    CONF_RESPONSE_TYPE,
    CONF_SCAN_INTERVAL,
    CONF_TEXT_GROUP,
    CONF_TEXT_REGEX,
    CONF_TIMEOUT,
    CONF_URL,
    CONF_VALUE_TEMPLATE,
    CONF_VERIFY_SSL,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
    MANUFACTURER,
    MODEL,
)
from .parser import parse_html, parse_json, parse_text, render_template

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the HTTP Request sensor."""
    coordinator = HttpRequestDataUpdateCoordinator(hass, config_entry)
    
    await coordinator.async_config_entry_first_refresh()
    
    async_add_entities([HttpRequestSensor(coordinator, config_entry)], True)


class HttpRequestDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching HTTP Request data."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize."""
        self.config_entry = config_entry
        self.hass = hass
        
        # Get config
        self.url = config_entry.data[CONF_URL]
        self.method = config_entry.data.get(CONF_METHOD, "GET")
        self.timeout = config_entry.data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)
        self.verify_ssl = config_entry.data.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL)
        self.response_type = config_entry.data.get(CONF_RESPONSE_TYPE, "text")
        
        # Parse JSON configs
        self.headers = self._parse_json_config(config_entry.data.get(CONF_HEADERS, ""))
        self.params = self._parse_json_config(config_entry.data.get(CONF_PARAMS, ""))
        self.body = self._parse_json_config(config_entry.data.get(CONF_BODY, ""))
        
        # Get update interval
        scan_interval = config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{config_entry.entry_id}",
            update_interval=timedelta(seconds=scan_interval),
        )

    def _parse_json_config(self, json_str: str) -> dict[str, Any]:
        """Parse JSON string from config."""
        if not json_str:
            return {}
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            _LOGGER.error("Failed to parse JSON: %s", json_str)
            return {}

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from HTTP endpoint."""
        session = async_get_clientsession(self.hass, verify_ssl=self.verify_ssl)
        
        try:
            # Prepare request
            kwargs = {
                "method": self.method,
                "url": self.url,
            }
            
            if self.headers:
                kwargs["headers"] = self.headers
            if self.params:
                kwargs["params"] = self.params
            if self.body and self.method in ["POST", "PUT", "PATCH"]:
                kwargs["json"] = self.body
            
            async with async_timeout.timeout(self.timeout):
                async with session.request(**kwargs) as response:
                    text = await response.text()
                    status = response.status
                    
                    # Try to parse as JSON if needed
                    json_data = None
                    if self.response_type == "json":
                        try:
                            json_data = await response.json(content_type=None)
                        except Exception:
                            _LOGGER.debug("Failed to parse response as JSON")
                    
                    # Store response data
                    response_data = {
                        "text": text,
                        "json": json_data,
                        "status": status,
                    }
                    
                    # Parse based on response type
                    if self.response_type == "json":
                        value = parse_json(
                            json_data or text,
                            self.config_entry.data.get(CONF_JSON_PATH)
                        )
                    elif self.response_type == "html":
                        value = parse_html(
                            text,
                            self.config_entry.data.get(CONF_HTML_SELECTOR, ""),
                            self.config_entry.data.get(CONF_HTML_ATTR)
                        )
                    elif self.response_type == "text":
                        value = parse_text(
                            text,
                            self.config_entry.data.get(CONF_TEXT_REGEX),
                            self.config_entry.data.get(CONF_TEXT_GROUP, 1)
                        )
                    else:
                        value = text
                    
                    # Apply template if configured
                    template_str = self.config_entry.data.get(CONF_VALUE_TEMPLATE)
                    if template_str:
                        value = await render_template(
                            self.hass,
                            template_str,
                            value,
                            response_data
                        )
                    
                    return {
                        "value": value,
                        "response_data": response_data,
                    }
                    
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        except Exception as err:
            _LOGGER.exception("Unexpected error fetching data")
            raise UpdateFailed(f"Unexpected error: {err}") from err


class HttpRequestSensor(CoordinatorEntity, SensorEntity):
    """Representation of a HTTP Request sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: HttpRequestDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._attr_unique_id = config_entry.entry_id
        self._attr_name = config_entry.data.get(CONF_NAME, "HTTP Request")
        
        # Set device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=MODEL,
            manufacturer=MANUFACTURER,
            model=MODEL,
            sw_version="1.0.0",
            configuration_url="https://github.com/pageskr/ha-http-request",
        )

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("value")

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the state attributes."""
        if self.coordinator.data is None:
            return None
            
        response_data = self.coordinator.data.get("response_data", {})
        
        attributes = {
            "http_status": response_data.get("status"),
            "response_type": self.coordinator.response_type,
            "url": self.coordinator.url,
            "method": self.coordinator.method,
        }
        
        # Add raw response for debugging
        if self.coordinator.response_type == "json" and response_data.get("json"):
            attributes["json_response"] = response_data["json"]
        
        return attributes