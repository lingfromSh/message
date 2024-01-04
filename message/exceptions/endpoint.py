# Local Folder
from .base import DefinedError

__all__ = [
    "EndpointNotFoundError",
    "EndpointContactIsNotValidError",
]


class EndpointNotFoundError(DefinedError):
    message = "Endpoint not found"


class EndpointContactIsNotValidError(DefinedError):
    message = "Contact value is not valid"
