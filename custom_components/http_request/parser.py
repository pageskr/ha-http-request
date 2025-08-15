from __future__ import annotations
from typing import Any, Optional
import re
import jmespath
from bs4 import BeautifulSoup

def parse_json(body: Any, jmes: Optional[str]) -> Any:
    if jmes:
        try:
            return jmespath.search(jmes, body)
        except Exception as e:
            return f"JMESPath error: {e}"
    return body

def parse_html(text: str, selector: str, attr: Optional[str]) -> Any:
    try:
        soup = BeautifulSoup(text, "html.parser")
        el = soup.select_one(selector)
        if el is None:
            return None
        if attr is None or attr == "text":
            return el.get_text(strip=True)
        return el.get(attr)
    except Exception as e:
        return f"HTML parse error: {e}"

def parse_text(text: str, pattern: str, group: int = 1) -> Any:
    try:
        m = re.search(pattern, text, re.MULTILINE | re.DOTALL)
        if not m:
            return None
        return m.group(group)
    except Exception as e:
        return f"Regex error: {e}"

def extract_value(response_type: str, body_obj: Any, body_text: str,
                  json_jmes: str | None, html_selector: str | None,
                  html_attr: str | None, text_regex: str | None, text_group: int | None):
    if response_type == "json":
        return parse_json(body_obj, json_jmes or "")
    elif response_type == "html":
        return parse_html(body_text, html_selector or "", html_attr)
    elif response_type == "text":
        return parse_text(body_text, text_regex or "", int(text_group or 1))
    return None