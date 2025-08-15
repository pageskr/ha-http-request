from __future__ import annotations
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from .const import *

METHODS = ["GET","POST","PUT","PATCH","DELETE"]
RESP_TYPES = ["json","html","text"]

class HttpRequestConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title=user_input.get(CONF_NAME, "HTTP Request"),
                                           data=user_input)

        schema = vol.Schema({
            vol.Required(CONF_NAME): str,
            vol.Required(CONF_METHOD, default="GET"): vol.In(METHODS),
            vol.Required(CONF_URL): str,
            vol.Optional(CONF_HEADERS, default={}): dict,
            vol.Optional(CONF_PARAMS, default={}): dict,
            vol.Optional(CONF_BODY, default={}): dict,
            vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): int,
            vol.Optional(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): bool,
            vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
            vol.Required(CONF_RESPONSE_TYPE, default="json"): vol.In(RESP_TYPES),

            # JSON 파서
            vol.Optional(CONF_JSON_JMES, default=""): str,
            # HTML 파서
            vol.Optional(CONF_HTML_SELECTOR, default=""): str,
            vol.Optional(CONF_HTML_ATTR, default="text"): str,
            # TEXT 파서
            vol.Optional(CONF_TEXT_REGEX, default=""): str,
            vol.Optional(CONF_TEXT_GROUP, default=1): int,

            # Attributes: [{key, response_type, json_jmes/html_selector/html_attr/text_regex/text_group}, ...]
            vol.Optional(CONF_ATTRIBUTES, default=[]): list
        })
        return self.async_show_form(step_id="user", data_schema=schema)

    async def async_step_import(self, user_input) -> FlowResult:
        return await self.async_step_user(user_input)