# Standard Library
import enum
import os

QUEUE_NAME = "message"
SETTINGS_YAML = os.environ.get("MESSAGE_SETTINGS", "message/settings.yaml")


class ContactEnum(enum.Enum):
    EMAIL = "email"
    MOBILE = "mobile"
    WEBSOCKET = "websocket"
    FEISHU = "feishu"


class MessageStatusEnum(enum.Enum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    SENDING = "sending"
    FAILED = "failed"
    SUCCEEDED = "succeeded"


class SIGNALS:
    MESSAGE_CREATE = "message.create"
