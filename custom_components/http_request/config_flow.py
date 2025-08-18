"""Config flow for HTTP Request integration."""
from __future__ import annotations

import json
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv

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
    CONF_SENSOR_NAME,
    DEFAULT_HTML_ATTR,
    DEFAULT_METHOD,
    DEFAULT_NAME,
    DEFAULT_RESPONSE_TYPE,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SENSOR_NAME,
    DEFAULT_TEXT_GROUP,
    DEFAULT_TIMEOUT,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
    HTTP_METHODS,
    RESPONSE_TYPES,
)

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HTTP Request."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate JSON fields
            if user_input.get(CONF_HEADERS):
                try:
                    json.loads(user_input[CONF_HEADERS])
                except json.JSONDecodeError:
                    errors["base"] = "invalid_headers_json"
            
            if user_input.get(CONF_PARAMS):
                try:
                    json.loads(user_input[CONF_PARAMS])
                except json.JSONDecodeError:
                    errors["base"] = "invalid_params_json"
            
            if user_input.get(CONF_BODY):
                try:
                    json.loads(user_input[CONF_BODY])
                except json.JSONDecodeError:
                    errors["base"] = "invalid_body_json"
            
            if not errors:
                # Create unique ID for the integration instance
                await self.async_set_unique_id(f"{DOMAIN}_{user_input[CONF_URL]}")
                self._abort_if_unique_id_configured()
                
                # Create entry without any sensors initially
                return self.async_create_entry(
                    title=DEFAULT_NAME,
                    data={
                        **user_input,
                        "sensors": []  # Start with no sensors
                    },
                )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_URL): str,
                vol.Required(CONF_METHOD, default=DEFAULT_METHOD): vol.In(HTTP_METHODS),
                vol.Required(CONF_RESPONSE_TYPE, default=DEFAULT_RESPONSE_TYPE): vol.In(RESPONSE_TYPES),
                vol.Optional(CONF_HEADERS, default=""): str,
                vol.Optional(CONF_PARAMS, default=""): str,
                vol.Optional(CONF_BODY, default=""): str,
                vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=300)
                ),
                vol.Optional(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): bool,
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
                    vol.Coerce(int), vol.Range(min=30, max=86400)
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for HTTP Request."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["settings", "add_sensor", "manage_sensors"],
        )

    async def async_step_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the settings option."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate JSON fields
            if user_input.get(CONF_HEADERS):
                try:
                    json.loads(user_input[CONF_HEADERS])
                except json.JSONDecodeError:
                    errors["base"] = "invalid_headers_json"
            
            if user_input.get(CONF_PARAMS):
                try:
                    json.loads(user_input[CONF_PARAMS])
                except json.JSONDecodeError:
                    errors["base"] = "invalid_params_json"
            
            if user_input.get(CONF_BODY):
                try:
                    json.loads(user_input[CONF_BODY])
                except json.JSONDecodeError:
                    errors["base"] = "invalid_body_json"
            
            if not errors:
                # Update config entry
                new_data = dict(self.config_entry.data)
                new_data.update(user_input)
                self.hass.config_entries.async_update_entry(
                    self.config_entry, data=new_data
                )
                
                # Force refresh after settings change
                await self.hass.config_entries.async_reload(self.config_entry.entry_id)
                
                return self.async_create_entry(title="", data={})

        data = self.config_entry.data
        data_schema = vol.Schema(
            {
                vol.Required(CONF_URL, default=data.get(CONF_URL, "")): str,
                vol.Required(CONF_METHOD, default=data.get(CONF_METHOD, DEFAULT_METHOD)): vol.In(HTTP_METHODS),
                vol.Required(CONF_RESPONSE_TYPE, default=data.get(CONF_RESPONSE_TYPE, DEFAULT_RESPONSE_TYPE)): vol.In(RESPONSE_TYPES),
                vol.Optional(CONF_HEADERS, default=data.get(CONF_HEADERS, "")): str,
                vol.Optional(CONF_PARAMS, default=data.get(CONF_PARAMS, "")): str,
                vol.Optional(CONF_BODY, default=data.get(CONF_BODY, "")): str,
                vol.Optional(CONF_TIMEOUT, default=data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=300)
                ),
                vol.Optional(CONF_VERIFY_SSL, default=data.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL)): bool,
                vol.Optional(CONF_SCAN_INTERVAL, default=data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)): vol.All(
                    vol.Coerce(int), vol.Range(min=30, max=86400)
                ),
            }
        )

        return self.async_show_form(
            step_id="settings",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_add_sensor(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle adding a new sensor."""
        if user_input is not None:
            # Store sensor name temporarily
            self.temp_sensor_name = user_input.get(CONF_SENSOR_NAME, DEFAULT_SENSOR_NAME)
            return await self.async_step_sensor_parsing()

        data_schema = vol.Schema(
            {
                vol.Required(CONF_SENSOR_NAME, default=DEFAULT_SENSOR_NAME): str,
            }
        )

        return self.async_show_form(
            step_id="add_sensor",
            data_schema=data_schema,
        )

    async def async_step_sensor_parsing(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle parsing configuration for the new sensor."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Add new sensor to the sensors list
            new_data = dict(self.config_entry.data)
            sensors = new_data.get("sensors", [])
            
            # Create new sensor config
            new_sensor = {
                "name": self.temp_sensor_name,
                **user_input
            }
            sensors.append(new_sensor)
            new_data["sensors"] = sensors
            
            # Update config entry
            self.hass.config_entries.async_update_entry(
                self.config_entry, data=new_data
            )
            
            # Reload the integration to add the new sensor
            await self.hass.config_entries.async_reload(self.config_entry.entry_id)
            
            return self.async_create_entry(title="", data={})

        # Build schema based on response type
        response_type = self.config_entry.data.get(CONF_RESPONSE_TYPE, DEFAULT_RESPONSE_TYPE)
        
        if response_type == "json":
            data_schema = vol.Schema(
                {
                    vol.Optional(CONF_JSON_PATH, default=""): str,
                    vol.Optional(CONF_VALUE_TEMPLATE, default=""): str,
                }
            )
        elif response_type == "html":
            data_schema = vol.Schema(
                {
                    vol.Required(CONF_HTML_SELECTOR): str,
                    vol.Optional(CONF_HTML_ATTR, default=DEFAULT_HTML_ATTR): str,
                    vol.Optional(CONF_VALUE_TEMPLATE, default=""): str,
                }
            )
        elif response_type == "text":
            data_schema = vol.Schema(
                {
                    vol.Optional(CONF_TEXT_REGEX, default=""): str,
                    vol.Optional(CONF_TEXT_GROUP, default=DEFAULT_TEXT_GROUP): vol.All(
                        vol.Coerce(int), vol.Range(min=0, max=99)
                    ),
                    vol.Optional(CONF_VALUE_TEMPLATE, default=""): str,
                }
            )
        else:
            data_schema = vol.Schema(
                {
                    vol.Optional(CONF_VALUE_TEMPLATE, default=""): str,
                }
            )

        return self.async_show_form(
            step_id="sensor_parsing",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={"response_type": response_type},
        )

    async def async_step_manage_sensors(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle managing existing sensors."""
        sensors = self.config_entry.data.get("sensors", [])
        
        if user_input is not None:
            # Handle sensor management actions
            if "remove_sensors" in user_input:
                # Remove selected sensors
                indices_to_remove = user_input["remove_sensors"]
                new_sensors = [s for i, s in enumerate(sensors) if i not in indices_to_remove]
                
                new_data = dict(self.config_entry.data)
                new_data["sensors"] = new_sensors
                
                self.hass.config_entries.async_update_entry(
                    self.config_entry, data=new_data
                )
                
                await self.hass.config_entries.async_reload(self.config_entry.entry_id)
                
                return self.async_create_entry(title="", data={})
        
        if not sensors:
            # No sensors to manage
            return self.async_abort(reason="no_sensors")
        
        # Create options for sensor selection
        sensor_options = {
            i: f"{sensor.get('name', DEFAULT_SENSOR_NAME)} (Index: {i})"
            for i, sensor in enumerate(sensors)
        }
        
        data_schema = vol.Schema(
            {
                vol.Optional("remove_sensors"): cv.multi_select(sensor_options),
            }
        )
        
        return self.async_show_form(
            step_id="manage_sensors",
            data_schema=data_schema,
            description_placeholders={"sensor_count": str(len(sensors))},
        )
