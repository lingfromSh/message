import enum


class MessageProviderType(str, enum.Enum):
    """
    Providers types
    """

    WEBSOCKET = "websocket"
    EMAIL = "email"
    VOICE_MESSAGE = "voice_message"
    SMS = "sms"


class MessageStatus(str, enum.Enum):
    """
    Message status
    """

    SENDING = "sending"
    FAILED = "failed"
    SUCCEEDED = "succeeded"
