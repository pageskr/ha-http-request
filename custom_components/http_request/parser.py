"""Parser utilities for HTTP Request integration."""
from __future__ import annotations

import json
import logging
import re
from typing import Any

from bs4 import BeautifulSoup

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import TemplateError
from homeassistant.helpers import template as template_helper

_LOGGER = logging.getLogger(__name__)


def parse_json(data: str | dict, path: str | None = None) -> Any:
    """Parse JSON data with optional path."""
    try:
        if isinstance(data, str):
            json_data = json.loads(data)
        else:
            json_data = data
            
        if not path:
            return json_data
            
        # Enhanced JSON path support
        # Support for:
        # - Simple path: "data.temperature"
        # - Array index: "items[0].value"
        # - Multiple indices: "data.items[0].values[1]"
        # - Bracket notation: "data['temperature']"
        
        result = json_data
        
        # Replace bracket notation with dot notation
        path = path.replace("']['", ".").replace("['", ".").replace("']", "").replace("[\"", ".").replace("\"]", "")
        
        # Split by dots, but handle array indices
        parts = []
        current = ""
        for char in path:
            if char == ".":
                if current:
                    parts.append(current)
                    current = ""
            elif char == "[":
                if current:
                    parts.append(current)
                    current = "["
            else:
                current += char
        if current:
            parts.append(current)
        
        for part in parts:
            if not part:
                continue
                
            if part.startswith("[") and part.endswith("]"):
                # Array index
                index = int(part[1:-1])
                result = result[index]
            elif "[" in part and "]" in part:
                # Handle array index in format like "items[0]"
                key, index_str = part.split("[")
                index = int(index_str.rstrip("]"))
                if key:
                    result = result[key]
                result = result[index]
            else:
                # Regular key
                result = result[part]
        
        return result
    except (KeyError, IndexError, TypeError) as err:
        _LOGGER.debug("JSON path error for path '%s': %s", path, err)
        return None
    except Exception as err:
        _LOGGER.error("JSON parsing error: %s", err)
        return None


def parse_html(html_content: str, selector: str, attr: str | None = None) -> Any:
    """Parse HTML with CSS selector."""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        element = soup.select_one(selector)
        
        if element is None:
            _LOGGER.debug("No element found for selector: %s", selector)
            return None
        
        if attr is None or attr == "text":
            return element.get_text(strip=True)
        
        return element.get(attr)
    except Exception as err:
        _LOGGER.error("HTML parsing error: %s", err)
        return None


def parse_html_full(html_content: str, selector: str) -> str | None:
    """Parse HTML and return the outer HTML of selected element."""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        element = soup.select_one(selector)
        
        if element is None:
            _LOGGER.debug("No element found for selector: %s", selector)
            return None
        
        # Return the outer HTML
        return str(element)
    except Exception as err:
        _LOGGER.error("HTML parsing error: %s", err)
        return None


def parse_text(text: str, regex: str | None = None, group: int = 1) -> Any:
    """Parse text with optional regex."""
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
        _LOGGER.error("Regex error: %s", err)
        return None


async def render_template(
    hass: HomeAssistant,
    template_str: str,
    value: Any,
    response_data: dict[str, Any],
) -> Any:
    """Render a template with the given value and context."""
    if not template_str:
        return value
        
    try:
        template = template_helper.Template(template_str, hass)
        variables = {
            "value": value,
            "response": response_data.get("text", ""),
            "json": response_data.get("json"),
            "status": response_data.get("status"),
        }
        
        result = template.async_render(variables)
        return result
    except TemplateError as err:
        _LOGGER.error("Template error: %s", err)
        return value
    except Exception as err:
        _LOGGER.error("Unexpected template error: %s", err)
        return value
