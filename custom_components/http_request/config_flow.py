"""Config flow for HTTP Request integration."""
from __future__ import annotations

import json
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
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
    DEFAULT_HTML_ATTR,
    DEFAULT_METHOD,
    DEFAULT_NAME,
    DEFAULT_RESPONSE_TYPE,
    DEFAULT_SCAN_INTERVAL,
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
            # Save basic config and move to parsing options
            self.data = user_input
            return await self.async_step_parsing()

        data_schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
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

    async def async_step_parsing(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle parsing configuration based on response type."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate JSON fields
            if self.data[CONF_HEADERS]:
                try:
                    json.loads(self.data[CONF_HEADERS])
                except json.JSONDecodeError:
                    errors["base"] = "invalid_headers_json"
            
            if self.data[CONF_PARAMS]:
                try:
                    json.loads(self.data[CONF_PARAMS])
                except json.JSONDecodeError:
                    errors["base"] = "invalid_params_json"
            
            if self.data[CONF_BODY]:
                try:
                    json.loads(self.data[CONF_BODY])
                except json.JSONDecodeError:
                    errors["base"] = "invalid_body_json"
            
            if not errors:
                # Combine all data
                self.data.update(user_input)
                
                # Create unique ID
                await self.async_set_unique_id(f"{DOMAIN}_{self.data[CONF_NAME]}_{self.data[CONF_URL]}")
                self._abort_if_unique_id_configured()
                
                return self.async_create_entry(
                    title=self.data[CONF_NAME],
                    data=self.data,
                )

        # Build schema based on response type
        response_type = self.data.get(CONF_RESPONSE_TYPE, DEFAULT_RESPONSE_TYPE)
        
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
            step_id="parsing",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={"response_type": response_type},
        )