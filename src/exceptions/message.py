# Local Folder
from .base import DefinedError

__all__ = [
    "MessageNotFoundError",
    "MessageSendRequiredReceiversError",
]


class MessageNotFoundError(DefinedError):
    message = "message not found"


class MessageSendRequiredReceiversError(DefinedError):
    message = "message send requires receivers"
