"""Sensor platform for HTTP Request integration."""
from __future__ import annotations

import json
import logging
from datetime import timedelta
from typing import Any

import aiohttp

from homeassistant.components.sensor import (
    SensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_NAME,
)
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
    CONF_ATTRIBUTES,
    CONF_BODY,
    CONF_HEADERS,
    CONF_HTML_ATTR,
    CONF_HTML_SELECTOR,
    CONF_JSON_JMES,
    CONF_KEY,
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
from .parser import extract_value, render_template_value

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up HTTP Request sensor from a config entry."""
    coordinator = HttpRequestDataUpdateCoordinator(hass, config_entry)
    
    await coordinator.async_config_entry_first_refresh()
    
    async_add_entities([HttpRequestSensor(coordinator, config_entry)])


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
        self.headers = self._parse_json(config_entry.data.get(CONF_HEADERS, ""), {})
        self.params = self._parse_json(config_entry.data.get(CONF_PARAMS, ""), {})
        self.body = self._parse_json(config_entry.data.get(CONF_BODY, ""), {})
        self.attributes_config = self._parse_json(config_entry.data.get(CONF_ATTRIBUTES, ""), [])
        
        # Get update interval
        scan_interval = max(10, config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

    def _parse_json(self, json_str: str, default: Any) -> Any:
        """Parse JSON string safely."""
        if not json_str or not json_str.strip():
            return default
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            _LOGGER.warning("Failed to parse JSON: %s", json_str)
            return default

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from HTTP endpoint."""
        session = async_get_clientsession(self.hass, verify_ssl=self.verify_ssl)
        
        try:
            # Prepare request
            kwargs = {
                "timeout": aiohttp.ClientTimeout(total=self.timeout),
            }
            
            if self.headers:
                kwargs["headers"] = self.headers
            if self.params:
                kwargs["params"] = self.params
            if self.body and self.method in ["POST", "PUT", "PATCH"]:
                if isinstance(self.body, dict):
                    kwargs["json"] = self.body
                else:
                    kwargs["data"] = self.body
            
            # Make request
            async with session.request(self.method, self.url, **kwargs) as response:
                text = await response.text()
                status = response.status
                
                # Parse response
                json_data = None
                if self.response_type == "json":
                    try:
                        json_data = await response.json(content_type=None)
                    except Exception:
                        _LOGGER.debug("Failed to parse JSON response")
                
                # Extract state value
                state_config = {
                    CONF_JSON_JMES: self.config_entry.data.get(CONF_JSON_JMES),
                    CONF_HTML_SELECTOR: self.config_entry.data.get(CONF_HTML_SELECTOR),
                    CONF_HTML_ATTR: self.config_entry.data.get(CONF_HTML_ATTR),
                    CONF_TEXT_REGEX: self.config_entry.data.get(CONF_TEXT_REGEX),
                    CONF_TEXT_GROUP: self.config_entry.data.get(CONF_TEXT_GROUP, 1),
                }
                
                state_value = extract_value(
                    self.response_type,
                    json_data,
                    text,
                    state_config,
                )
                
                # Apply value template
                value_template = self.config_entry.data.get(CONF_VALUE_TEMPLATE)
                if value_template:
                    template_vars = {
                        "value": state_value,
                        "json": json_data,
                        "text": text,
                        "status": status,
                    }
                    state_value = await render_template_value(
                        self.hass,
                        value_template,
                        template_vars,
                    )
                
                # Extract attributes
                attributes = {"http_status": status}
                
                if isinstance(self.attributes_config, list):
                    for attr_config in self.attributes_config:
                        if not isinstance(attr_config, dict):
                            continue
                        
                        key = attr_config.get(CONF_KEY)
                        if not key:
                            continue
                        
                        # Get response type for this attribute
                        attr_response_type = attr_config.get(CONF_RESPONSE_TYPE, self.response_type)
                        
                        # Extract attribute value
                        attr_value = extract_value(
                            attr_response_type,
                            json_data,
                            text,
                            attr_config,
                        )
                        
                        # Apply attribute template
                        attr_template = attr_config.get("attr_template")
                        if attr_template:
                            template_vars = {
                                "value": attr_value,
                                "json": json_data,
                                "text": text,
                                "status": status,
                            }
                            attr_value = await render_template_value(
                                self.hass,
                                attr_template,
                                template_vars,
                            )
                        
                        attributes[key] = attr_value
                
                return {
                    "state": state_value,
                    "attributes": attributes,
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
            configuration_url="https://github.com/pageskr/ha-http-request",
        )

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("state")

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the state attributes."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("attributes", {})