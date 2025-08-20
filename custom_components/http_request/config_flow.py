"""Config flow for HTTP Request integration."""
from __future__ import annotations

import json
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME, CONF_UNIT_OF_MEASUREMENT
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv

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
    CONF_TEXT_GROUP,
    CONF_TEXT_GROUP_COUNT,
    CONF_TEXT_REGEX,
    CONF_TIMEOUT,
    CONF_URL,
    CONF_VALUE_TEMPLATE,
    CONF_VERIFY_SSL,
    CONF_SENSOR_NAME,
    CONF_ATTRIBUTES_TEMPLATE,
    CONF_KEEP_LAST_VALUE,
    DEFAULT_HTML_ATTR,
    DEFAULT_METHOD,
    DEFAULT_NAME,
    DEFAULT_RESPONSE_TYPE,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SENSOR_NAME,
    DEFAULT_TEXT_GROUP,
    DEFAULT_TEXT_GROUP_COUNT,
    DEFAULT_TIMEOUT,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
    HTTP_METHODS,
    RESPONSE_TYPES,
    HTML_VALUE_TYPES,
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
            # Save service name and move to HTTP configuration
            self.data["service_name"] = user_input["service_name"]
            return await self.async_step_http_config()

        data_schema = vol.Schema(
            {
                vol.Required("service_name", default=DEFAULT_NAME): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_http_config(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle HTTP configuration step."""
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
                # Combine all data
                self.data.update(user_input)
                
                # Create unique ID for the integration instance
                await self.async_set_unique_id(f"{DOMAIN}_{self.data[CONF_URL]}_{self.data['service_name']}")
                self._abort_if_unique_id_configured()
                
                # Create entry without any sensors initially
                return self.async_create_entry(
                    title=self.data["service_name"],
                    data={
                        **self.data,
                        "sensors": []  # Start with no sensors
                    },
                )

        # Reordered schema with SSL after URL
        data_schema = vol.Schema(
            {
                vol.Required(CONF_URL): str,
                vol.Optional(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): bool,
                vol.Required(CONF_METHOD, default=DEFAULT_METHOD): vol.In(HTTP_METHODS),
                vol.Optional(CONF_HEADERS, default=""): str,
                vol.Optional(CONF_PARAMS, default=""): str,
                vol.Optional(CONF_BODY, default=""): str,
                vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=300)
                ),
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
                    vol.Coerce(int), vol.Range(min=30, max=86400)
                ),
                vol.Required(CONF_RESPONSE_TYPE, default=DEFAULT_RESPONSE_TYPE): vol.In(RESPONSE_TYPES),
            }
        )

        return self.async_show_form(
            step_id="http_config",
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
        self.sensor_to_edit = None
        self.sensor_index_to_edit = None

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["settings", "add_sensor", "edit_sensor", "remove_sensor"],
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
        # Reordered schema
        data_schema = vol.Schema(
            {
                vol.Required("service_name", default=data.get("service_name", DEFAULT_NAME)): str,
                vol.Required(CONF_URL, default=data.get(CONF_URL, "")): str,
                vol.Optional(CONF_VERIFY_SSL, default=data.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL)): bool,
                vol.Required(CONF_METHOD, default=data.get(CONF_METHOD, DEFAULT_METHOD)): vol.In(HTTP_METHODS),
                vol.Optional(CONF_HEADERS, default=data.get(CONF_HEADERS, "")): str,
                vol.Optional(CONF_PARAMS, default=data.get(CONF_PARAMS, "")): str,
                vol.Optional(CONF_BODY, default=data.get(CONF_BODY, "")): str,
                vol.Optional(CONF_TIMEOUT, default=data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=300)
                ),
                vol.Optional(CONF_SCAN_INTERVAL, default=data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)): vol.All(
                    vol.Coerce(int), vol.Range(min=30, max=86400)
                ),
                vol.Required(CONF_RESPONSE_TYPE, default=data.get(CONF_RESPONSE_TYPE, DEFAULT_RESPONSE_TYPE)): vol.In(RESPONSE_TYPES),
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
            # Validate attributes template JSON if provided
            if user_input.get(CONF_ATTRIBUTES_TEMPLATE):
                try:
                    json.loads(user_input[CONF_ATTRIBUTES_TEMPLATE])
                except json.JSONDecodeError:
                    errors["base"] = "invalid_attributes_json"
            
            if not errors:
                # Add new sensor to the sensors list
                new_data = dict(self.config_entry.data)
                sensors = new_data.get("sensors", [])
                
                # Create new sensor config
                new_sensor = {
                    "name": self.temp_sensor_name,
                }
                
                # Process all fields, converting empty strings to None for removal
                for key, value in user_input.items():
                    if value == "" or (isinstance(value, str) and value.strip() == ""):
                        # Don't add empty fields
                        pass
                    else:
                        new_sensor[key] = value
                
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
                    vol.Optional(CONF_ATTRIBUTES_TEMPLATE, default=""): str,
                    vol.Optional(CONF_UNIT_OF_MEASUREMENT, default=""): str,
                    vol.Optional(CONF_KEEP_LAST_VALUE, default=False): bool,
                }
            )
        elif response_type == "html":
            data_schema = vol.Schema(
                {
                    vol.Required(CONF_HTML_SELECTOR): str,
                    vol.Required(CONF_HTML_VALUE_TYPE, default="value"): vol.In(HTML_VALUE_TYPES),
                    vol.Optional(CONF_HTML_ATTR_NAME, default=""): str,
                    vol.Optional(CONF_VALUE_TEMPLATE, default=""): str,
                    vol.Optional(CONF_ATTRIBUTES_TEMPLATE, default=""): str,
                    vol.Optional(CONF_UNIT_OF_MEASUREMENT, default=""): str,
                    vol.Optional(CONF_KEEP_LAST_VALUE, default=False): bool,
                }
            )
        elif response_type == "text":
            data_schema = vol.Schema(
                {
                    vol.Optional(CONF_TEXT_REGEX, default=""): str,
                    vol.Optional(CONF_TEXT_GROUP_COUNT, default=DEFAULT_TEXT_GROUP_COUNT): vol.All(
                        vol.Coerce(int), vol.Range(min=1, max=50)
                    ),
                    vol.Optional(CONF_VALUE_TEMPLATE, default=""): str,
                    vol.Optional(CONF_ATTRIBUTES_TEMPLATE, default=""): str,
                    vol.Optional(CONF_UNIT_OF_MEASUREMENT, default=""): str,
                    vol.Optional(CONF_KEEP_LAST_VALUE, default=False): bool,
                }
            )
        else:
            data_schema = vol.Schema(
                {
                    vol.Optional(CONF_VALUE_TEMPLATE, default=""): str,
                    vol.Optional(CONF_ATTRIBUTES_TEMPLATE, default=""): str,
                    vol.Optional(CONF_UNIT_OF_MEASUREMENT, default=""): str,
                    vol.Optional(CONF_KEEP_LAST_VALUE, default=False): bool,
                }
            )

        return self.async_show_form(
            step_id="sensor_parsing",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={"response_type": response_type},
        )

    async def async_step_edit_sensor(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle editing an existing sensor - select sensor."""
        sensors = self.config_entry.data.get("sensors", [])
        
        if not sensors:
            return self.async_abort(reason="no_sensors")
        
        if user_input is not None:
            # Store selected sensor index
            self.sensor_index_to_edit = int(user_input["sensor_to_edit"])
            self.sensor_to_edit = sensors[self.sensor_index_to_edit]
            return await self.async_step_edit_sensor_details()
        
        # Create options for sensor selection
        sensor_options = {
            str(i): f"{sensor.get('name', DEFAULT_SENSOR_NAME)}"
            for i, sensor in enumerate(sensors)
        }
        
        data_schema = vol.Schema(
            {
                vol.Required("sensor_to_edit"): vol.In(sensor_options),
            }
        )
        
        return self.async_show_form(
            step_id="edit_sensor",
            data_schema=data_schema,
        )

    async def async_step_edit_sensor_details(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle editing sensor details."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate attributes template JSON if provided
            if user_input.get(CONF_ATTRIBUTES_TEMPLATE):
                try:
                    json.loads(user_input[CONF_ATTRIBUTES_TEMPLATE])
                except json.JSONDecodeError:
                    errors["base"] = "invalid_attributes_json"
            
            if not errors:
                # Update sensor configuration
                new_data = dict(self.config_entry.data)
                sensors = new_data.get("sensors", [])
                
                # Update the sensor with new values
                updated_sensor = {
                    "name": user_input.get(CONF_SENSOR_NAME, self.sensor_to_edit["name"]),
                }
                
                # Process all fields, converting empty strings to None for removal
                for key, value in user_input.items():
                    if key != CONF_SENSOR_NAME:
                        if value == "" or (isinstance(value, str) and value.strip() == ""):
                            # Don't add empty fields - check if field exists in old sensor
                            if key in self.sensor_to_edit:
                                # Field existed before but now empty, so don't include it
                                pass
                        else:
                            updated_sensor[key] = value
                
                sensors[self.sensor_index_to_edit] = updated_sensor
                new_data["sensors"] = sensors
                
                # Update config entry
                self.hass.config_entries.async_update_entry(
                    self.config_entry, data=new_data
                )
                
                # Reload the integration
                await self.hass.config_entries.async_reload(self.config_entry.entry_id)
                
                return self.async_create_entry(title="", data={})

        # Build schema based on response type with current values
        response_type = self.config_entry.data.get(CONF_RESPONSE_TYPE, DEFAULT_RESPONSE_TYPE)
        sensor_name = self.sensor_to_edit.get("name", DEFAULT_SENSOR_NAME)
        
        # Base schema with sensor name
        schema_dict = {
            vol.Required(CONF_SENSOR_NAME, default=sensor_name): str,
        }
        
        if response_type == "json":
            schema_dict.update({
                vol.Optional(CONF_JSON_PATH, default=self.sensor_to_edit.get(CONF_JSON_PATH, "")): str,
                vol.Optional(CONF_VALUE_TEMPLATE, default=self.sensor_to_edit.get(CONF_VALUE_TEMPLATE, "")): str,
                vol.Optional(CONF_ATTRIBUTES_TEMPLATE, default=self.sensor_to_edit.get(CONF_ATTRIBUTES_TEMPLATE, "")): str,
                vol.Optional(CONF_UNIT_OF_MEASUREMENT, default=self.sensor_to_edit.get(CONF_UNIT_OF_MEASUREMENT, "")): str,
                vol.Optional(CONF_KEEP_LAST_VALUE, default=self.sensor_to_edit.get(CONF_KEEP_LAST_VALUE, False)): bool,
            })
        elif response_type == "html":
            schema_dict.update({
                vol.Required(CONF_HTML_SELECTOR, default=self.sensor_to_edit.get(CONF_HTML_SELECTOR, "")): str,
                vol.Required(CONF_HTML_VALUE_TYPE, default=self.sensor_to_edit.get(CONF_HTML_VALUE_TYPE, "value")): vol.In(HTML_VALUE_TYPES),
                vol.Optional(CONF_HTML_ATTR_NAME, default=self.sensor_to_edit.get(CONF_HTML_ATTR_NAME, "")): str,
                vol.Optional(CONF_VALUE_TEMPLATE, default=self.sensor_to_edit.get(CONF_VALUE_TEMPLATE, "")): str,
                vol.Optional(CONF_ATTRIBUTES_TEMPLATE, default=self.sensor_to_edit.get(CONF_ATTRIBUTES_TEMPLATE, "")): str,
                vol.Optional(CONF_UNIT_OF_MEASUREMENT, default=self.sensor_to_edit.get(CONF_UNIT_OF_MEASUREMENT, "")): str,
                vol.Optional(CONF_KEEP_LAST_VALUE, default=self.sensor_to_edit.get(CONF_KEEP_LAST_VALUE, False)): bool,
            })
        elif response_type == "text":
            schema_dict.update({
                vol.Optional(CONF_TEXT_REGEX, default=self.sensor_to_edit.get(CONF_TEXT_REGEX, "")): str,
                vol.Optional(CONF_TEXT_GROUP_COUNT, default=self.sensor_to_edit.get(CONF_TEXT_GROUP_COUNT, DEFAULT_TEXT_GROUP_COUNT)): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=50)
                ),
                vol.Optional(CONF_VALUE_TEMPLATE, default=self.sensor_to_edit.get(CONF_VALUE_TEMPLATE, "")): str,
                vol.Optional(CONF_ATTRIBUTES_TEMPLATE, default=self.sensor_to_edit.get(CONF_ATTRIBUTES_TEMPLATE, "")): str,
                vol.Optional(CONF_UNIT_OF_MEASUREMENT, default=self.sensor_to_edit.get(CONF_UNIT_OF_MEASUREMENT, "")): str,
                vol.Optional(CONF_KEEP_LAST_VALUE, default=self.sensor_to_edit.get(CONF_KEEP_LAST_VALUE, False)): bool,
            })
        else:
            schema_dict.update({
                vol.Optional(CONF_VALUE_TEMPLATE, default=self.sensor_to_edit.get(CONF_VALUE_TEMPLATE, "")): str,
                vol.Optional(CONF_ATTRIBUTES_TEMPLATE, default=self.sensor_to_edit.get(CONF_ATTRIBUTES_TEMPLATE, "")): str,
                vol.Optional(CONF_UNIT_OF_MEASUREMENT, default=self.sensor_to_edit.get(CONF_UNIT_OF_MEASUREMENT, "")): str,
                vol.Optional(CONF_KEEP_LAST_VALUE, default=self.sensor_to_edit.get(CONF_KEEP_LAST_VALUE, False)): bool,
            })
        
        data_schema = vol.Schema(schema_dict)

        return self.async_show_form(
            step_id="edit_sensor_details",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "response_type": response_type,
                "sensor_name": sensor_name,
            },
        )

    async def async_step_remove_sensor(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle removing sensors."""
        sensors = self.config_entry.data.get("sensors", [])
        
        if not sensors:
            return self.async_abort(reason="no_sensors")
        
        if user_input is not None:
            # Handle sensor removal
            if "sensors_to_remove" in user_input and user_input["sensors_to_remove"]:
                # Convert string indices to integers and remove sensors
                indices_to_remove = [int(idx) for idx in user_input["sensors_to_remove"]]
                new_sensors = [s for i, s in enumerate(sensors) if i not in indices_to_remove]
                
                new_data = dict(self.config_entry.data)
                new_data["sensors"] = new_sensors
                
                self.hass.config_entries.async_update_entry(
                    self.config_entry, data=new_data
                )
                
                await self.hass.config_entries.async_reload(self.config_entry.entry_id)
                
                return self.async_create_entry(title="", data={})
        
        # Create options for sensor selection
        sensor_options = {
            str(i): f"{sensor.get('name', DEFAULT_SENSOR_NAME)}"
            for i, sensor in enumerate(sensors)
        }
        
        data_schema = vol.Schema(
            {
                vol.Optional("sensors_to_remove"): cv.multi_select(sensor_options),
            }
        )
        
        return self.async_show_form(
            step_id="remove_sensor",
            data_schema=data_schema,
            description_placeholders={"sensor_count": str(len(sensors))},
        )
