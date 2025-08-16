"""Constants for the HTTP Request integration."""
from typing import Final

DOMAIN: Final = "http_request"

# Device info
MANUFACTURER: Final = "Pages in Korea (pages.kr)"
MODEL: Final = "HTTP Request"

# Configuration
CONF_NAME: Final = "name"
CONF_METHOD: Final = "method"
CONF_URL: Final = "url"
CONF_HEADERS: Final = "headers"
CONF_PARAMS: Final = "params"
CONF_BODY: Final = "body"
CONF_TIMEOUT: Final = "timeout"
CONF_VERIFY_SSL: Final = "verify_ssl"
CONF_SCAN_INTERVAL: Final = "scan_interval"
CONF_RESPONSE_TYPE: Final = "response_type"

# Parsing
CONF_JSON_JMES: Final = "json_jmes"
CONF_HTML_SELECTOR: Final = "html_selector"
CONF_HTML_ATTR: Final = "html_attr"
CONF_TEXT_REGEX: Final = "text_regex"
CONF_TEXT_GROUP: Final = "text_group"

# Template
CONF_VALUE_TEMPLATE: Final = "value_template"
CONF_ATTR_TEMPLATE: Final = "attr_template"

# Attributes
CONF_ATTRIBUTES: Final = "attributes"
CONF_KEY: Final = "key"

# Defaults
DEFAULT_NAME: Final = "HTTP Request Sensor"
DEFAULT_METHOD: Final = "GET"
DEFAULT_TIMEOUT: Final = 15
DEFAULT_VERIFY_SSL: Final = True
DEFAULT_SCAN_INTERVAL: Final = 60
DEFAULT_RESPONSE_TYPE: Final = "json"
DEFAULT_HTML_ATTR: Final = "text"
DEFAULT_TEXT_GROUP: Final = 1

# Limits
MIN_SCAN_INTERVAL: Final = 10