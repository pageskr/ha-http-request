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
CONF_HTML_VALUE_TYPE: Final = "html_value_type"
CONF_HTML_ATTR_NAME: Final = "html_attr_name"
CONF_TEXT_REGEX: Final = "text_regex"
CONF_TEXT_GROUP: Final = "text_group"
CONF_TEXT_GROUP_COUNT: Final = "text_group_count"

# Value template
CONF_VALUE_TEMPLATE: Final = "value_template"
CONF_KEEP_LAST_VALUE: Final = "keep_last_value"

# Defaults
DEFAULT_NAME: Final = "HTTP Request"
DEFAULT_SENSOR_NAME: Final = "Sensor"
DEFAULT_METHOD: Final = "GET"
DEFAULT_TIMEOUT: Final = 30
DEFAULT_VERIFY_SSL: Final = True
DEFAULT_SCAN_INTERVAL: Final = 300
DEFAULT_RESPONSE_TYPE: Final = "json"
DEFAULT_HTML_ATTR: Final = "text"
DEFAULT_TEXT_GROUP: Final = 1
DEFAULT_TEXT_GROUP_COUNT: Final = 10

# Response types
RESPONSE_TYPES: Final = ["json", "html", "text"]
HTTP_METHODS: Final = ["GET", "POST", "PUT", "DELETE", "PATCH"]
HTML_VALUE_TYPES: Final = ["value", "attribute", "html", "outerhtml"]

# Attributes template
CONF_ATTRIBUTES_TEMPLATE: Final = "attributes_template"

# Reset settings
CONF_RESET_SETTINGS: Final = "reset_settings"