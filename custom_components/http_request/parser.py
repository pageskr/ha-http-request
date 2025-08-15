"""Parser functions for HTTP Request integration."""
from __future__ import annotations
from typing import Any, Optional
import re
import logging
import jmespath
from bs4 import BeautifulSoup
from homeassistant.helpers.template import Template
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


def parse_json(body: Any, jmes: Optional[str]) -> Any:
    """Parse JSON response with JMESPath."""
    if not jmes:
        return body
    try:
        return jmespath.search(jmes, body)
    except Exception as e:
        _LOGGER.error("JMESPath error: %s", e)
        return None


def parse_html(text: str, selector: str, attr: Optional[str]) -> Any:
    """Parse HTML response with CSS selector."""
    if not selector:
        return text
    try:
        soup = BeautifulSoup(text, "lxml")
        el = soup.select_one(selector)
        if el is None:
            return None
        if attr is None or attr == "text":
            return el.get_text(strip=True)
        return el.get(attr)
    except Exception as e:
        _LOGGER.error("HTML parse error: %s", e)
        return None


def parse_text(text: str, pattern: str, group: int = 1) -> Any:
    """Parse text response with regex."""
    if not pattern:
        return text
    try:
        m = re.search(pattern, text, re.MULTILINE | re.DOTALL)
        if not m:
            return None
        return m.group(group)
    except Exception as e:
        _LOGGER.error("Regex error: %s", e)
        return None


def extract_value(
    response_type: str,
    body_obj: Any,
    body_text: str,
    json_jmes: str | None,
    html_selector: str | None,
    html_attr: str | None,
    text_regex: str | None,
    text_group: int | None,
) -> Any:
    """Extract value based on response type and parsing config."""
    if response_type == "json":
        return parse_json(body_obj, json_jmes)
    elif response_type == "html":
        return parse_html(body_text, html_selector or "", html_attr)
    elif response_type == "text":
        return parse_text(body_text, text_regex or "", int(text_group or 1))
    return None


async def render_template(
    hass: HomeAssistant, template_str: str, variables: dict[str, Any]
) -> Any:
    """Render Jinja2 template with variables."""
    if not template_str:
        return None
    
    try:
        template = Template(template_str, hass)
        return template.async_render(variables)
    except Exception as e:
        _LOGGER.error("Template render error: %s", e)
        return None