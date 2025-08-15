"""Config flow for HTTP Request integration."""
from __future__ import annotations
import logging
from typing import Any
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import (
    CONF_ATTRIBUTES,
    CONF_BODY,
    CONF_HEADERS,
    CONF_HTML_ATTR,
    CONF_HTML_SELECTOR,
    CONF_JSON_JMES,
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
    DEFAULT_METHOD,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"]
RESP_TYPES = ["json", "html", "text"]


class HttpRequestConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HTTP Request."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                # Basic validation
                if not user_input.get(CONF_NAME):
                    errors["base"] = "invalid_name"
                elif not user_input.get(CONF_URL):
                    errors["base"] = "invalid_url"
                else:
                    # Create entry
                    return self.async_create_entry(
                        title=user_input[CONF_NAME], data=user_input
                    )
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        # Show form
        data_schema = vol.Schema(
            {
                vol.Required(CONF_NAME): str,
                vol.Required(CONF_METHOD, default=DEFAULT_METHOD): vol.In(METHODS),
                vol.Required(CONF_URL): str,
                vol.Optional(CONF_HEADERS, default=""): str,  # JSON string
                vol.Optional(CONF_PARAMS, default=""): str,   # JSON string
                vol.Optional(CONF_BODY, default=""): str,      # JSON string
                vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): vol.Coerce(int),
                vol.Optional(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): bool,
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.Coerce(int),
                vol.Required(CONF_RESPONSE_TYPE, default="json"): vol.In(RESP_TYPES),
                # JSON parser
                vol.Optional(CONF_JSON_JMES, default=""): str,
                # HTML parser
                vol.Optional(CONF_HTML_SELECTOR, default=""): str,
                vol.Optional(CONF_HTML_ATTR, default="text"): str,
                # TEXT parser
                vol.Optional(CONF_TEXT_REGEX, default=""): str,
                vol.Optional(CONF_TEXT_GROUP, default=1): vol.Coerce(int),
                # Template
                vol.Optional(CONF_VALUE_TEMPLATE, default=""): str,
                # Attributes as JSON string for now
                vol.Optional(CONF_ATTRIBUTES, default=""): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )