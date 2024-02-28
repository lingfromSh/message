# Standard Library
import enum

QUEUE_NAME = "message"
SETTINGS_YAML = "/app/message/settings.yaml"


class MessageStatusEnum(enum.Enum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    SENDING = "sending"
    FAILED = "failed"
    SUCCEEDED = "succeeded"
