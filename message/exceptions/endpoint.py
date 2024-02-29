# Local Folder
from .base import DefinedError

__all__ = [
    "EndpointNotFoundError",
    "EndpointInvalidValueError",
]


class EndpointNotFoundError(DefinedError):
    message = "Endpoint not found"


class EndpointInvalidValueError(DefinedError):
    message = "Invalid value within contact schema"


class EndpointContactRequiredError(DefinedError):
    message = "An existed contact is required"
