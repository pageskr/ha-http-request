DOMAIN = "http_request"

# Common
CONF_NAME = "name"
CONF_METHOD = "method"
CONF_URL = "url"
CONF_HEADERS = "headers"
CONF_PARAMS = "params"
CONF_BODY = "body"
CONF_TIMEOUT = "timeout"
CONF_VERIFY_SSL = "verify_ssl"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_RESPONSE_TYPE = "response_type"  # json | html | text

# Parsing (state)
CONF_JSON_JMES = "json_jmes"          # JMESPath
CONF_HTML_SELECTOR = "html_selector"  # e.g. div.price span.value
CONF_HTML_ATTR = "html_attr"          # text | attribute name (e.g. "href")
CONF_TEXT_REGEX = "text_regex"        # e.g. "price:\\s*(\\d+)"
CONF_TEXT_GROUP = "text_group"        # int (capture group index)

# Attributes
CONF_ATTRIBUTES = "attributes"        # list[dict] of same parsing schema with "key"
CONF_KEY = "key"

# Defaults
DEFAULT_TIMEOUT = 15
DEFAULT_VERIFY_SSL = True
MIN_SCAN_INTERVAL = 10
DEFAULT_SCAN_INTERVAL = 60