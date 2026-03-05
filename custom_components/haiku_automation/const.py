"""Constants for HAIKU Automation Builder."""

DOMAIN = "haiku_automation"
DEFAULT_NAME = "HAIKU Automation"

# Service names
SERVICE_CREATE_AUTOMATION = "create_automation"
SERVICE_PROCESS_TELEGRAM = "process_telegram"

# Events
EVENT_AUTOMATION_CREATED = f"{DOMAIN}_automation_created"
EVENT_TELEGRAM_PROCESSED = f"{DOMAIN}_telegram_processed"