"""Sensor platform for HTTP Request integration."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

import aiohttp
from aiohttp import ClientSession, ClientTimeout

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_DEVICE_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    CONF_ATTR_TEMPLATE,
    CONF_ATTRIBUTES,
    CONF_BODY,
    CONF_HEADERS,
    CONF_HTML_ATTR,
    CONF_HTML_SELECTOR,
    CONF_JSON_JMES,
    CONF_KEY,
    CONF_METHOD,
    CONF_NAME,
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
from .parser import extract_value, render_template

_LOGGER = logging.getLogger(__name__)


@dataclass
class HttpRequestData:
    """Data from HTTP request."""

    state: Any
    attributes: dict[str, Any]
    raw_text: str
    raw_json: Any


class HttpRequestCoordinator(DataUpdateCoordinator[HttpRequestData]):
    """Coordinator to manage HTTP requests."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
    ) -> None:
        """Initialize coordinator."""
        self.entry = entry
        self.hass = hass
        
        # Parse config
        self.method = entry.data.get(CONF_METHOD, "GET").upper()
        self.url = entry.data.get(CONF_URL)
        self.timeout = entry.data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)
        self.verify_ssl = entry.data.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL)
        self.response_type = entry.data.get(CONF_RESPONSE_TYPE, "json")
        
        # Parse headers, params, body
        self.headers = self._parse_json_str(entry.data.get(CONF_HEADERS, ""))
        self.params = self._parse_json_str(entry.data.get(CONF_PARAMS, ""))
        self.body = self._parse_json_str(entry.data.get(CONF_BODY, ""))
        
        # Parse attributes config
        self.attributes_config = self._parse_json_str(entry.data.get(CONF_ATTRIBUTES, ""))
        if not isinstance(self.attributes_config, list):
            self.attributes_config = []
        
        # Update interval
        scan_interval = max(10, entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

    def _parse_json_str(self, json_str: str) -> Any:
        """Parse JSON string safely."""
        if not json_str or not json_str.strip():
            return {}
        try:
            return json.loads(json_str)
        except Exception:
            _LOGGER.error("Failed to parse JSON: %s", json_str)
            return {}

    async def _async_update_data(self) -> HttpRequestData:
        """Fetch data from HTTP endpoint."""
        session = async_get_clientsession(self.hass, verify_ssl=self.verify_ssl)
        timeout = ClientTimeout(total=self.timeout)
        
        try:
            # Prepare request kwargs
            kwargs = {
                "method": self.method,
                "url": self.url,
                "timeout": timeout,
            }
            
            if self.headers:
                kwargs["headers"] = self.headers
            if self.params:
                kwargs["params"] = self.params
            if self.body and self.method in ["POST", "PUT", "PATCH"]:
                kwargs["json"] = self.body
            
            async with session.request(**kwargs) as response:
                text = await response.text()
                
                # Try to parse as JSON
                body_obj = None
                if self.response_type == "json":
                    try:
                        body_obj = await response.json(content_type=None)
                    except Exception:
                        _LOGGER.debug("Failed to parse response as JSON")
                
                # Extract state value
                state_val = extract_value(
                    self.response_type,
                    body_obj,
                    text,
                    self.entry.data.get(CONF_JSON_JMES),
                    self.entry.data.get(CONF_HTML_SELECTOR),
                    self.entry.data.get(CONF_HTML_ATTR),
                    self.entry.data.get(CONF_TEXT_REGEX),
                    self.entry.data.get(CONF_TEXT_GROUP),
                )
                
                # Apply value template if provided
                value_template = self.entry.data.get(CONF_VALUE_TEMPLATE)
                if value_template:
                    template_vars = {
                        "value": state_val,
                        "json": body_obj,
                        "text": text,
                        "status": response.status,
                    }
                    state_val = await render_template(self.hass, value_template, template_vars)
                
                # Extract attributes
                attrs = {"http_status": response.status}
                
                for attr_config in self.attributes_config:
                    if not isinstance(attr_config, dict):
                        continue
                        
                    key = attr_config.get(CONF_KEY)
                    if not key:
                        continue
                    
                    # Extract attribute value
                    attr_val = extract_value(
                        attr_config.get(CONF_RESPONSE_TYPE, self.response_type),
                        body_obj,
                        text,
                        attr_config.get(CONF_JSON_JMES),
                        attr_config.get(CONF_HTML_SELECTOR),
                        attr_config.get(CONF_HTML_ATTR),
                        attr_config.get(CONF_TEXT_REGEX),
                        attr_config.get(CONF_TEXT_GROUP),
                    )
                    
                    # Apply attribute template if provided
                    attr_template = attr_config.get(CONF_ATTR_TEMPLATE)
                    if attr_template:
                        template_vars = {
                            "value": attr_val,
                            "json": body_obj,
                            "text": text,
                            "status": response.status,
                        }
                        attr_val = await render_template(self.hass, attr_template, template_vars)
                    
                    attrs[key] = attr_val
                
                return HttpRequestData(
                    state=state_val,
                    attributes=attrs,
                    raw_text=text,
                    raw_json=body_obj,
                )
                
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"HTTP request failed: {err}") from err
        except Exception as err:
            _LOGGER.exception("Unexpected error")
            raise UpdateFailed(f"Unexpected error: {err}") from err


class HttpRequestSensor(CoordinatorEntity[HttpRequestCoordinator], SensorEntity):
    """Representation of a HTTP Request sensor."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:http"

    def __init__(
        self,
        coordinator: HttpRequestCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = entry.entry_id
        self._attr_name = entry.data.get(CONF_NAME, "HTTP Request")
        
        # Set device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=MODEL,
            manufacturer=MANUFACTURER,
            model=MODEL,
            configuration_url="https://github.com/pageskr/ha-http-request",
        )

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.state

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        if self.coordinator.data is None:
            return {}
        return self.coordinator.data.attributes


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up HTTP Request sensor based on a config entry."""
    coordinator = HttpRequestCoordinator(hass, entry)
    
    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()
    
    async_add_entities([HttpRequestSensor(coordinator, entry)])