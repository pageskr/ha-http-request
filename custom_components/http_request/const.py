"""Constants for the HTTP Request integration."""
from typing import Final

DOMAIN: Final = "http_request"
DOMAIN_DATA: Final = f"{DOMAIN}_data"

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
CONF_SENSOR_NAME: Final = "sensor_name"

# Parsing options
CONF_JSON_PATH: Final = "json_path"
CONF_HTML_SELECTOR: Final = "html_selector"
CONF_HTML_ATTR: Final = "html_attr"
CONF_TEXT_REGEX: Final = "text_regex"
CONF_TEXT_GROUP: Final = "text_group"

# Value template
CONF_VALUE_TEMPLATE: Final = "value_template"

# Defaults
DEFAULT_NAME: Final = "HTTP Request"
DEFAULT_SENSOR_NAME: Final = "Sensor"
DEFAULT_METHOD: Final = "GET"
DEFAULT_TIMEOUT: Final = 30
DEFAULT_VERIFY_SSL: Final = True
DEFAULT_SCAN_INTERVAL: Final = 300
DEFAULT_RESPONSE_TYPE: Final = "text"
DEFAULT_HTML_ATTR: Final = "text"
DEFAULT_TEXT_GROUP: Final = 1

# Response types
RESPONSE_TYPES: Final = ["text", "json", "html"]
HTTP_METHODS: Final = ["GET", "POST", "PUT", "DELETE", "PATCH"]