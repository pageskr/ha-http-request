from __future__ import annotations
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Dict, Optional
import asyncio
from aiohttp import ClientSession, ClientTimeout
from yarl import URL

from homeassistant.core import HomeAssistant
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import *
from .parser import extract_value

@dataclass
class RequestConfig:
    name: str
    method: str
    url: str
    headers: Dict[str, Any]
    params: Dict[str, Any]
    body: Dict[str, Any]
    timeout: int
    verify_ssl: bool
    scan_interval: int
    response_type: str
    json_jmes: Optional[str]
    html_selector: Optional[str]
    html_attr: Optional[str]
    text_regex: Optional[str]
    text_group: Optional[int]
    attributes: list

class HttpCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, cfg: RequestConfig):
        self.hass = hass
        self.cfg = cfg
        interval = max(MIN_SCAN_INTERVAL, int(cfg.scan_interval))
        super().__init__(hass, logger=None, name=DOMAIN, update_interval=timedelta(seconds=interval))

    async def _async_update_data(self) -> dict:
        timeout = ClientTimeout(total=self.cfg.timeout)
        async with ClientSession(timeout=timeout) as session:
            try:
                url = URL(self.cfg.url)
                async with session.request(
                    self.cfg.method, url, headers=self.cfg.headers or {},
                    params=self.cfg.params or {}, json=self.cfg.body or None,
                    ssl=self.cfg.verify_ssl
                ) as resp:
                    text = await resp.text()
                    try:
                        body_obj = await resp.json(content_type=None)
                    except Exception:
                        body_obj = None

                    # state
                    state_val = extract_value(
                        self.cfg.response_type, body_obj, text,
                        self.cfg.json_jmes, self.cfg.html_selector,
                        self.cfg.html_attr, self.cfg.text_regex, self.cfg.text_group
                    )

                    # attributes
                    attrs: Dict[str, Any] = {"http_status": resp.status}
                    for item in (self.cfg.attributes or []):
                        key = item.get(CONF_KEY)
                        rtype = item.get(CONF_RESPONSE_TYPE, self.cfg.response_type)
                        val = extract_value(
                            rtype,
                            body_obj, text,
                            item.get(CONF_JSON_JMES),
                            item.get(CONF_HTML_SELECTOR),
                            item.get(CONF_HTML_ATTR),
                            item.get(CONF_TEXT_REGEX),
                            item.get(CONF_TEXT_GROUP),
                        )
                        if key:
                            attrs[key] = val

                    return {
                        "state": state_val,
                        "attrs": attrs,
                        "raw_text": text,
                        "raw_json": body_obj
                    }
            except Exception as e:
                raise UpdateFailed(str(e)) from e

class HttpRequestSensor(SensorEntity):
    _attr_icon = "mdi:http"

    def __init__(self, coordinator: HttpCoordinator, entry: ConfigEntry, cfg: RequestConfig):
        super().__init__()
        self.coordinator = coordinator
        self._entry = entry
        self._cfg = cfg
        self._attr_name = cfg.name
        self._attr_unique_id = f"{entry.entry_id}"

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def native_value(self) -> Any:
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("state")

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        if not self.coordinator.data:
            return {}
        return self.coordinator.data.get("attrs", {})

    async def async_update(self):
        await self.coordinator.async_request_refresh()

    async def async_added_to_hass(self):
        self.async_on_remove(self.coordinator.async_add_listener(self.async_write_ha_state))

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    d = entry.data
    cfg = RequestConfig(
        name=d.get(CONF_NAME),
        method=d.get(CONF_METHOD, "GET").upper(),
        url=d.get(CONF_URL),
        headers=d.get(CONF_HEADERS, {}),
        params=d.get(CONF_PARAMS, {}),
        body=d.get(CONF_BODY, {}),
        timeout=int(d.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)),
        verify_ssl=bool(d.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL)),
        scan_interval=int(d.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)),
        response_type=d.get(CONF_RESPONSE_TYPE, "json"),
        json_jmes=d.get(CONF_JSON_JMES) or "",
        html_selector=d.get(CONF_HTML_SELECTOR) or "",
        html_attr=d.get(CONF_HTML_ATTR) or "text",
        text_regex=d.get(CONF_TEXT_REGEX) or "",
        text_group=int(d.get(CONF_TEXT_GROUP, 1)),
        attributes=d.get(CONF_ATTRIBUTES, []),
    )

    coord = HttpCoordinator(hass, cfg)
    await coord.async_config_entry_first_refresh()
    async_add_entities([HttpRequestSensor(coord, entry, cfg)])