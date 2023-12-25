# Standard Library
import enum
import os

SETTINGS_YAML = os.environ.get("MESSAGE_SETTINGS", "settings.yaml")


class ContactEnum(enum.Enum):
    EMAIL = "email"
    MOBILE = "mobile"
    WEBSOCKET = "websocket"


class MessageStatusEnum(enum.Enum):
    SCHEDULED = "scheduled"
    SENDING = "sending"
    FAILED = "failed"
    SUCCEEDED = "succeeded"
