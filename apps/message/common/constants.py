import enum


class MessageProviderType(enum.Enum):
    """
    Providers types
    """

    WEBSOCKET = "websocket"
    EMAIL = "email"
    VOICE_MESSAGE = "voice_message"
    SMS = "sms"
