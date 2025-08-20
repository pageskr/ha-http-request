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


def parse_html(html_content: str, selector: str, value_type: str = "value", attr_name: str | None = None) -> Any:
    """Parse HTML with CSS selector and value type."""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        element = soup.select_one(selector)
        
        if element is None:
            _LOGGER.debug("No element found for selector: %s", selector)
            return None
        
        if value_type == "value":
            # Return text content without HTML tags
            return element.get_text(strip=True)
        elif value_type == "attribute":
            # Return specific attribute value
            if attr_name:
                return element.get(attr_name)
            else:
                _LOGGER.error("Attribute name not specified for attribute type")
                return None
        elif value_type == "html":
            # Return inner HTML
            return ''.join(str(child) for child in element.children)
        else:
            # Default to text
            return element.get_text(strip=True)
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


def parse_text_all(text: str, regex: str, max_groups: int | None = None) -> list[str] | None:
    """Parse text and return all regex matches, optionally limited to max_groups."""
    if not regex:
        return None
        
    try:
        matches = re.findall(regex, text, re.MULTILINE | re.DOTALL)
        # Limit to max_groups only if specified
        if matches and max_groups is not None and len(matches) > max_groups:
            matches = matches[:max_groups]
        return matches if matches else None
    except Exception as err:
        _LOGGER.error("Regex error: %s", err)
        return None


async def render_template(
    hass: HomeAssistant,
    template_str: str,
    variables: dict[str, Any],
) -> Any:
    """Render a template with the given variables."""
    if not template_str:
        return variables.get("value")
        
    try:
        template = template_helper.Template(template_str, hass)
        result = template.async_render(variables)
        return result
    except TemplateError as err:
        _LOGGER.error("Template error: %s", err)
        return variables.get("value")
    except Exception as err:
        _LOGGER.error("Unexpected template error: %s", err)
        return variables.get("value")


async def render_attributes_template(
    hass: HomeAssistant,
    template_str: str,
    variables: dict[str, Any],
) -> dict[str, Any]:
    """Render attributes template and return dictionary."""
    if not template_str:
        return {}
        
    try:
        # First, parse the JSON structure
        attributes_config = json.loads(template_str)
        
        # Then render each value as a template
        rendered_attributes = {}
        for key, value_template in attributes_config.items():
            if isinstance(value_template, str):
                template = template_helper.Template(value_template, hass)
                rendered_attributes[key] = template.async_render(variables)
            else:
                # If not a string, use as-is
                rendered_attributes[key] = value_template
        
        return rendered_attributes
    except json.JSONDecodeError as err:
        _LOGGER.error("Invalid JSON in attributes template: %s", err)
        return {}
    except TemplateError as err:
        _LOGGER.error("Template error in attributes: %s", err)
        return {}
    except Exception as err:
        _LOGGER.error("Unexpected error in attributes template: %s", err)
        return {}
