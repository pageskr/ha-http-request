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
    CONF_SENSOR_NAME,
    CONF_TEXT_GROUP,
    CONF_TEXT_REGEX,
    CONF_TIMEOUT,
    CONF_URL,
    CONF_VALUE_TEMPLATE,
    CONF_VERIFY_SSL,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SENSOR_NAME,
    DEFAULT_TIMEOUT,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
)
from .parser import parse_html, parse_html_full, parse_json, parse_text, render_template

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the HTTP Request sensor."""
    # Check if coordinator already exists (created by binary_sensor)
    if "coordinator" in hass.data[DOMAIN][config_entry.entry_id]:
        coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    else:
        # Create new coordinator if not exists
        coordinator = HttpRequestDataUpdateCoordinator(hass, config_entry)
        await coordinator.async_config_entry_first_refresh()
        hass.data[DOMAIN][config_entry.entry_id]["coordinator"] = coordinator
    
    # Get sensors configuration
    sensors_config = config_entry.data.get("sensors", [])
    
    # Create sensor entities
    sensors = []
    for idx, sensor_config in enumerate(sensors_config):
        sensors.append(
            HttpRequestSensor(coordinator, config_entry, sensor_config, idx)
        )
    
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
                    
                    # Get response headers
                    response_headers = response.headers
                    content_type = response.content_type
                    content_length = response.headers.get("Content-Length")
                    
                    # Try to parse as JSON if needed
                    json_data = None
                    if self.response_type == "json":
                        try:
                            json_data = await response.json(content_type=None)
                        except Exception:
                            _LOGGER.debug("Failed to parse response as JSON")
                    
                    # Store response data
                    return {
                        "text": text,
                        "json": json_data,
                        "status": status,
                        "headers": response_headers,
                        "content_type": content_type,
                        "content_length": int(content_length) if content_length else None,
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
        sensor_config: dict[str, Any],
        idx: int,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._sensor_config = sensor_config
        self._idx = idx
        
        # Set unique ID for this sensor
        sensor_name = sensor_config.get("name", DEFAULT_SENSOR_NAME)
        self._attr_unique_id = f"{config_entry.entry_id}_{idx}_{sensor_name}"
        
        # Set name as "HTTP Request {Sensor}"
        self._attr_name = f"HTTP Request {sensor_name}"
        
        # Store parsed values
        self._parsed_value = None
        self._response_html = None

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        return self._parsed_value

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the state attributes."""
        if self.coordinator.data is None:
            return None
            
        response_data = self.coordinator.data
        
        attributes = {
            "sensor_index": self._idx,
            "sensor_name": self._sensor_config.get("name", DEFAULT_SENSOR_NAME),
        }
        
        # Add response HTML for HTML type
        if self.coordinator.response_type == "html" and self._response_html:
            attributes["response_html"] = self._response_html
        
        # Add parsing configuration
        if self.coordinator.response_type == "json":
            if json_path := self._sensor_config.get(CONF_JSON_PATH):
                attributes["json_path"] = json_path
        elif self.coordinator.response_type == "html":
            attributes["html_selector"] = self._sensor_config.get(CONF_HTML_SELECTOR, "")
            if html_attr := self._sensor_config.get(CONF_HTML_ATTR):
                attributes["html_attr"] = html_attr
        elif self.coordinator.response_type == "text":
            if regex := self._sensor_config.get(CONF_TEXT_REGEX):
                attributes["text_regex"] = regex
                attributes["text_group"] = self._sensor_config.get(CONF_TEXT_GROUP, 1)
        
        return attributes

    async def async_update(self) -> None:
        """Update the sensor."""
        await super().async_update()
        
        if self.coordinator.data is None:
            self._parsed_value = None
            self._response_html = None
            return
        
        response_data = self.coordinator.data
        
        # Parse based on response type
        if self.coordinator.response_type == "json":
            value = parse_json(
                response_data.get("json") or response_data.get("text"),
                self._sensor_config.get(CONF_JSON_PATH)
            )
        elif self.coordinator.response_type == "html":
            value = parse_html(
                response_data.get("text", ""),
                self._sensor_config.get(CONF_HTML_SELECTOR, ""),
                self._sensor_config.get(CONF_HTML_ATTR)
            )
            # Get the full HTML of selected element
            self._response_html = parse_html_full(
                response_data.get("text", ""),
                self._sensor_config.get(CONF_HTML_SELECTOR, "")
            )
        elif self.coordinator.response_type == "text":
            value = parse_text(
                response_data.get("text", ""),
                self._sensor_config.get(CONF_TEXT_REGEX),
                self._sensor_config.get(CONF_TEXT_GROUP, 1)
            )
        else:
            value = response_data.get("text")
        
        # Apply template if configured
        template_str = self._sensor_config.get(CONF_VALUE_TEMPLATE)
        if template_str:
            value = await render_template(
                self.hass,
                template_str,
                value,
                response_data
            )
        
        self._parsed_value = value
