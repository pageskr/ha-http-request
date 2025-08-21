"""Support for HTTP Request sensors."""
from __future__ import annotations

import json
import logging
from datetime import timedelta
from typing import Any

import aiohttp
import async_timeout

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, CONF_UNIT_OF_MEASUREMENT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.util import dt as dt_util

from .const import (
    CONF_BODY,
    CONF_HEADERS,
    CONF_HTML_ATTR,
    CONF_HTML_SELECTOR,
    CONF_HTML_VALUE_TYPE,
    CONF_HTML_ATTR_NAME,
    CONF_JSON_PATH,
    CONF_METHOD,
    CONF_PARAMS,
    CONF_RESPONSE_TYPE,
    CONF_SCAN_INTERVAL,
    CONF_SENSOR_NAME,
    CONF_TEXT_GROUP,
    CONF_TEXT_GROUP_COUNT,
    CONF_TEXT_REGEX,
    CONF_TIMEOUT,
    CONF_URL,
    CONF_VALUE_TEMPLATE,
    CONF_VERIFY_SSL,
    CONF_ATTRIBUTES_TEMPLATE,
    CONF_KEEP_LAST_VALUE,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SENSOR_NAME,
    DEFAULT_TEXT_GROUP_COUNT,
    DEFAULT_TIMEOUT,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
    MANUFACTURER,
    MODEL,
)
from .parser import parse_html, parse_html_full, parse_json, parse_text, parse_text_all, render_template, render_attributes_template

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
        self.response_type = config_entry.data.get(CONF_RESPONSE_TYPE, "json")
        
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
        
        # Store last update time
        self.last_update_success_time = None

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
            
            # Handle params differently for POST/PUT/PATCH
            if self.method in ["POST", "PUT", "PATCH"]:
                if self.params:
                    kwargs["data"] = self.params  # Use data for form params
                if self.body:
                    kwargs["json"] = self.body
            else:
                if self.params:
                    kwargs["params"] = self.params  # Use params for query string
                    
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
                    
                    # Update last success time
                    self.last_update_success_time = dt_util.now()
                    
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
        service_name = config_entry.data.get("service_name", "HTTP Request")
        self._attr_unique_id = f"{config_entry.entry_id}_{idx}_{sensor_name}"
        
        # Set name
        self._attr_name = sensor_name
        
        # Set device info for service
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=service_name,
            manufacturer=MANUFACTURER,
            model=MODEL,
            entry_type=dr.DeviceEntryType.SERVICE,  # 서비스 타입
        )
        
        # Set unit of measurement if configured
        unit = sensor_config.get(CONF_UNIT_OF_MEASUREMENT)
        if unit:
            self._attr_unit_of_measurement = unit
        
        # Store parsed values
        self._parsed_value = None
        self._last_valid_value = None  # For keeping last value
        self._last_valid_state_value = None  # For keeping sensor's last state value
        self._response_html = None
        self._text_matches = None
        self._text_total_count = 0  # Total count of text matches
        self._custom_attributes = {}
        self._last_update = None  # Last sensor update time
        self._state_restored = False  # Flag to check if state has been restored

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
            "sensor_update": dt_util.now(),  # Always update to current time
        }
        
        # Add response HTML for HTML type
        if self.coordinator.response_type == "html" and self._response_html:
            attributes["response_html"] = self._response_html
        
        # Add text matches for text type with regex
        if self.coordinator.response_type == "text":
            if self._text_matches:
                attributes["text_matches"] = self._text_matches
            if self._sensor_config.get(CONF_TEXT_REGEX):
                attributes["text_total_count"] = self._text_total_count
        
        # Add parsing configuration
        if self.coordinator.response_type == "json":
            if json_path := self._sensor_config.get(CONF_JSON_PATH):
                attributes["json_path"] = json_path
        elif self.coordinator.response_type == "html":
            attributes["html_selector"] = self._sensor_config.get(CONF_HTML_SELECTOR, "")
            if value_type := self._sensor_config.get(CONF_HTML_VALUE_TYPE):
                attributes["html_value_type"] = value_type
            if attr_name := self._sensor_config.get(CONF_HTML_ATTR_NAME):
                attributes["html_attr_name"] = attr_name
        elif self.coordinator.response_type == "text":
            if regex := self._sensor_config.get(CONF_TEXT_REGEX):
                attributes["text_regex"] = regex
                attributes["text_group_count"] = self._sensor_config.get(CONF_TEXT_GROUP_COUNT, DEFAULT_TEXT_GROUP_COUNT)
        
        # Add unit of measurement to attributes if configured
        if hasattr(self, '_attr_unit_of_measurement'):
            attributes["unit_of_measurement"] = self._attr_unit_of_measurement
        
        # Add custom attributes
        attributes.update(self._custom_attributes)
        
        return attributes

    async def async_update(self) -> None:
        """Update the sensor."""
        await super().async_update()
        
        # Try to restore the sensor's last state value on first update
        if not self._state_restored and self.entity_id:
            state = self.hass.states.get(self.entity_id)
            if state and state.state not in ["unknown", "unavailable", None]:
                self._last_valid_state_value = state.state
            self._state_restored = True
        
        if self.coordinator.data is None:
            if not self._sensor_config.get(CONF_KEEP_LAST_VALUE, False):
                self._parsed_value = None
                self._response_html = None
                self._text_matches = None
                self._text_total_count = 0
                self._custom_attributes = {}
            return
        
        response_data = self.coordinator.data
        
        # Store original parsed values for templates
        json_full = None  # Full JSON response
        json_value = None  # JSON path result
        html_full = None  # Full HTML response
        html_value = None  # Selected HTML element value
        text_full = None  # Full text response
        text_value = None  # Text matches or raw text
        
        # Parse based on response type
        if self.coordinator.response_type == "json":
            # Store full JSON response
            json_full = response_data.get("json") or response_data.get("text")
            # Parse JSON path if specified
            json_value = parse_json(
                json_full,
                self._sensor_config.get(CONF_JSON_PATH)
            )
            value = json_value
        elif self.coordinator.response_type == "html":
            html_value_type = self._sensor_config.get(CONF_HTML_VALUE_TYPE, "value")
            attr_name = self._sensor_config.get(CONF_HTML_ATTR_NAME)
            
            # Store full HTML response
            html_full = response_data.get("text", "")
            
            # Get the outer HTML of selected element for response_html attribute
            selected_html = parse_html_full(
                html_full,
                self._sensor_config.get(CONF_HTML_SELECTOR, "")
            )
            self._response_html = selected_html  # Outer HTML of selected element
            
            # Parse value based on value type for sensor state
            html_value = parse_html(
                html_full,
                self._sensor_config.get(CONF_HTML_SELECTOR, ""),
                html_value_type,
                attr_name
            )
            value = html_value
        elif self.coordinator.response_type == "text":
            # Store full text response
            text_full = response_data.get("text", "")
            
            if regex := self._sensor_config.get(CONF_TEXT_REGEX):
                # Get ALL matches for template variable
                all_matches = parse_text_all(
                    text_full,
                    regex,
                    None  # No limit for template variable
                )
                # Store total count
                self._text_total_count = len(all_matches) if all_matches else 0
                
                # Get matches up to configured count for attribute
                group_count = self._sensor_config.get(CONF_TEXT_GROUP_COUNT, DEFAULT_TEXT_GROUP_COUNT)
                if all_matches and len(all_matches) > group_count:
                    self._text_matches = all_matches[:group_count]
                else:
                    self._text_matches = all_matches
                
                # Get first match for sensor value
                text_value = all_matches[0] if all_matches else None
                value = text_value
            else:
                text_value = text_full
                value = text_value
                self._text_matches = None
                self._text_total_count = 0
        else:
            value = response_data.get("text")
        
        # Apply value template if configured
        template_str = self._sensor_config.get(CONF_VALUE_TEMPLATE)
        if template_str:
            template_vars = {
                "value": value,  # Current parsed value (for backward compatibility)
                "json": json_full,  # Full JSON response
                "html": html_full,  # Full HTML response
                "text": text_full,  # Full text response
                "response": response_data.get("text", ""),  # Raw response
                "status": response_data.get("status"),
            }
            try:
                template_result = await render_template(
                    self.hass,
                    template_str,
                    template_vars
                )
                # Check if keep_last_value is enabled and template result is invalid
                if self._sensor_config.get(CONF_KEEP_LAST_VALUE, False):
                    template_str_lower = str(template_result).lower() if template_result is not None else "none"
                    if template_result is None or template_str_lower in ["false", "none", "unknown", "unavailable"]:
                        # Template result is invalid and keep_last_value is enabled
                        if self._last_valid_state_value is not None:
                            value = self._last_valid_state_value  # Keep sensor's last state value
                        else:
                            value = template_result  # No previous state to keep
                    else:
                        value = template_result
                else:
                    # Keep_last_value is not enabled, use template result as-is
                    value = template_result
            except Exception as e:
                _LOGGER.debug("Template error: %s", e)
                # If keep_last_value is enabled and template fails, keep sensor's last state value
                if self._sensor_config.get(CONF_KEEP_LAST_VALUE, False):
                    if self._last_valid_state_value is not None:
                        value = self._last_valid_state_value  # Keep sensor's last state value
                    else:
                        value = None  # No previous state to keep
                else:
                    # Keep_last_value is not enabled, set to None
                    value = None
        
        # Update parsed value
        self._parsed_value = value
        
        # Store the current valid state value for next update
        if value is not None:
            value_str_lower = str(value).lower()
            if value_str_lower not in ["false", "none", "unknown", "unavailable"]:
                self._last_valid_state_value = value
        
        # Always update the last update time
        self._last_update = dt_util.now()
        
        # Auto-detect state class for numeric values with units
        if hasattr(self, '_attr_unit_of_measurement') and self._attr_unit_of_measurement:
            try:
                # Check if the value is numeric
                float(self._parsed_value)
                # Set state_class to measurement for statistics
                self._attr_state_class = SensorStateClass.MEASUREMENT
            except (ValueError, TypeError):
                # Not numeric, remove state_class if set
                if hasattr(self, '_attr_state_class'):
                    delattr(self, '_attr_state_class')
        else:
            # No unit, ensure no state_class for statistics
            if hasattr(self, '_attr_state_class'):
                delattr(self, '_attr_state_class')
        
        # Apply attributes template if configured
        attributes_template_str = self._sensor_config.get(CONF_ATTRIBUTES_TEMPLATE)
        if attributes_template_str:
            template_vars = {
                "value": value,  # Current parsed value (for backward compatibility)
                "json": json_full,  # Full JSON response
                "html": html_full,  # Full HTML response
                "text": text_full,  # Full text response
                "response": response_data.get("text", ""),  # Raw response
                "status": response_data.get("status"),
            }
            self._custom_attributes = await render_attributes_template(
                self.hass,
                attributes_template_str,
                template_vars
            )
        else:
            self._custom_attributes = {}
