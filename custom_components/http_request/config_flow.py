"""Config flow for HTTP Request integration."""
from __future__ import annotations

import json
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

DOMAIN = "http_request"

# Basic configuration schema
DATA_SCHEMA = vol.Schema({
    vol.Required("name"): str,
    vol.Required("url"): str,
    vol.Optional("method", default="GET"): vol.In(["GET", "POST", "PUT", "PATCH", "DELETE"]),
    vol.Optional("headers", default=""): str,
    vol.Optional("timeout", default=30): vol.All(vol.Coerce(int), vol.Range(min=1, max=300)),
    vol.Optional("scan_interval", default=60): vol.All(vol.Coerce(int), vol.Range(min=10, max=86400)),
})


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HTTP Request."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Validate the data
            if not user_input.get("name"):
                errors["name"] = "invalid_name"
            elif not user_input.get("url"):
                errors["url"] = "invalid_url"
            else:
                # Validate JSON in headers field
                headers_str = user_input.get("headers", "")
                if headers_str:
                    try:
                        json.loads(headers_str)
                    except json.JSONDecodeError:
                        errors["headers"] = "invalid_json"
                
                if not errors:
                    # Create the entry
                    return self.async_create_entry(
                        title=user_input["name"],
                        data=user_input
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )