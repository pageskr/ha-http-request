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
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_ATTRIBUTES,
    CONF_BODY,
    CONF_HEADERS,
    CONF_HTML_ATTR,
    CONF_HTML_SELECTOR,
    CONF_JSON_JMES,
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
    MIN_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


def validate_json_string(value: str) -> str:
    """Validate JSON string and return it."""
    if not value:
        return ""
    try:
        json.loads(value)
        return value
    except json.JSONDecodeError:
        raise vol.Invalid("Invalid JSON format")


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HTTP Request."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                # Validate inputs
                if not user_input.get(CONF_NAME):
                    errors["base"] = "invalid_name"
                elif not user_input.get(CONF_URL):
                    errors["base"] = "invalid_url"
                else:
                    # Parse JSON strings
                    headers = user_input.get(CONF_HEADERS, "")
                    params = user_input.get(CONF_PARAMS, "")
                    body = user_input.get(CONF_BODY, "")
                    attributes = user_input.get(CONF_ATTRIBUTES, "")
                    
                    # Validate JSON format
                    try:
                        if headers:
                            json.loads(headers)
                        if params:
                            json.loads(params)
                        if body:
                            json.loads(body)
                        if attributes:
                            json.loads(attributes)
                    except json.JSONDecodeError:
                        errors["base"] = "invalid_json"
                    
                    if not errors:
                        # Create unique ID
                        await self.async_set_unique_id(f"{DOMAIN}_{user_input[CONF_NAME]}")
                        self._abort_if_unique_id_configured()
                        
                        return self.async_create_entry(
                            title=user_input[CONF_NAME],
                            data=user_input,
                        )
                        
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        # Show form
        data_schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
                vol.Required(CONF_METHOD, default=DEFAULT_METHOD): vol.In(
                    ["GET", "POST", "PUT", "PATCH", "DELETE"]
                ),
                vol.Required(CONF_URL): str,
                vol.Optional(CONF_HEADERS, default=""): str,
                vol.Optional(CONF_PARAMS, default=""): str,
                vol.Optional(CONF_BODY, default=""): str,
                vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=300)
                ),
                vol.Optional(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): bool,
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): vol.All(
                    vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL, max=86400)
                ),
                vol.Required(CONF_RESPONSE_TYPE, default=DEFAULT_RESPONSE_TYPE): vol.In(
                    ["json", "html", "text"]
                ),
            }
        )

        # Add parsing fields based on form state
        if self.show_advanced_options:
            data_schema = data_schema.extend(
                {
                    vol.Optional(CONF_JSON_JMES, default=""): str,
                    vol.Optional(CONF_HTML_SELECTOR, default=""): str,
                    vol.Optional(CONF_HTML_ATTR, default=DEFAULT_HTML_ATTR): str,
                    vol.Optional(CONF_TEXT_REGEX, default=""): str,
                    vol.Optional(CONF_TEXT_GROUP, default=DEFAULT_TEXT_GROUP): vol.All(
                        vol.Coerce(int), vol.Range(min=0, max=99)
                    ),
                    vol.Optional(CONF_VALUE_TEMPLATE, default=""): str,
                    vol.Optional(CONF_ATTRIBUTES, default=""): str,
                }
            )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )