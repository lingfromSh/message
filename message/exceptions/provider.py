# Local Folder
from .base import DefinedError

__all__ = [
    "ProviderSendNotSupportError",
    "ProviderRecvNotSupportError",
    "ProviderCodeNotFoundError",
]


class ProviderSendNotSupportError(DefinedError):
    message = "provider send not support"


class ProviderRecvNotSupportError(DefinedError):
    message = "provider recv not support"


class ProviderCodeNotFoundError(DefinedError):
    message = "provider code not found"
