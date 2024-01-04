# Third Party Library
from fastapi import status
from message.exceptions.base import DefinedError

__all__ = [
    "UserNotFoundError",
    "UserDuplicatedExternalIDError",
    "UserMetadataWithWrongTypeError",
    "UserGotInvalidEndpointError",
]


class UserNotFoundError(DefinedError):
    code = status.HTTP_404_NOT_FOUND
    status_code = status.HTTP_404_NOT_FOUND
    message = "User not found"


class UserDuplicatedExternalIDError(DefinedError):
    message = "User has a duplicated external ID"


class UserMetadataWithWrongTypeError(DefinedError):
    message = "Metadata must be a map"


class UserGotInvalidEndpointError(DefinedError):
    message = "User can not bind invalid endpoint"
