"""Parser utilities for HTTP Request integration."""
from __future__ import annotations

import logging
import re
from typing import Any

import jmespath
from bs4 import BeautifulSoup

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import TemplateError
from homeassistant.helpers import template

_LOGGER = logging.getLogger(__name__)


def parse_json(data: Any, jmes_path: str | None) -> Any:
    """Parse JSON data with JMESPath."""
    if not jmes_path:
        return data
    
    try:
        result = jmespath.search(jmes_path, data)
        return result
    except Exception as err:
        _LOGGER.error("JMESPath error '%s': %s", jmes_path, err)
        return None


def parse_html(text: str, selector: str, attr: str | None = None) -> Any:
    """Parse HTML with CSS selector."""
    if not selector:
        return text
    
    try:
        soup = BeautifulSoup(text, "lxml")
        element = soup.select_one(selector)
        
        if element is None:
            _LOGGER.debug("No element found for selector: %s", selector)
            return None
        
        if attr is None or attr == "text":
            return element.get_text(strip=True)
        
        return element.get(attr)
    except Exception as err:
        _LOGGER.error("HTML parsing error for selector '%s': %s", selector, err)
        return None


def parse_text(text: str, regex: str, group: int = 1) -> Any:
    """Parse text with regex."""
    if not regex:
        return text
    
    try:
        match = re.search(regex, text, re.MULTILINE | re.DOTALL)
        if match:
            try:
                return match.group(group)
            except IndexError:
                _LOGGER.error("Regex group %d not found", group)
                return None
        return None
    except Exception as err:
        _LOGGER.error("Regex error '%s': %s", regex, err)
        return None


def extract_value(
    response_type: str,
    data: Any,
    text: str,
    config: dict[str, Any],
) -> Any:
    """Extract value based on response type."""
    if response_type == "json":
        return parse_json(data, config.get("json_jmes"))
    elif response_type == "html":
        return parse_html(
            text,
            config.get("html_selector", ""),
            config.get("html_attr", "text"),
        )
    elif response_type == "text":
        return parse_text(
            text,
            config.get("text_regex", ""),
            config.get("text_group", 1),
        )
    return None


async def render_template_value(
    hass: HomeAssistant,
    template_str: str,
    variables: dict[str, Any],
) -> Any:
    """Render a template with variables."""
    if not template_str:
        return variables.get("value")
    
    try:
        tpl = template.Template(template_str, hass)
        result = await tpl.async_render(variables)
        return result
    except TemplateError as err:
        _LOGGER.error("Template error: %s", err)
        return None
    except Exception as err:
        _LOGGER.error("Unexpected template error: %s", err)
        return None